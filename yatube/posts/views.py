from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator

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
    following = Follow.objects.filter(
        user__username=request.user, author__username=username).all()
    context = {
        # Все посты пользователя в profile.html
        'author': author,
        # Всего постов автора в profile.html
        'posts_amount': posts_amount,
        'following': following,
        # Список всех постов отсорт по 10 шт и привяз. к панинатору
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
    """Посты авторов,на которых подписан текущий пользователь"""
    user = request.user
    posts = Post.objects.filter(author__following__user=user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/follow.html', {'page': page,
                                                 'paginator': paginator})


@login_required
def profile_follow(request, username):
    """Подписка на интересного автора"""
    user = request.user
    author = get_object_or_404(User, username=username)
    now_follower = Follow.objects.filter(user=user, author=author).exists()
    if user != author and not now_follower:
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Функция отписаться от некого автора"""
    user = request.user
    author = get_object_or_404(User, username=username)
    now_follower = Follow.objects.filter(user=user, author=author).exists()
    if now_follower:
        follow = Follow.objects.get(user=user, author=author)
        follow.delete()
    return redirect('posts:profile', username=username)


# def paginator_view(request, post_list):
#     posts = Post.objects.filter(author__following__user=user)
#     paginator = Paginator(posts, 10)
#     page_number = request.GET.get("page")
#     return paginator.get_page(page_number)


@login_required
def follow_index(request):
    user = request.user
    posts = Post.objects.filter(author__following__user=user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'posts/follow.html', {'page_obj': page_obj})

# def test_delete_image(self):
#         """Проверяем, что картинку можно удалить из существующего поста"""
#         post_count = Post.objects.count()
#         form_data = {
#             'text': self.post.text,
#             'group': self.post.group.id,
#             'image-clear': 'on'
#         }
#         response = self.author_client.post(
#             reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
#             data=form_data
#         )

#         self.assertRedirects(
#             response, reverse(
#                 'posts:post_detail', kwargs={'post_id': self.post.id}
#             )
#         )
#         self.assertEqual(Post.objects.count(), post_count,
#                          f'Создан новый пост')
#         self.post.refresh_from_db()
#         self.assertEqual(self.post.image.name, '')
