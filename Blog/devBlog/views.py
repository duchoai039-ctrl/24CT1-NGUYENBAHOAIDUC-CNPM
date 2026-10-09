from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Post, Tag, UserProfile, Follow
from .forms import RegisterForm, PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q


def home(request):
    query = request.GET.get('q', '').strip()
    tags = Tag.objects.all()

    # Trang landing chào mừng có video khi mới vào web
    if not request.user.is_authenticated and not query and not request.GET.get('feed'):
        return render(request, 'devBlog/landing.html')

    if query:
        posts = Post.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__name__icontains=query) |
            Q(author__username__icontains=query)
        ).distinct().order_by('-created_at')
    else:
        posts = Post.objects.all().order_by('-created_at')

    return render(request, 'devBlog/home.html', {
        'posts': posts,
        'tags': tags,
        'query': query
    })


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    comments = post.comments.all().order_by('-created_at')

    if request.method == 'POST':

        if not request.user.is_authenticated:
            return redirect('login')

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
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)

    next_url = request.META.get('HTTP_REFERER')
    if next_url:
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
        form = PostForm(request.POST, request.FILES, instance=post)

        if form.is_valid():
            form.save()
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
        post.delete()
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
    posts = Post.objects.filter(
        author=profile_user
    ).order_by('-created_at')

    total_likes_received = sum(post.total_likes() for post in posts)
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
def toggle_follow(request, username):
    target_user = get_object_or_404(User, username=username)

    if target_user == request.user:
        return redirect('user_profile', username=username)

    follow_obj = Follow.objects.filter(
        follower=request.user, following=target_user
    )
    if follow_obj.exists():
        follow_obj.delete()
    else:
        Follow.objects.create(follower=request.user, following=target_user)

    return redirect('user_profile', username=username)


@login_required
def my_posts(request):
    posts = Post.objects.filter(
        author=request.user
    ).order_by('-created_at')

    return render(request, 'devBlog/my_posts.html', {
        'posts': posts
    })


@login_required
def posts_by_tag(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    posts = Post.objects.filter(tags=tag).order_by('-created_at')
    tags = Tag.objects.all()

    return render(request, 'devBlog/home.html', {
        'posts': posts,
        'tags': tags,
        'current_tag': tag
    })