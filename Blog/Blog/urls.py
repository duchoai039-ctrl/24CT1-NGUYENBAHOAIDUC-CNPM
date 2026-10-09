"""
URL configuration for Blog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.contrib.staticfiles.views import serve as serve_static
from django.views.static import serve as serve_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('devBlog.urls')),
    # shortcut: Django tự phục vụ CSS và ảnh upload kể cả khi DEBUG tắt.
    # Đủ cho chạy runserver + tunnel với ít người dùng; deploy thật thì dùng whitenoise hoặc nginx.
    re_path(r'^static/(?P<path>.*)$', serve_static, {'insecure': True}),
    re_path(r'^media/(?P<path>.*)$', serve_media, {'document_root': settings.MEDIA_ROOT}),
]
