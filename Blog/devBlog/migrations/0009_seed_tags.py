from django.db import migrations

# Chủ đề mặc định. Neon từng bị trống bảng này nên web thật không có chủ đề để chọn.
TAGS = ['Công nghệ', 'Giải trí', 'Thể thao', 'Du lịch', 'Ẩm thực',
        'Giáo dục', 'Sức khỏe', 'Âm nhạc', 'Phim ảnh', 'Game']


def seed_tags(apps, schema_editor):
    Tag = apps.get_model('devBlog', 'Tag')
    for name in TAGS:
        Tag.objects.get_or_create(name=name)   # đã có thì bỏ qua


class Migration(migrations.Migration):
    dependencies = [('devBlog', '0008_notification')]
    operations = [migrations.RunPython(seed_tags, migrations.RunPython.noop)]
