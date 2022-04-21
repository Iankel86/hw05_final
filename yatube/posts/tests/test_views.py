from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()

POSTS_QUANTITY = 10
SECOND_POST_PAGE_COUNT = POSTS_QUANTITY - settings.NUMBER_POST + 1


class PostPagesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тест',
            slug='12',
        )
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group
        )
        self.form_data = {
            'text': self.post.text,
            'group': self.group.id,
        }
        self.new_post = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )

    def test_uses_correct_template(self):
        """URL использует корректные шаблоны HTML."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            self.user.username}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            self.post.pk}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            self.post.pk}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_context_index(self):
        """Проверка контекста домашней страницы index"""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context.get('page_obj')[0]
        self.assertEqual(first_object, self.post, "что то пошло не так")
        self.assertEqual(first_object.text, self.post.text, 'Ошибка Text')
        self.assertEqual(
            first_object.author, self.post.author, 'Ошибка Author'
        )

    def test_group_contains_list_of_posts(self):
        """group_list содержит посты, отфильтрованные по группе."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            ))
        for post_example in response.context.get('page_obj'):
            with self.subTest():
                self.assertIsInstance(post_example, Post)
                self.assertEqual(post_example.group, self.group)
        self.assertEqual(response.context['group'], self.group)

    def test_context_post_create(self):
        """Проверка контекста - post_create."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_context_post_edit(self):
        """Проверка контекста - post_edit."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id},
            ))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        test_is_edit = response.context['is_edit']
        self.assertTrue(test_is_edit)

    def test_profile_contains_list_of_posts(self):
        """profile содержит посты, отфильтрованные по пользователю."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ))

        for post_example in response.context.get('page_obj'):
            with self.subTest():
                self.assertIsInstance(post_example, Post)
                self.assertEqual(post_example.author, self.user)
        self.assertEqual(response.context['author'], self.user)


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовая группа',
        )
        cls.post = settings.SAMPLING + settings.NUMBER_POST
        for cls.post in range(settings.SAMPLING + settings.NUMBER_POST):
            cls.post = Post.objects.create(
                text='Тестовый текст',
                author=cls.user,
                group=cls.group
            )

    def test_first_page_contains(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         settings.SAMPLING)

    def test_group_first_page_contains(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={
                'slug': PaginatorTests.group.slug
            })
        )
        self.assertEqual(len(response.context['page_obj']),
                         settings.SAMPLING)

    def test_group_second_page_contains(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={
                'slug': PaginatorTests.group.slug
            }) + '?page=2'
        )
        self.assertEqual(len(
            response.context['page_obj']), settings.NUMBER_POST)

    def test_profile_first_page_contains(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={
                'username': PaginatorTests.user.username,
            })
        )
        self.assertEqual(len(response.context['page_obj']),
                         settings.SAMPLING)

    def test_profile_second_page_contains(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={
                'username': PaginatorTests.user.username,
            }) + '?page=2'
        )
        self.assertEqual(len(
            response.context['page_obj']), settings.NUMBER_POST)
