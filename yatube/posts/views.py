from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import get_paginator


def index(request):
    posts = Post.objects.all()
    page_obj, total_count = get_paginator(Post.objects.all(), request)
    context = {
        'posts': posts,
        'page_obj': page_obj,
        'total_count': total_count,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    page_obj, total_count = get_paginator(group.posts.all(), request)
    context = {
        'group': group,
        'total_count': total_count,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    page_obj, posts_amount = get_paginator(author.posts.all(), request)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(
            user__username=request.user, author__username=username).exists())
    context = {
        'author': author,
        'posts_amount': posts_amount,
        'following': following,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author_posts = post.author.posts.count()
    num_author_posts = Post.objects.filter(author=author_posts).count()
    comment_form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'author_posts': author_posts,
        'posts_count': num_author_posts,
        'form': comment_form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    tamplate = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, tamplate, {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    template = 'posts/create_post.html'
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post.pk)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.pk)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Посты авторов,на которых подписан текущий пользователь, не более 10"""
    user = request.user
    posts = Post.objects.filter(author__following__user=user)
    paginator = get_paginator(posts, request)
    template = 'posts/follow.html'
    context = {
        'page_obj': paginator,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    """Функция отписаться от некого автора"""
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username)
