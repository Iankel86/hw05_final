from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

from yatube.settings import SYMBOLS_POST

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(
            self.group.title,
            str(self.group),
            'Названия групп не совпадают')
        self.assertEqual(
            self.post.text[:SYMBOLS_POST],
            str(self.post),
            'Текст поста не совпадает')
