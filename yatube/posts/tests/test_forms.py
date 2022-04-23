from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='testgroup',
            description='Тест описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.form_data = {
            'text': cls.post.text,
            'group': cls.group.id,
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTest.user)

    def test_create_post(self):
        post_count = Post.objects.count()
        context = {
            'text': 'Текстовый текст',
            'group': PostFormTest.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=context,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={
                                         'username': PostFormTest.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.latest('id').text, context['text'])
        self.assertEqual(Post.objects.latest('id').group, PostFormTest.group)

    def test_post_edit(self):
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[self.post.pk]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=[self.post.id])
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=self.group.id,
                id=self.post.id,
                author=PostFormTest.user,
            ).exists()
        )

    def test_anonim_client_create_post(self):
        post_count = Post.objects.count()
        response = self.client.post(
            reverse('posts:post_create'),
            data=PostFormTest.form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response,
                             reverse('users:login') + '?next=' + reverse(
                                 'posts:post_create'))
        self.assertEqual(Post.objects.count(), post_count)

    def test_anonim_edit_post(self):
        context = {
            'text': 'Попытка изменить пост',
            'group': self.group.id,
        }
        response = self.client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': PostFormTest.post.id}),
            data=context,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse(
            'posts:post_edit', kwargs={'post_id': PostFormTest.post.id}))
        edited_post = Post.objects.get(id=PostFormTest.post.id)
        self.assertNotEqual(edited_post.text, context['text'])
        self.assertNotEqual(edited_post.group, context['group'])

    def test_create_post_without_group(self):
        post_count = Post.objects.count()
        context = {
            'text': 'Текстовый текст',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=context,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={
                                         'username': PostFormTest.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.latest('id').text, context['text'])

    def test_edit_post_not_author(self):
        user_editor = User.objects.create(
            username='editor_not_owner_post'
        )
        authorized_editor = Client()
        authorized_editor.force_login(user_editor)

        form_data = {
            'text': 'Отредактированный текст поста',
        }
        response = authorized_editor.post(
            reverse('posts:post_edit', args=[self.post.pk]),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(id=self.post.pk)
        self.assertEqual(post.text, self.post.text)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=[self.post.id])
        )

    def test_comment_posts_guost(self):
        'Проверка создания комментария не авторизированного'
        author = self.user.id
        post = self.post.id
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Коммент',
            'author_id': author,
            'post_id': post
        }
        response = self.guest_client.post(reverse('posts:add_comment',
                                          kwargs={
                                                  'post_id': self.post.id}),
                                          data=form_data,
                                          follow=True)
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('users:login')
                             + f'?next=/posts/{self.post.id}/comment/')
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Comment.objects.count(), comment_count,
                         'Ошибка:Число постов увеличелось..')
