import re

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import Truncator

OPENING_MAX_CHARS = 160
TITLE_MAX_CHARS = 100
EXCERPT_MAX_CHARS = 300


def display_name(user):
    """Tên hiện trên web, theo thứ tự Việt Nam: Họ + Tên ("Nguyễn Hoài Đức").
    Tài khoản cũ chưa điền tên thì tạm dùng tên đăng nhập cũ (vốn đã công khai),
    không dùng email để khỏi lộ email."""
    return f'{user.last_name} {user.first_name}'.strip() or user.username


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
    # Dạng 0xxxxxxxxx (xem forms.normalize_phone). Tài khoản cũ chưa có số nên cho phép trống;
    # NULL không tính là trùng nhau nên unique vẫn đúng.
    phone = models.CharField(max_length=10, unique=True, null=True, blank=True)

    def __str__(self):
        return display_name(self.user)


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
    def lead(self):
        # Câu mở đầu nguyên vẹn, hiện to hơn (bảng tin cắt bớt bằng |truncatechars)
        return first_sentence(self.content)

    @property
    def rest(self):
        # Toàn bộ phần sau câu mở đầu (trang chi tiết). first_sentence luôn là phần đầu của content.strip()
        return self.content.strip()[len(self.lead):].strip()

    @property
    def excerpt_rest(self):
        # Phần đoạn trích sau câu mở đầu. first_sentence luôn là phần đầu của content.strip()
        room = EXCERPT_MAX_CHARS - len(self.lead)
        return Truncator(self.rest).chars(room) if room > 0 else ''

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
        return display_name(self.author) + ': ' + self.content[:30]


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
        return f'{display_name(self.follower)} theo dõi {display_name(self.following)}'

class Notification(models.Model):
    """Một dòng trong chuông thông báo của `recipient`."""
    KINDS = [
        ('comment', 'bình luận bài của bạn'),
        ('like', 'thích bài của bạn'),
        ('follow', 'đã theo dõi bạn'),
        ('post', 'vừa đăng bài mới'),
    ]
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    kind = models.CharField(max_length=10, choices=KINDS)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['recipient', 'read'])]

    def __str__(self):
        return f'{display_name(self.actor)} {self.get_kind_display()}'
