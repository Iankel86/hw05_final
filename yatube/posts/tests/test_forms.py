import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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
        cls.POST_PAGE = reverse('posts:post_detail', args=[cls.post.pk])
        cls.POST_EDIT = reverse('posts:post_edit', args=[cls.post.pk])
        cls.COMMENT = reverse('posts:add_comment', args=[cls.post.pk])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTest.user)

    def test_create_comment(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Создаем коммент',
        }
        response = self.authorized_client.post(
            PostFormTest.COMMENT,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.POST_PAGE)
        self.assertEqual(Comment.objects.count(), comments_count + 1)

        self.assertTrue(
            Comment.objects.filter(
                text='Создаем коммент',
            ).last()
        )

    def test_create_post(self):
        post_count = Post.objects.count()
        upload = SimpleUploadedFile(
            name='small_for_create.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        context = {
            'text': 'Текстовый текст',
            'group': PostFormTest.group.id,
            'image': upload,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=context,
            follow=True
        )
        tested_post = Post.objects.first()
        self.assertEqual(tested_post.group.id, context['group'])
        self.assertEqual(tested_post.text, context['text'])
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={
                                         'username': PostFormTest.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.latest('id').text, context['text'])
        self.assertTrue(
            Post.objects.filter(
                text='Текстовый текст',
                image='posts/small_for_create.gif'
            ).first()
        )
        # self.assertTrue(
        #     Group.objects.filter(
        #         title='Тестовая группа',
        #         slug='test-slug',
        #         description='Тестовое описание',
        #     ).first()
        # )

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
