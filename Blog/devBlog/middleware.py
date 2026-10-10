from django.shortcuts import redirect
from django.urls import reverse


class RequireIntroMiddleware:
    """Đã đăng nhập mà chưa có Họ + Tên (vừa đăng ký, hoặc tài khoản cũ) thì đưa về bước giới thiệu."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and not (user.first_name and user.last_name):
            intro = reverse('complete_profile')
            allowed = (intro, reverse('logout'), '/admin/', '/static/', '/media/')
            if not request.path.startswith(allowed):
                return redirect(intro)
        return self.get_response(request)
