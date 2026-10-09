import re

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import Truncator

OPENING_MAX_CHARS = 160
TITLE_MAX_CHARS = 100
EXCERPT_MAX_CHARS = 300


def first_sentence(text):
    """Câu đầu tiên của dòng có chữ đầu tiên (bỏ dòng trống ở đầu)."""
    first_line = text.strip().split('\n', 1)[0]
    return re.split(r'(?<=[.!?…])\s+', first_line, maxsplit=1)[0].strip()


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    interests = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='interested_users'
    )

    def __str__(self):
        return self.user.username


class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total_likes(self):
        return self.likes.count()

    def total_comments(self):
        return self.comments.count()

    @property
    def opening(self):
        # "Góc nhìn" của bài: câu mở đầu (dùng ở danh sách "Mới đăng", trang xóa bài, tên tab)
        return Truncator(first_sentence(self.content)).chars(OPENING_MAX_CHARS)

    @property
    def excerpt(self):
        # Đoạn nội dung hiện ở bảng tin (bài không còn tiêu đề nên hiện dài hơn một câu)
        return Truncator(self.content.strip()).chars(EXCERPT_MAX_CHARS)

    @property
    def has_more(self):
        return len(self.content.strip()) > EXCERPT_MAX_CHARS

    def save(self, *args, **kwargs):
        # Không còn ô nhập tiêu đề: tiêu đề tự lấy từ câu đầu của nội dung mỗi lần lưu.
        # Vẫn giữ cột title cho tên tab trình duyệt, tìm kiếm và trang quản trị.
        self.title = Truncator(first_sentence(self.content)).chars(TITLE_MAX_CHARS) or 'Bài viết'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.author.username + ': ' + self.content[:30]


class Follow(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f'{self.follower.username} follows {self.following.username}'