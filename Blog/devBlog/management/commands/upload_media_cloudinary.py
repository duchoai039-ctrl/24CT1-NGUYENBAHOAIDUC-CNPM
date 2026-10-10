"""Tải ảnh cũ trong thư mục media/ lên Cloudinary và cập nhật đường dẫn trong database.

Dùng một lần khi chuyển sang Render (cần đặt CLOUDINARY_URL và DATABASE_URL trỏ tới database mới).
Chạy lại nhiều lần không sao: ảnh đã lên Cloudinary sẽ được bỏ qua.
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from devBlog.models import Post


class Command(BaseCommand):
    help = 'Tải ảnh cũ trong media/ lên Cloudinary và cập nhật đường dẫn ảnh của bài viết'

    def handle(self, *args, **options):
        if not settings.USE_CLOUDINARY:
            raise CommandError('Chưa đặt biến CLOUDINARY_URL nên không biết tải ảnh lên đâu.')

        media_root = Path(settings.MEDIA_ROOT)
        uploaded = already = missing = 0
        for post in Post.objects.exclude(image='').exclude(image__isnull=True):
            name = post.image.name
            local = media_root / name
            if not local.exists():
                if name.startswith('media/'):      # tên kiểu Cloudinary: đã tải lên từ trước
                    already += 1
                else:
                    missing += 1
                    self.stderr.write(f'Bài {post.id}: không tìm thấy {local}')
                continue
            with local.open('rb') as f:
                new_name = default_storage.save(name, File(f, name=local.name))
            # update() thay vì save() để không chạm vào updated_at / tiêu đề tự sinh
            Post.objects.filter(id=post.id).update(image=new_name)
            uploaded += 1
            self.stdout.write(f'Bài {post.id}: {name} -> {new_name}')

        self.stdout.write(self.style.SUCCESS(
            f'Xong: tải lên {uploaded}, đã có sẵn {already}, thiếu file {missing}.'
        ))
