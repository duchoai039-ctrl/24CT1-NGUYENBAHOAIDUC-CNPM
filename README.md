# Perspect

Mạng xã hội chia sẻ "góc nhìn" ngắn: đăng bài (kèm ảnh), thích, bình luận, theo dõi, chủ đề, thông báo.
Web thật: https://perspect.onrender.com

## Kiến trúc (production)

| Phần | Dịch vụ |
|---|---|
| Web app | Django 5.2 (Python 3.14) trên **Render** |
| Database | **Neon PostgreSQL** |
| Ảnh người dùng tải lên | **Cloudinary** |
| File tĩnh (CSS, ảnh giao diện) | WhiteNoise |

Production database: **Neon PostgreSQL** (all models in `Blog/devBlog/models.py` are stored there).
Uploaded images: **Cloudinary**. The SQLite file is only a local development fallback.

## Mã nguồn

- `Blog/Blog/settings.py`: cấu hình (Neon qua `DATABASE_URL`, Cloudinary qua `CLOUDINARY_URL`)
- `Blog/devBlog/`: app chính (models, views, forms, templates, `static/css/main.css`)

Cách deploy và chạy trên máy: xem [DEPLOY.md](DEPLOY.md).
