from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Post, Comment, Tag, UserProfile, Follow, Notification, first_sentence, display_name
from .forms import RegisterForm, IntroForm, PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.paginator import Paginator
from django.db.models import Q, Count, Exists, OuterRef, Max, F, Value
from django.db.models.functions import Concat
from django.utils import timezone
from django.utils.text import Truncator
from datetime import timedelta

POSTS_PER_PAGE = 10
QUOTE_MIN_CHARS = 20
QUOTE_MAX_CHARS = 120


def posts_with_stats(posts, user):
    # Lấy sẵn tác giả, thẻ, số thích, số bình luận và "mình đã thích chưa"
    # trong vài truy vấn cố định, thay vì template hỏi DB riêng cho từng bài.
    return posts.select_related('author').prefetch_related('tags').annotate(
        n_likes=Count('likes', distinct=True),
        n_comments=Count('comments', distinct=True),
        is_liked=Exists(Post.likes.through.objects.filter(post=OuterRef('pk'), user_id=user.id)),
    )


FOLLOWING_SIDEBAR_LIMIT = 8


def following_sidebar(user):
    # Cột "Đang theo dõi": người đăng bài gần nhất lên đầu, người chưa có bài xuống cuối.
    following = (User.objects.filter(followers__follower=user)
                 .annotate(last_post_at=Max('post__created_at'))
                 .order_by(F('last_post_at').desc(nulls_last=True), 'first_name', 'id'))
    total = following.count()
    shown = list(following[:FOLLOWING_SIDEBAR_LIMIT])
    recent = timezone.now() - timedelta(hours=24)
    for u in shown:
        u.posted_recently = bool(u.last_post_at and u.last_post_at >= recent)
    return {
        'following_users': shown,
        'following_more': total - len(shown),
        'people_you_may_know': people_you_may_know(user),
    }


SUGGESTION_LIMIT = 3


def people_you_may_know(user):
    """ "Những người bạn có thể biết": người mình chưa theo dõi, xếp theo
    đang theo dõi mình > nhiều bạn chung > cùng chủ đề quan tâm > viết nhiều > mới tham gia."""
    following_ids = Follow.objects.filter(follower=user).values('following')
    my_tags = UserProfile.interests.through.objects.filter(userprofile__user=user).values('tag')
    return (User.objects
            .exclude(id=user.id).exclude(id__in=following_ids)
            .filter(is_active=True)
            # Vừa đăng ký dở (chưa có tên, chỉ có mã ẩn u + 12 ký tự) thì chưa gợi ý; tài khoản cũ vẫn gợi ý bằng tên cũ
            .exclude(first_name='', username__regex=r'^u[0-9a-f]{12}$')
            .annotate(
                follows_me=Exists(Follow.objects.filter(follower=OuterRef('pk'), following=user)),
                mutual=Count('followers', filter=Q(followers__follower__in=following_ids), distinct=True),
                shared=Count('profile__interests', filter=Q(profile__interests__in=my_tags), distinct=True),
                n_posts=Count('post', distinct=True),
            )
            .order_by('-follows_me', '-mutual', '-shared', '-n_posts', '-date_joined')[:SUGGESTION_LIMIT])


def render_feed(request, posts, extra):
    page = Paginator(posts_with_stats(posts, request.user), POSTS_PER_PAGE).get_page(request.GET.get('page'))
    return render(request, 'devBlog/home.html', {
        'posts': page,
        'latest_posts': Post.objects.order_by('-created_at')[:5],
        'tags': Tag.objects.all(),
        **following_sidebar(request.user),
        **extra,
    })


def featured_quote(posts):
    # "Góc nhìn được thích nhất" ở trang cá nhân (posts = bài của một người):
    # câu đầu (tối đa 120 ký tự) của bài được thích nhiều nhất, hòa thì lấy bài mới hơn.
    # Bỏ qua câu quá ngắn (vd "hehe") vì không ra "góc nhìn"; chỉ xét 20 bài đứng đầu.
    top = (posts.select_related('author')
           .annotate(n_likes=Count('likes'))
           .order_by('-n_likes', '-created_at')[:20])
    for post in top:
        sentence = first_sentence(post.content)
        if len(sentence) >= QUOTE_MIN_CHARS:
            return {
                'text': Truncator(sentence).chars(QUOTE_MAX_CHARS),
                'author': display_name(post.author),
                'post_id': post.id,
                'created_at': post.created_at,
                'likes': post.n_likes,
            }
    return None


def home(request):
    # Chưa đăng nhập thì luôn thấy trang landing (bài viết chỉ dành cho thành viên)
    if not request.user.is_authenticated:
        return render(request, 'devBlog/landing.html')

    query = request.GET.get('q', '').strip()

    if query:
        # Tìm theo tên tác giả: ghép "Họ Tên" để gõ cả họ lẫn tên vẫn ra
        posts = Post.objects.annotate(
            author_name=Concat('author__last_name', Value(' '), 'author__first_name'),
        ).filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__name__icontains=query) |
            Q(author_name__icontains=query)
        ).distinct().order_by('-created_at')
    else:
        posts = Post.objects.all().order_by('-created_at')

    tag_id = request.GET.get('tag', '')
    current_tag = Tag.objects.filter(id=tag_id).first() if tag_id.isdigit() else None
    if current_tag:
        posts = posts.filter(tags=current_tag)

    return render_feed(request, posts, {'query': query, 'current_tag': current_tag})


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    comments = post.comments.select_related('author').order_by('-created_at')

    if request.method == 'POST':
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            if post.author != request.user:
                Notification.objects.create(recipient=post.author, actor=request.user, kind='comment', post=post)

            return redirect(reverse('post_detail', args=[post.id]) + '#binh-luan')

    else:
        form = CommentForm()

    return render(request, 'devBlog/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
        'is_liked': post.likes.filter(id=request.user.id).exists(),
        'like_count': post.likes.count(),
    })


@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    liked = not post.likes.filter(id=request.user.id).exists()
    if liked:
        post.likes.add(request.user)
        if post.author != request.user:
            Notification.objects.create(recipient=post.author, actor=request.user, kind='like', post=post)
    else:
        post.likes.remove(request.user)
        # Bỏ thích thì rút thông báo, bấm qua lại không làm chuông đầy rác
        Notification.objects.filter(recipient=post.author, actor=request.user, kind='like', post=post).delete()

    # Gọi từ JavaScript (nút thích không tải lại trang): trả trạng thái mới
    if request.headers.get('X-Requested-With') == 'fetch':
        return JsonResponse({'liked': liked, 'count': post.likes.count()})

    # Chỉ quay lại trang trước nếu trang đó thuộc web mình (chặn open redirect)
    next_url = request.META.get('HTTP_REFERER')
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect('post_detail', post_id=post.id)

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Đăng nhập luôn rồi sang bước giới thiệu (Họ + Tên), không bắt nhập lại
            login(request, user, backend='devBlog.backends.EmailOrPhoneBackend')
            return redirect('complete_profile')
    else:
        form = RegisterForm()

    return render(request, 'devBlog/register.html', {'form': form})


@login_required
def complete_profile(request):
    """ "Mọi người có thể biết đến bạn thông qua": Họ + Tên (bắt buộc) và chủ đề quan tâm."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    editing = bool(request.user.first_name)   # đã có tên -> đang sửa thông tin, không phải bước chào mừng
    if request.method == 'POST':
        form = IntroForm(request.POST)
        if form.is_valid():
            user = request.user
            user.last_name = form.cleaned_data['last_name']
            user.first_name = form.cleaned_data['first_name']
            user.save(update_fields=['last_name', 'first_name'])
            profile.interests.set(form.cleaned_data['interests'])
            if editing:
                messages.success(request, 'Đã lưu thông tin.')
                return redirect('profile')
            messages.success(request, f'Chào {user.first_name}, chúc bạn có những góc nhìn thú vị!')
            return redirect('home')
    else:
        form = IntroForm(initial={
            'last_name': request.user.last_name,
            'first_name': request.user.first_name,
            'interests': profile.interests.all(),
        })

    return render(request, 'devBlog/welcome.html', {'form': form, 'tags': Tag.objects.all(), 'editing': editing})


def login_view(request):
    if request.method == 'POST':
        ident = request.POST.get('ident', '').strip()
        user = authenticate(request, username=ident, password=request.POST.get('password'))
        if user is not None:
            login(request, user)
            return redirect('home')

        return render(request, 'devBlog/login.html', {
            'error': 'Sai Gmail / số điện thoại hoặc mật khẩu.',
            'ident': ident,
        })

    return render(request, 'devBlog/login.html')


def csrf_failure(request, reason=''):
    # Trang đang mở còn mã CSRF cũ (đăng nhập lại ở tab khác, bấm Back sau khi đăng nhập).
    # Đăng xuất thì vẫn cho thoát (cùng lắm web lạ làm mình bị đăng xuất, vô hại);
    # form khác vẫn bị chặn như cũ, chỉ báo bằng lời dễ hiểu thay trang 403.
    if request.path == reverse('logout'):
        logout(request)
        return redirect('login')
    messages.error(request, 'Trang đã cũ, bạn tải lại rồi thử lần nữa nhé.')
    back = request.META.get('HTTP_REFERER')
    if back and url_has_allowed_host_and_scheme(back, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(back)
    return redirect('home')


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()  # Save ManyToMany tags
            Notification.objects.bulk_create(
                Notification(recipient_id=f.follower_id, actor=request.user, kind='post', post=post)
                for f in Follow.objects.filter(following=request.user)
            )

            messages.success(request, 'Đã đăng bài.')
            return redirect('post_detail', post_id=post.id)

    else:
        form = PostForm()

    return render(request, 'devBlog/create_post.html', {
        'form': form
    })

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('post_detail', post_id=post.id)

    if request.method == 'POST':
        # Ghi lại tên ảnh cũ trước is_valid(), vì is_valid() gán ảnh mới vào post
        old_image = post.image.name
        form = PostForm(request.POST, request.FILES, instance=post)

        if form.is_valid():
            form.save()
            # Đã đổi ảnh -> xóa file ảnh cũ khỏi ổ đĩa (lưu DB xong mới xóa file)
            if old_image and old_image != post.image.name:
                post.image.storage.delete(old_image)
            return redirect('post_detail', post_id=post.id)

    else:
        form = PostForm(instance=post)

    return render(request, 'devBlog/edit_post.html', {
        'form': form,
        'post': post
    })


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('post_detail', post_id=post.id)

    if request.method == 'POST':
        image = post.image
        post.delete()
        # Xóa bài xong mới xóa file ảnh, để lỡ xóa file lỗi thì DB vẫn đúng
        if image:
            image.delete(save=False)
        messages.success(request, 'Đã xóa bài.')
        return redirect('home')

    return render(request, 'devBlog/delete_post.html', {
        'post': post
    })

@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author == request.user:
        comment.delete()
        messages.success(request, 'Đã xóa bình luận.')
    return redirect(reverse('post_detail', args=[comment.post_id]) + '#binh-luan')

@login_required
def profile(request):
    return user_profile(request, request.user.id)


@login_required
def user_profile(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    posts = posts_with_stats(
        Post.objects.filter(author=profile_user).order_by('-created_at'),
        request.user,
    )

    total_likes_received = Post.likes.through.objects.filter(post__author=profile_user).count()
    follower_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()
    user_profile_obj, _ = UserProfile.objects.get_or_create(user=profile_user)

    is_own_profile = (request.user == profile_user)
    is_following = False
    if not is_own_profile:
        is_following = Follow.objects.filter(
            follower=request.user, following=profile_user
        ).exists()

    return render(request, 'devBlog/profile.html', {
        'profile_user': profile_user,
        'posts': posts,
        'total_likes': total_likes_received,
        'follower_count': follower_count,
        'following_count': following_count,
        'user_profile': user_profile_obj,
        'is_own_profile': is_own_profile,
        'is_following': is_following,
        'top_quote': featured_quote(Post.objects.filter(author=profile_user)),
    })


@login_required
@require_POST
def toggle_follow(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    is_fetch = request.headers.get('X-Requested-With') == 'fetch'

    if target_user == request.user:
        if is_fetch:
            return JsonResponse({'error': 'Không thể tự theo dõi chính mình.'}, status=400)
        return redirect('user_profile', user_id=user_id)

    # Xóa trước; không có gì để xóa nghĩa là chưa theo dõi -> tạo mới.
    # get_or_create tự xử lý khi hai lần bấm cùng tạo (không văng IntegrityError).
    deleted, _ = Follow.objects.filter(
        follower=request.user, following=target_user
    ).delete()
    if deleted:
        Notification.objects.filter(recipient=target_user, actor=request.user, kind='follow').delete()
    else:
        _, created = Follow.objects.get_or_create(follower=request.user, following=target_user)
        if created:
            Notification.objects.create(recipient=target_user, actor=request.user, kind='follow')

    # Gọi từ JavaScript (nút theo dõi không tải lại trang): trả trạng thái mới
    if is_fetch:
        return JsonResponse({
            'following': not deleted,
            'followers': Follow.objects.filter(following=target_user).count(),
        })

    return redirect('user_profile', user_id=user_id)


@login_required
def posts_by_tag(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    posts = Post.objects.filter(tags=tag).order_by('-created_at')

    return render_feed(request, posts, {'current_tag': tag})


@login_required
def notifications(request):
    items = list(request.user.notifications.select_related('actor', 'post')[:50])
    # Mở trang là coi như đã đọc hết; `items` đã lấy trước nên vẫn tô được dòng mới
    request.user.notifications.filter(read=False).update(read=True)
    return render(request, 'devBlog/notifications.html', {'items': items})


@login_required
def notification_count(request):
    return JsonResponse({'unread': request.user.notifications.filter(read=False).count()})


@login_required
def explore(request):
    # Mục "Tìm kiếm" ở thanh dưới trên điện thoại: ô tìm + danh sách chủ đề
    return render(request, 'devBlog/explore.html')
