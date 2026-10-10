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
from django.views.static import serve as serve_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('devBlog.urls')),
]

# CSS/phông/video do WhiteNoise phục vụ (xem MIDDLEWARE).
# Ảnh upload: trên Render nằm ở Cloudinary (link thẳng tới Cloudinary);
# trên máy nằm ở media/ nên Django tự phục vụ, kể cả khi DEBUG tắt (chạy thử qua tunnel).
if not settings.USE_CLOUDINARY:
    urlpatterns.append(
        re_path(r'^media/(?P<path>.*)$', serve_media, {'document_root': settings.MEDIA_ROOT}),
    )
