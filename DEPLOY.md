# Đưa Perspect lên mạng (miễn phí)

| Phần | Dịch vụ | Ghi chú |
|---|---|---|
| Chạy web Django | **Render** (gói Free) | Ngủ sau 15 phút không ai vào; lần đầu vào lại chờ ~1 phút |
| Database PostgreSQL | **Neon** (gói Free) | Không hết hạn; xem/sửa dữ liệu ở console.neon.tech |
| Ảnh người dùng tải lên | **Cloudinary** (gói Free) | Ổ đĩa Render bị xóa mỗi lần deploy, nên ảnh phải để ở đây |

Trên máy cá nhân web vẫn chạy như cũ (SQLite, ảnh trong `Blog/media/`).
Chỉ khi có biến `DATABASE_URL` / `CLOUDINARY_URL` thì mới dùng Neon / Cloudinary.

> **Chuỗi kết nối Neon và Cloudinary là mật khẩu.** Chỉ dán vào trang Render hoặc cửa sổ lệnh
> trên máy mình. Không đưa vào code, GitHub, chat hay gửi cho người khác.

---

## Bước 1 — Neon (database)

1. Đăng nhập https://console.neon.tech (dùng tài khoản GitHub cho nhanh).
2. **Create project**: đặt tên `perspect`, Postgres bản mới nhất, vùng **AWS Asia Pacific (Singapore)**.
3. Mở **Connect**, chọn database `neondb`, **tắt "Connection pooling"**, rồi copy chuỗi dạng
   `postgresql://...@ep-....ap-southeast-1.aws.neon.tech/neondb?sslmode=require`.
   (Django giữ kết nối lâu, nên dùng kết nối trực tiếp, không qua pooler.)

## Bước 2 — Cloudinary (ảnh)

1. Đăng nhập https://cloudinary.com, tạo tài khoản Free.
2. Ở **Dashboard / API Keys**, copy **API environment variable** dạng
   `cloudinary://<api_key>:<api_secret>@<cloud_name>` (bỏ chữ `CLOUDINARY_URL=` ở đầu nếu có).

## Bước 3 — Chuyển dữ liệu cũ sang Neon và Cloudinary (chạy trên máy mình)

Làm bước này **trước khi đưa link cho người khác**: nạp dữ liệu cũ sau khi đã có người đăng ký mới
có thể ghi đè lên tài khoản / bài viết mới.

Trong PowerShell, venv đã bật, đứng ở thư mục `Blog`:

```powershell
# 3.1 Xuất dữ liệu từ SQLite (chưa đặt DATABASE_URL nên đang đọc db.sqlite3)
python -X utf8 manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.permission -e admin.logentry -e sessions --indent 2 -o du_lieu.json

# 3.2 Trỏ tạm cửa sổ này tới Neon và Cloudinary (chỉ có hiệu lực trong cửa sổ này)
$env:DATABASE_URL = "<dán chuỗi Neon>"
$env:CLOUDINARY_URL = "<dán chuỗi Cloudinary>"

# 3.3 Tạo bảng trên Neon rồi nạp dữ liệu
python manage.py migrate
python -X utf8 manage.py loaddata du_lieu.json

# 3.4 Tải ảnh cũ trong media/ lên Cloudinary và cập nhật đường dẫn ảnh
python manage.py upload_media_cloudinary

# 3.5 Tạo tài khoản quản trị để vào /admin/
python manage.py createsuperuser

# 3.6 Dọn dẹp: xóa file dữ liệu (có mật khẩu đã mã hóa) và đóng cửa sổ PowerShell này
Remove-Item du_lieu.json
```

## Bước 4 — Render (chạy web)

1. Đẩy code mới nhất lên GitHub.
2. Đăng nhập https://dashboard.render.com bằng GitHub → **New → Blueprint** → chọn repo này.
   Render đọc `render.yaml` và tạo dịch vụ `perspect` (vùng Singapore, gói Free).
3. Render hỏi giá trị cho `DATABASE_URL` và `CLOUDINARY_URL`: dán 2 chuỗi ở Bước 1 và 2.
   `DJANGO_SECRET_KEY` Render tự tạo.
4. **Apply**. Render chạy `build.sh` (cài thư viện, gom file tĩnh, cập nhật bảng), rồi khởi động web.
5. Xong sẽ có link `https://perspect.onrender.com` (hoặc tên tương tự Render cấp).

## Sau khi deploy

- **Xem / sửa dữ liệu:** `https://<link>/admin/` (tài khoản quản trị ở bước 3.5), hoặc console.neon.tech → **Tables** / **SQL Editor**.
- **Cập nhật web:** đẩy code lên nhánh `main` là Render tự deploy lại.
- **Xem lỗi:** Render → dịch vụ `perspect` → **Logs**. Cần trang lỗi chi tiết thì tạm đặt biến `DJANGO_DEBUG=1`, xem xong **xóa ngay**.
- Python trên Render lấy từ file `.python-version` (3.14, cùng bản trên máy).
