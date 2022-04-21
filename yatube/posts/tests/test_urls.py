from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # создали автора
        cls.author = User.objects.create_user(username='test_author')
        # создали юзера
        cls.user = User.objects.create_user(username='test_user')
        # создаем группу
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        # создаем пост, где юзер стал автором,
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_author = Client()
        # мы создали авторизованного автора (зарегистрировали)
        self.authorized_author = Client()
        # мы залогинились автором
        self.authorized_author.force_login(self.author)
        self.authorized_user = Client()
        # мы залогинились юзером
        self.authorized_user.force_login(self.user)

    def test_url(self):
        """Проверка URL по запросу."""
        open_urls_names = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.author.username}/',
            f'/posts/{self.post.pk}/',
        ]
        for address in open_urls_names:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_user.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_author.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_grouppage(self):
        'Проверка страниц групп для не авторизированных'
        response = self.guest_author.get(reverse('posts:group_list',
                                         kwargs={'slug': f'{self.group.slug}'})
                                         )
        self.assertEqual(response.status_code, HTTPStatus.OK,
                         'ОШИБКА: страница /group/<slug> работает не верно!')

    def test_correct_template(self):
        """URL-адрес использует соотв. шаблон."""
        url_templates_names = {
            '/': 'posts/index.html',
            f'/profile/{self.author.username}/':
                'posts/profile.html',
            f'/posts/{self.post.pk}/edit/':
                'posts/create_post.html',
            f'/posts/{self.post.pk}/':
                'posts/post_detail.html',
            f'/group/{self.group.slug}/':
                'posts/group_list.html',
            '/create/': 'posts/create_post.html',
        }
        for reverse_name, template in url_templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_redirect(self):
        """Проверяем редиректы для неавтор. пользователя."""
        urls_names = [
            '/create/',
            f'/posts/{self.post.pk}/edit/',
        ]
        for address in urls_names:
            with self.subTest(address=address):
                response = self.client.get(address, follow=True)
                self.assertRedirects(
                    response, (
                        f'/auth/login/?next={address}'
                    )
                )
        response = self.authorized_user.get(
            f'/posts/{self.post.pk}/edit/', follow=True
        )
        self.assertRedirects(
            response, (
                f'/posts/{self.post.pk}/'
            )
        )

    def test_404(self):
        """Проверка несуществующей страницы."""
        response = self.client.get('/404/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_homepage(self):
        'Проверка домашней страницы для не авторизированных'
        response = self.guest_author.get(reverse('posts:index'))
        self.assertEqual(response.status_code, HTTPStatus.OK,
                         'ОШИБКА: Домашняя страница работает не верно!')

    def test_profileppage(self):
        'Проверка страницы профиля для не авторизированных'
        response = self.guest_author.get(reverse('posts:profile',
                                         kwargs={'username':
                                                 f'{self.user.username}'})
                                         )
        self.assertEqual(response.status_code, HTTPStatus.OK,
                         'ОШИБКА: страница профилей не работает!')

    def test_post_page(self):
        'Проверка страницы просмотра постов для не авторизированных'
        response = self.guest_author.get(reverse('posts:post_detail',
                                         kwargs={'post_id': f'{self.post.id}'})
                                         )
        self.assertEqual(response.status_code, HTTPStatus.OK,
                         'ОШИБКА: Страница просмотра постов не работает!')

    def test_post_edit_page(self):
        'Проверка страницы редактирования постов для автора'
        response = self.authorized_author.get(reverse('posts:post_edit',
                                              kwargs={'post_id':
                                                      f'{self.post.id}'})
                                              )
        self.assertEqual(response.status_code, HTTPStatus.OK,
                         'ОШИБКА: Редактирует не автор!')

    # def test_comment_guest(self):
    #     """Проверяем, что комментировать может авторизованный мользователь
    #        А гостя перенаправляем на авторизацию"""
    #     response_no_auth = self.guest_author.get(
    #         f'/posts/{self.post.id}/comment/')
    #     response_auth = self.authorized_author.get(
    #         f'/posts/{self.post.id}/comment/')
    #     self.assertEqual(
    #         response_no_auth.status_code, HTTPStatus.FOUND.value)
    #     self.assertEqual(response_auth.status_code, HTTPStatus.FOUND.value)
    #     self.assertRedirects(
    #         response_no_auth,
    #         f'/auth/login/?next=/posts/{self.post.id}/comment/')
