import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class CreateEditTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.post_author = User.objects.create_user(username='writer')
        cls.non_author = User.objects.create_user(username='reader')

        cls.test_dict = {
            'group_title': 'Test Group',
            'group_slug': 'test-group',
            'group_description': 'group for testing forms',
            'pc_text': 'Created test post',
            'pei_text': 'Original unedited post',
            'pef_text': 'Edited post',
            'post_edit_id': None,
            'bad_text': 'I should not be able to do this'
        }

        cls.group = Group.objects.create(
            title='Test Group',
            slug='test-group',
            description='group for testing forms',
        )

    def setUp(self):
        self.post_author = Client()
        self.post_author.force_login(CreateEditTest.post_author)
        self.non_author = Client()
        self.non_author.force_login(CreateEditTest.non_author)

        post = Post.objects.create(
            text=CreateEditTest.test_dict['pei_text'],
            author=CreateEditTest.post_author,
        )
        CreateEditTest.test_dict['post_edit_id'] = post.id

    def test_post_creation(self):
        post_count = Post.objects.count()
        form_data = {
            'text': CreateEditTest.test_dict['pc_text']
        }
        self.post_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post_query = Post.objects.order_by('pk')
        last_post = post_query[len(post_query) - 1]
        post_exists = Post.objects.filter(
            id=last_post.id,
            text=CreateEditTest.test_dict['pc_text'],
            author=CreateEditTest.post_author,
        ).exists()
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(post_exists)

    def test_post_edition(self):
        post_count = Post.objects.count()

        form_edit_data = {
            'text': CreateEditTest.test_dict['pef_text']
        }
        self.post_author.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': CreateEditTest.test_dict['post_edit_id']}
            ),
            data=form_edit_data,
            follow=True
        )

        post_exists = Post.objects.filter(
            text=CreateEditTest.test_dict['pef_text'],
            id=CreateEditTest.test_dict['post_edit_id'],
            author=CreateEditTest.post_author,
        ).exists()
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(post_exists)

    def test_post_creation_by_anonymous(self):
        post_count = Post.objects.count()
        form_data = {
            'text': CreateEditTest.test_dict['bad_text'],
            'group': CreateEditTest.group,
        }
        self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            Post.objects.count(), post_count,
            'Анонимный пользователь смог добавить пост'
        )

    def test_post_edition_by_anonymous_non_author(self):
        post_count = Post.objects.count()

        form_edit_data = {
            'text': CreateEditTest.test_dict['bad_text'],
            'group': CreateEditTest.group,
        }

        clients_list = [self.client, self.non_author]

        def inner_post_edit_tests(client):
            client.post(
                reverse(
                    'posts:post_edit',
                    kwargs={
                        'post_id': CreateEditTest.test_dict['post_edit_id']
                    }
                ),
                data=form_edit_data,
                follow=True
            )

            post = Post.objects.get(
                id=CreateEditTest.test_dict['post_edit_id']
            )
            self.assertEqual(
                post.text, CreateEditTest.test_dict['pei_text']
            )
            self.assertIsNone(post.group)
            self.assertEqual(
                post.author, CreateEditTest.post_author
            )
            self.assertEqual(
                post_count, Post.objects.count()
            )

        for client in clients_list:
            with self.subTest(client=client):
                inner_post_edit_tests(client)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageFormTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.img_uploader_usrnm = 'img_uploader'
        cls.img_uploader = User.objects.create(
            username=cls.img_uploader_usrnm
        )
        cls.test_dict = {
            'small_gif_b': (
                b'\x47\x49\x46\x38\x39\x61\x02\x00'
                b'\x01\x00\x80\x00\x00\x00\x00\x00'
                b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                b'\x0A\x00\x3B'
            ),
            'gif_name': 'small.gif',
            'gif_address': 'posts/small.gif',
            'content_type': 'image/gif',
            'post_text': 'Тестовый текст',
            'reverse_for_post_create': reverse(
                'posts:post_create'
            )
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client.force_login(ImageFormTest.img_uploader)

    def test_upload_gif_to_db(self):
        test_dict = ImageFormTest.test_dict

        posts_count = Post.objects.count()

        small_gif = test_dict['small_gif_b']

        uploaded_img = SimpleUploadedFile(
            name=test_dict['gif_name'],
            content=small_gif,
            content_type=test_dict['content_type']
        )
        form_data = {
            'text': test_dict['post_text'],
            'image': uploaded_img
        }
        self.client.post(
            test_dict['reverse_for_post_create'],
            data=form_data
        )

        post_query = Post.objects.order_by('pk')
        last_post = post_query[len(post_query) - 1]
        post_exists = Post.objects.filter(
            id=last_post.id,
            text=test_dict['post_text'],
            image=test_dict['gif_address'],
            author=ImageFormTest.img_uploader
        ).exists()

        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            post_exists
        )


class CommentsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.post_author = User.objects.create(
            username='author'
        )
        cls.commenter = User.objects.create(
            username='commenter'
        )
        cls.post_with_comment = Post.objects.create(
            text='Тестовый текст',
            author=cls.post_author
        )

    def setUp(self):
        self.commenter = Client()
        self.commenter.force_login(CommentsTest.commenter)
        self.reverse_name = reverse(
            'posts:add_comment',
            kwargs={
                'post_id': CommentsTest.post_with_comment.id
            },
        )
        self.cm_text = 'Тестовый комментарий'
        self.anon_text = 'Анонимный комментарий'

    def test_comment_creation(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': self.cm_text
        }
        self.commenter.post(
            self.reverse_name,
            data=form_data,
            follow=True
        )
        comment_query = Comment.objects.order_by('id')
        last_comment = comment_query[len(comment_query) - 1]
        comment_exists = Comment.objects.filter(
            post=CommentsTest.post_with_comment,
            id=last_comment.id,
            text=self.cm_text
        ).exists()
        self.assertEqual(
            Comment.objects.count(), comment_count + 1,
            'Нового комментария нет в базе'
        )
        self.assertTrue(comment_exists)

    def test_comment_creation_by_anon(self):

        comment_count = Comment.objects.count()
        form_data = {
            'text': self.anon_text
        }
        self.client.post(
            self.reverse_name,
            data=form_data,
            follow=True
        )
        self.assertEqual(
            Comment.objects.count(), comment_count,
            'Комментарий анонима добавился в базу'
        )
