from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

# pyrefly: ignore [missing-import]
from .forms import normalize_phone


class EmailOrPhoneBackend(ModelBackend):
    """Đăng nhập bằng Gmail hoặc số điện thoại (không còn tên đăng nhập)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        ident = (username or kwargs.get('email') or '').strip()
        if not ident or password is None:
            return None
        if '@' in ident:
            users = User.objects.filter(email__iexact=ident)
        elif normalize_phone(ident):
            users = User.objects.filter(profile__phone=normalize_phone(ident))
        else:
            # Chỉ quản trị viên tạo bằng createsuperuser (có thể không có email) được vào /admin/ bằng username
            users = User.objects.filter(username=ident, is_staff=True)
        user = users.order_by('id').first()
        if user is None:
            User().set_password(password)   # tốn thời gian như khi có tài khoản, để không đoán được tài khoản nào tồn tại
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
