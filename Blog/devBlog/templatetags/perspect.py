from django import template
from django.utils import timezone

# pyrefly: ignore [missing-import]
from devBlog.models import Tag, display_name

register = template.Library()


@register.simple_tag
def chu_de():
    """Tất cả chủ đề, cho menu trái: {% chu_de as nav_tags %}."""
    return Tag.objects.all()


@register.simple_tag
def so_thong_bao(user):
    """Số thông báo chưa đọc cho cái chuông: {% so_thong_bao user as unread %}."""
    return user.notifications.filter(read=False).count() if user.is_authenticated else 0


@register.filter
def ten(user):
    """Tên hiện trên web: "Nguyễn Hoài Đức" (Họ + Tên)."""
    return display_name(user) if user else ''


@register.filter
def chu_dau(user):
    """Chữ trên avatar: chữ đầu của Tên ("Đức" -> "Đ")."""
    return (user.first_name or display_name(user))[:1].upper() if user else ''


@register.filter
def tong(user):
    """Tông màu sơn mài của avatar, cố định theo mã số người dùng (son / vàng / cánh gián / rêu)."""
    return f'tone-{user.id % 4}' if user and user.id else ''


@register.filter
def ngay(value):
    """Ngày kiểu nói tự nhiên: "9 tháng 10, 2026" (theo giờ Việt Nam)."""
    if not value:
        return ''
    d = timezone.localtime(value)
    return f'{d.day} tháng {d.month}, {d.year}'


@register.filter
def thoi_gian(value):
    """Mốc đăng bài tương đối: "Vừa xong", "5 phút trước", "23 giờ trước", "3 ngày trước";
    từ 4 ngày trở lên ghi ngày dd/mm/yyyy (theo giờ Việt Nam)."""
    if not value:
        return ''
    seconds = (timezone.now() - value).total_seconds()
    if seconds < 60:                       # kể cả giờ máy lệch làm thời gian ở tương lai
        return 'Vừa xong'
    if seconds < 3600:
        return f'{int(seconds // 60)} phút trước'
    if seconds < 86400:
        return f'{int(seconds // 3600)} giờ trước'
    days = int(seconds // 86400)
    if days <= 3:
        return f'{days} ngày trước'
    return timezone.localtime(value).strftime('%d/%m/%Y')


@register.filter
def dang_luc(value):
    """Cụm có chữ "Đăng" cho chỗ cần nói rõ: "Vừa đăng", "Đăng 2 giờ trước", "Đăng 05/10/2026"."""
    t = thoi_gian(value)
    if not t:
        return ''
    return 'Vừa đăng' if t == 'Vừa xong' else f'Đăng {t}'


@register.filter
def ngay_gio(value):
    """Ngày giờ đầy đủ "14:30, 09/10/2026" — hiện khi rê chuột lên mốc tương đối."""
    if not value:
        return ''
    return timezone.localtime(value).strftime('%H:%M, %d/%m/%Y')
