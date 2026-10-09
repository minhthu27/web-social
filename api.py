
from flask import Flask, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from pymongo import MongoClient
from config.db import db, serialize_objectid
from backend.profile import profile_bp
from config.config import Config
from bson.objectid import ObjectId
from datetime import datetime
import logging
from pymongo.errors import ConnectionFailure

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.register_blueprint(profile_bp, url_prefix='/profile')
# Connect to MongoDB
try:
    client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client["connectify_db"]
    logger.info("MongoDB connection successful!")
except ConnectionFailure as e:
    logger.error(f"MongoDB connection failed: {str(e)}")
    raise

# Helper function to serialize ObjectId and datetime for JSON
def serialize_doc(doc):
    if isinstance(doc, dict):
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, datetime):
                doc[key] = value.isoformat()
            elif isinstance(value, dict):
                doc[key] = serialize_doc(value)
            elif isinstance(value, list):
                doc[key] = [serialize_doc(item) if isinstance(item, dict) else str(item) if isinstance(item, ObjectId) else item for item in value]
    return doc

@app.route('/profile/<user_id>', methods=['GET'])
def get_user_profile(user_id):
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(user_id):
            return jsonify({"success": False, "message": "Invalid user ID"}), 400
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        profile_data = {
            "id": str(user["_id"]),
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "fullname": user.get("fullname", ""),
            "avatar": user.get("avatar", "/static/uploads/default-avatar.jpg"),
            "followers_count": user.get("followers_count", 0),
            "posts_count": user.get("posts_count", 0),
            "isFollowing": False
            # Add other profile fields as needed
        }
        return jsonify({"success": True, "data": profile_data}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/notifications/<user_id>', methods=['GET'])
def get_notifications(user_id):
    try:
        logger.debug(f"Fetching notification: {user_id}")
        notifications_id = db.notifications.find_one({"_id": ObjectId(user_id)})
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))
        unread_only = request.args.get('unread', 'false').lower() == 'true'
        notification_type = request.args.get('type', None)
        query = {"recipient_id": ObjectId(notifications_id)}
        if unread_only:
            query["read"] = False
        if notification_type:  # Thêm điều kiện lọc theo type
            query["type"] = notification_type
        notifications = list(db.notifications.find(query)
                             .sort("created_at", -1)
                             .skip(skip)
                             .limit(limit))

        unread_count = db.notifications.count_documents({
            "recipient_id": ObjectId(notifications_id),
            "read": False})
        likes_count = db.notifications.count_documents({
            "recipient_id": ObjectId(notifications_id),
            "read": False,
            "type": "like"
        })
        follows_count = db.notifications.count_documents({
            "recipient_id": ObjectId(notifications_id),
            "read": False,
            "type": "follow"
        })
        # mentions_count = db.notifications.count_documents({
        #         "recipient_id": ObjectId(notifications_id),
        #         "read": False,
        #         "type": "mention"
        #     })

        notifications = [serialize_objectid(notification) for notification in notifications]

        return jsonify({
            "notifications": notifications,
            "likes_count": likes_count,
            "follows_count": follows_count,
            # "mentions_count": mentions_count,
            "unread_count": unread_count,
            "total": len(notifications),
            "has_more": len(notifications) == limit
        }), 200
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        return jsonify({"error": "Failed to get notifications"}), 500


# Endpoint to get users
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        query = request.args.get('q', '').lower()
        logger.debug(f"Fetching users with query: {query}")

        query_filter = {}
        if query:
            query_filter["$or"] = [
                {"username": {"$regex": query, "$options": "i"}},
                {"fullname": {"$regex": query, "$options": "i"}}
            ]

        users = db.users.find(query_filter)
        users_list = [
            {
                "_id": str(user["_id"]),
                "username": user.get("username", ""),
                "fullname": user.get("fullname", user.get("username", "")),
                "avatar": user.get("avatar", "/static/images/default-avatar.png")
            }
            for user in users
        ]

        logger.debug(f"Found {len(users_list)} users")
        return jsonify({"users": users_list}), 200

    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return jsonify({"error": "Failed to fetch users"}), 500

# Endpoint to get conversations for a user
@app.route('/conversations/<user_id>', methods=['GET'])
def get_conversations(user_id):
    try:
        logger.debug(f"Fetching conversations for user ID: {user_id}")

        # Validate user_id format
        try:
            user_object_id = ObjectId(user_id)
        except Exception as e:
            logger.error(f"Invalid user ID format: {user_id}, error: {str(e)}")
            return jsonify({"error": "Invalid user ID"}), 400

        # Fetch conversations where the user is a participant
        conversations = db.conversations.find({"participants": user_object_id})
        conversations_list = []

        for conv in conversations:
            # Fetch participant details
            participants = []
            for participant_id in conv["participants"]:
                user = db.users.find_one({"_id": participant_id})
                if user:
                    participants.append({
                        "_id": str(user["_id"]),
                        "username": user.get("username", ""),
                        "fullname": user.get("fullname", user.get("username", "")),
                        "avatar": user.get("avatar", "/static/images/default-avatar.png")
                    })

            # Find the other participant (not the requesting user)
            other_participant = next(
                (p for p in participants if p["_id"] != user_id), None
            )
            if not other_participant:
                continue

            # Format lastMessage
            last_message = conv.get("lastMessage")
            if last_message:
                sender = db.users.find_one({"_id": last_message["sender"]})
                last_message = {
                    "_id": str(last_message["_id"]),
                    "content": last_message["content"],
                    "sender": {
                        "_id": str(sender["_id"]) if sender else "",
                    },
                    "createdAt": last_message["createdAt"].isoformat()
                }

            conversations_list.append({
                "_id": str(conv["_id"]),
                "participant": other_participant,
                "lastMessage": last_message,
                "unreadCount": conv.get("unreadCount", 0)
            })

        logger.debug(f"Found {len(conversations_list)} conversations")
        return jsonify({"conversations": conversations_list}), 200

    except Exception as e:
        logger.error(f"Error fetching conversations: {str(e)}")
        return jsonify({"error": "Failed to fetch conversations"}), 500

# Endpoint to get messages for a conversation
@app.route('/messages/<conversation_id>', methods=['GET'])
def get_conversation_messages(conversation_id):
    try:
        logger.debug(f"Fetching messages for conversation ID: {conversation_id}")

        # Validate conversation_id format
        try:
            conversation_object_id = ObjectId(conversation_id)
        except Exception as e:
            logger.error(f"Invalid conversation ID format: {conversation_id}, error: {str(e)}")
            return jsonify({"error": "Invalid conversation ID"}), 400

        # Fetch messages for the conversation
        messages = db.messages.find({"conversationId": conversation_object_id}).sort("createdAt", 1)
        messages_list = []

        for message in messages:
            # Fetch sender and receiver details
            sender = db.users.find_one({"_id": message["senderId"]})
            if not sender:
                continue
            receiver = db.users.find_one({"_id": message["receiverId"]})
            if not receiver:
                continue

            messages_list.append({
                "_id": str(message["_id"]),
                "conversationId": str(message["conversationId"]),
                "sender": {
                    "_id": str(sender["_id"]),
                    "username": sender.get("username", ""),
                    "fullname": sender.get("fullname", sender.get("username", "")),
                    "avatar": sender.get("avatar", "/static/images/default-avatar.png")
                },
                "receiver": {
                    "_id": str(receiver["_id"]),
                    "username": receiver.get("username", ""),
                    "fullname": receiver.get("fullname", receiver.get("username", "")),
                    "avatar": receiver.get("avatar", "/static/images/default-avatar.png")
                },
                "content": message.get("content", ""),
                "createdAt": message["createdAt"].isoformat(),
                "isRead": message.get("isRead", False),
                "isDelivered": message.get("isDelivered", True)
            })

        logger.debug(f"Found {len(messages_list)} messages")
        return jsonify({"messages": messages_list}), 200

    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        return jsonify({"error": "Failed to fetch messages"}), 500


@app.route('/settings/<user_id>', methods=['GET'])
def get_profile_settings(user_id):
    """Get user profile settings"""
    try:
        if not ObjectId.is_valid(user_id):
            return jsonify({"success": False, "message": "Invalid user ID"}), 400
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        # Return user settings data
        return jsonify({
            "fullname": user.get("fullname", ""),
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "bio": user.get("bio", ""),
            "avatar": user.get("avatar", ""),
            "cover": user.get("cover", ""),
            "theme": user.get("theme", "light"),
            "notification_settings": user.get("notification_settings", {
                "email_notifications": True,
                "push_notifications": True,
                "new_follower": True,
                "post_likes": True,
                "post_comments": True,
                "mentions": True
            }),
            "privacy_settings": user.get("privacy_settings", {
                "profile_visibility": "public",
                "post_visibility": "public",
                "show_online_status": True
            })
        }), 200

    except Exception as e:
        logger.error(f"Error getting profile settings: {str(e)}")
        return jsonify({"error": "Failed to get profile settings"}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)