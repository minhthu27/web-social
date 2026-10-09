# Web MXH / Social Media Web App

Dự án là một ứng dụng mạng xã hội dạng web được xây dựng bằng Flask, MongoDB và template HTML/CSS/JS. Ứng dụng hỗ trợ đăng ký, đăng nhập, hồ sơ người dùng, bài viết, bình luận, thông báo, tin nhắn, tìm kiếm và quản trị admin.

## Tính năng chính

- Đăng ký / đăng nhập / xác thực JWT
- Trang hồ sơ người dùng
- Tạo, xem và quản lý bài viết
- Bình luận trên bài viết
- Thông báo và tin nhắn
- Tìm kiếm người dùng và bài viết
- Giao diện admin
- Upload ảnh và tài nguyên mặc định

## Công nghệ sử dụng

- Python 3.10+
- Flask
- Flask-CORS
- Flask-JWT-Extended
- MongoDB (PyMongo)
- Pillow
- Python-dotenv

## Cấu trúc thư mục

- `app.py` - ứng dụng chính
- `api.py` - API phụ trợ
- `backend/` - các blueprint và logic nghiệp vụ
- `config/` - cấu hình MongoDB, JWT, upload
- `scripts/` - tạo tài nguyên mặc định và dữ liệu mẫu
- `static/` - file CSS, JS, uploads
- `templates/` - giao diện HTML

## Yêu cầu môi trường

- Python 3.10+
- MongoDB đang chạy hoặc dùng URI MongoDB Atlas
- Virtual environment khuyến nghị

## Cài đặt

1. Tạo môi trường ảo:

```bash
python -m venv venv
```

2. Kích hoạt môi trường ảo:

Windows (PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source venv/bin/activate
```

3. Cài đặt dependencies:

```bash
pip install -r requirements.txt
```

## Cấu hình môi trường

Tạo file `.env` ở thư mục gốc bằng cách sao chép từ `.env.example`:

```bash
copy .env.example .env
```

Sau đó chỉnh sửa các giá trị theo môi trường của bạn:

- `MONGO_URI`: dùng MongoDB local (`mongodb://localhost:27017/connectify_db`) hoặc chuỗi kết nối MongoDB Atlas của chính bạn.
- `JWT_SECRET_KEY` và `SECRET_KEY`: bắt buộc, đặt chuỗi ngẫu nhiên riêng của bạn.

Không commit file `.env` (đã có trong `.gitignore`).

## Chạy ứng dụng

```bash
python app.py
```

Ứng dụng sẽ chạy mặc định trên:

- http://127.0.0.1:5001

## Lưu ý

- Khi ứng dụng khởi động, hệ thống sẽ tự tạo thư mục upload và dữ liệu mẫu nếu cần.
- Nếu MongoDB không kết nối, bạn cần kiểm tra lại `MONGO_URI` và dịch vụ MongoDB.

## Tác giả

Dự án được phát triển cho mục đích học tập và demo web social media.
