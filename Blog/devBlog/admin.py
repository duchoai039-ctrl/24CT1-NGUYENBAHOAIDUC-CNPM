from django.contrib import admin
from django.db.models import Count
from django.utils.text import Truncator

# pyrefly: ignore [missing-import]
from .models import Post, Comment, Tag, UserProfile, Follow

admin.site.site_header = 'Perspect — Quản trị'
admin.site.site_title = 'Perspect'
admin.site.index_title = 'Dữ liệu của web'


def short(text, length=60):
    return Truncator(text).chars(length)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'noi_dung', 'author', 'created_at', 'so_thich', 'so_binh_luan')
    list_display_links = ('id', 'noi_dung')
    list_filter = ('created_at', 'tags')
    search_fields = ('content', 'author__username')
    autocomplete_fields = ('author', 'likes')
    filter_horizontal = ('tags',)
    readonly_fields = ('title', 'created_at', 'updated_at')   # title tự lấy từ câu đầu nội dung
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author').annotate(
            n_likes=Count('likes', distinct=True), n_comments=Count('comments', distinct=True),
        )

    @admin.display(description='Nội dung')
    def noi_dung(self, obj):
        return short(obj.content)

    @admin.display(description='Lượt thích', ordering='n_likes')
    def so_thich(self, obj):
        return obj.n_likes

    @admin.display(description='Bình luận', ordering='n_comments')
    def so_binh_luan(self, obj):
        return obj.n_comments


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'noi_dung', 'author', 'bai_viet', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username', 'post__content')
    autocomplete_fields = ('post', 'author')
    ordering = ('-created_at',)
    list_select_related = ('author', 'post')

    @admin.display(description='Bình luận')
    def noi_dung(self, obj):
        return short(obj.content)

    @admin.display(description='Trong bài')
    def bai_viet(self, obj):
        return short(obj.post.content, 40)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')
    autocomplete_fields = ('follower', 'following')
    list_select_related = ('follower', 'following')
    ordering = ('-created_at',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'so_bai')
    search_fields = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(n_posts=Count('posts'))

    @admin.display(description='Số bài', ordering='n_posts')
    def so_bai(self, obj):
        return obj.n_posts


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)
    autocomplete_fields = ('user',)
    filter_horizontal = ('interests',)
