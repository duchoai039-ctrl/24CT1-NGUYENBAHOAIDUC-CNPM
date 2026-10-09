from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Post, Tag, UserProfile, Follow
from .forms import RegisterForm, PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.paginator import Paginator
from django.db.models import Q, Count, Exists, OuterRef

POSTS_PER_PAGE = 10


def posts_with_stats(posts, user):
    # Lấy sẵn tác giả, thẻ, số thích, số bình luận và "mình đã thích chưa"
    # trong vài truy vấn cố định, thay vì template hỏi DB riêng cho từng bài.
    return posts.select_related('author').prefetch_related('tags').annotate(
        n_likes=Count('likes', distinct=True),
        n_comments=Count('comments', distinct=True),
        is_liked=Exists(Post.likes.through.objects.filter(post=OuterRef('pk'), user_id=user.id)),
    )


def render_feed(request, posts, extra):
    page = Paginator(posts_with_stats(posts, request.user), POSTS_PER_PAGE).get_page(request.GET.get('page'))
    return render(request, 'devBlog/home.html', {
        'posts': page,
        'latest_posts': Post.objects.order_by('-created_at')[:5],
        'tags': Tag.objects.all(),
        **extra,
    })


def home(request):
    # Chưa đăng nhập thì luôn thấy trang landing (bài viết chỉ dành cho thành viên)
    if not request.user.is_authenticated:
        return render(request, 'devBlog/landing.html')

    query = request.GET.get('q', '').strip()

    if query:
        posts = Post.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__name__icontains=query) |
            Q(author__username__icontains=query)
        ).distinct().order_by('-created_at')
    else:
        posts = Post.objects.all().order_by('-created_at')

    return render_feed(request, posts, {'query': query})


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    comments = post.comments.all().order_by('-created_at')

    if request.method == 'POST':
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()

            return redirect('post_detail', post_id=post.id)

    else:
        form = CommentForm()

    return render(request, 'devBlog/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form
    })


@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)

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
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Create user profile and save interests
            profile = UserProfile.objects.create(user=user)
            interests = form.cleaned_data.get('interests')
            if interests:
                profile.interests.set(interests)

            request.session['registered_username'] = user.username
            messages.success(request, 'Đăng ký tài khoản thành công! Vui lòng đăng nhập.')
            return redirect('login')

    else:
        form = RegisterForm()

    tags = Tag.objects.all()

    return render(request, 'devBlog/register.html', {
        'form': form,
        'tags': tags
    })


def login_view(request):
    registered_username = request.session.pop('registered_username', '')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('home')

        return render(request, 'devBlog/login.html', {
            'error': 'Sai tên đăng nhập hoặc mật khẩu.',
            'registered_username': username,
        })

    return render(request, 'devBlog/login.html', {
        'registered_username': registered_username,
    })


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

            return redirect('my_posts')

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
        return redirect('home')

    return render(request, 'devBlog/delete_post.html', {
        'post': post
    })

@login_required
def profile(request):
    return user_profile(request, request.user.username)


@login_required
def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
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
    })


@login_required
@require_POST
def toggle_follow(request, username):
    target_user = get_object_or_404(User, username=username)

    if target_user == request.user:
        return redirect('user_profile', username=username)

    # Xóa trước; không có gì để xóa nghĩa là chưa theo dõi -> tạo mới.
    # get_or_create tự xử lý khi hai lần bấm cùng tạo (không văng IntegrityError).
    deleted, _ = Follow.objects.filter(
        follower=request.user, following=target_user
    ).delete()
    if not deleted:
        Follow.objects.get_or_create(follower=request.user, following=target_user)

    return redirect('user_profile', username=username)


@login_required
def my_posts(request):
    posts = posts_with_stats(
        Post.objects.filter(author=request.user).order_by('-created_at'),
        request.user,
    )

    return render(request, 'devBlog/my_posts.html', {
        'posts': posts
    })


@login_required
def posts_by_tag(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    posts = Post.objects.filter(tags=tag).order_by('-created_at')

    return render_feed(request, posts, {'current_tag': tag})