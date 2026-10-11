from django.urls import path
# pyrefly: ignore [missing-import]
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),

    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('welcome/', views.complete_profile, name='complete_profile'),
    
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),

    path('profile/', views.profile, name='profile'),
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
    path('profile/<int:user_id>/follow/', views.toggle_follow, name='toggle_follow'),
    path('tim-kiem/', views.explore, name='explore'),
    path('thong-bao/', views.notifications, name='notifications'),
    path('thong-bao/so/', views.notification_count, name='notification_count'),
    path('tag/<int:tag_id>/', views.posts_by_tag, name='posts_by_tag'),
]