from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.select_related('group').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    
    return render(
        request,
        "index.html",
        {"page": page, "paginator": paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_posts = group.posts.all()
    paginator = Paginator(group_posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(
        request,
        "group.html",
        {"group": group, "page": page, "paginator": paginator}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'new.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.all()
    posts_count = author.posts.count()
    paginator = Paginator(author_posts, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = request.user.is_authenticated and Follow.objects.filter(user=request.user, author=author).exists()
    return render(
        request,
        'profile.html',
        {'author': author,
        'page': page,
        'count': posts_count,
        'paginator': paginator,
        'following': following}
    )
 
 
def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    posts_count = author.posts.count()
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm()
    comments = Comment.objects.filter(post=post_id)
    return render(
        request,
        'post.html',
        {'author': author, 'count': posts_count, 'post': post, 'form': form, 'comments': comments}
    )


@login_required
def post_edit(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author__username=username)
    posts_count = author.posts.count()
    if request.user != author:
        return render(
        request,
        'post.html',
        {'author': author, 'count': posts_count, 'post': post}
    )
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'new.html', {'form': form, 'post': post, 'edit_mode': True})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = Comment.objects.filter(post=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'post.html', {'form': form, 'post': post, 'comments': comments})


def page_not_found(request, exception):
    return render(
        request, 
        "misc/404.html", 
        {"path": request.path}, 
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    
    return render(
        request,
        "follow.html",
        {"page": page, "paginator": paginator}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        follow_link = Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow_link = Follow.objects.get(user=request.user, author=author)
    if follow_link:
        follow_link.delete()
    return redirect('profile', username)
