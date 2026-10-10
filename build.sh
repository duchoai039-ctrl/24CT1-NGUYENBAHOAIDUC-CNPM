#!/usr/bin/env bash
# Render chạy file này mỗi lần deploy (xem render.yaml).
set -o errexit   # lỗi ở bước nào thì dừng luôn, không deploy bản hỏng

pip install -r requirements.txt

cd Blog
python manage.py collectstatic --no-input   # gom CSS, phông, video vào staticfiles/ cho WhiteNoise
python manage.py migrate --no-input         # tạo / cập nhật bảng trong database Neon
