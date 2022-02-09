import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.query import EmptyQuerySet
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post
from yatube.settings import POSTS_BY_PAGE

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.test_dict = {
            'group_title': 'Test Group',
            'group_slug': 'test-group',
            'group_description': 'group for testing views',
            'author_usrnm': 'writer',
        }

        cls.post_author = User.objects.create_user(
            username=cls.test_dict['author_usrnm']
        )

        cls.group1 = Group.objects.create(
            title=cls.test_dict['group_title'],
            slug=cls.test_dict['group_slug'],
            description=cls.test_dict['group_description'],
        )

        cls.paginator_test_number = POSTS_BY_PAGE + POSTS_BY_PAGE // 2

        for i in range(1, PostViewsTests.paginator_test_number + 1):
            Post.objects.create(
                text=f'Post {i}',
                author=cls.post_author,
                group=cls.group1,
            )

    def setUp(self):
        self.test_post_id = 1
        self.post_author = Client()
        self.post_author.force_login(PostViewsTests.post_author)
        self.pages_names_templates_dict = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': PostViewsTests.test_dict['group_slug']
                }
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={
                    'username': PostViewsTests.test_dict['author_usrnm']
                }
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.test_post_id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.test_post_id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        self.context_paginator_tests_list = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': PostViewsTests.test_dict['group_slug']
                }
            ),
            reverse(
                'posts:profile',
                kwargs={
                    'username': PostViewsTests.test_dict['author_usrnm']
                }
            ),
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.test_post_id}
            ),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.test_post_id}
            ),
            reverse('posts:post_create'),
        ]

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        for reverse_name, template in self.pages_names_templates_dict.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.post_author.get(reverse_name)
                self.assertTemplateUsed(
                    response, template,
                    f'Проблемы с view-функцией {reverse_name}'
                )

    def test_paginator(self):
        '''
        Паджинатор тестируется в первых трех записях списка
        context_paginator_tests_list.
        Проходимся по первым трем записям этого списка для теста паджинатора.
        '''
        i = 1
        for reverse_name in self.context_paginator_tests_list:
            if i < 4:
                response = self.post_author.get(reverse_name)
                self.assertIsNotNone(
                    response.context.get('page_obj'),
                    f'Страница {reverse_name} не получила постов'
                )
                response_pg2 = self.post_author.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']), POSTS_BY_PAGE,
                    'Что-то не так с 1 страницей '
                    + f'паджинатора в {reverse_name}'
                )
                self.assertEqual(
                    len(response_pg2.context['page_obj']), POSTS_BY_PAGE / 2,
                    'Что-то не так со 2 страницей '
                    + f'паджинатора в {reverse_name}'
                )
            else:
                break
            i += 1

    def test_context_index(self):
        response = self.post_author.get(reverse('posts:index'))
        response_pg2 = self.post_author.get(reverse('posts:index') + '?page=2')
        page1_obj = response.context.get('page_obj')
        page2_obj = response_pg2.context.get('page_obj')

        def inner_for_tests(post):
            self.assertIn('Post ', post.text)
            self.assertEqual(post.author, PostViewsTests.post_author)
            self.assertEqual(post.group, PostViewsTests.group1)

        i = 1
        for post in page1_obj:
            inner_for_tests(post)
            i += 1

        i = POSTS_BY_PAGE + 1
        for post in page2_obj:
            inner_for_tests(post)
            i += 1

    def test_context_group(self):
        reverse_name = reverse(
            'posts:group_list',
            kwargs={
                'slug': PostViewsTests.test_dict['group_slug']
            }
        )
        response = self.post_author.get(reverse_name)
        response_pg2 = self.post_author.get(reverse_name + '?page=2')
        page1_obj = response.context.get('page_obj')
        page2_obj = response_pg2.context.get('page_obj')

        i = 1
        for post in page1_obj:
            self.assertEqual(post.group, PostViewsTests.group1)
            i += 1

        i = POSTS_BY_PAGE + 1
        for post in page2_obj:
            self.assertEqual(post.group, PostViewsTests.group1)
            i += 1

    def test_context_profile(self):
        reverse_name = reverse(
            'posts:profile',
            kwargs={
                'username': PostViewsTests.test_dict['author_usrnm']
            }
        )
        response = self.post_author.get(reverse_name)
        response_pg2 = self.post_author.get(reverse_name + '?page=2')
        page1_obj = response.context.get('page_obj')
        page2_obj = response_pg2.context.get('page_obj')

        i = 1
        for post in page1_obj:
            self.assertEqual(post.author, PostViewsTests.post_author)
            i += 1

        i = POSTS_BY_PAGE + 1
        for post in page2_obj:
            self.assertEqual(post.author, PostViewsTests.post_author)
            i += 1

    def test_context_post_detail(self):
        reverse_name = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.test_post_id}
        )
        response = self.post_author.get(reverse_name)
        post = response.context.get('post')
        self.assertEqual(post.text, 'Post 1')

    def test_context_post_edit(self):
        reverse_name = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.test_post_id}
        )
        response = self.post_author.get(reverse_name)
        form = response.context.get('form')
        self.assertIsNotNone(form)

    def test_context_post_create(self):
        reverse_name = reverse('posts:post_create')
        response = self.post_author.get(reverse_name)
        form = response.context.get('form')
        self.assertIsNotNone(form)


class PostAppearanceTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.post_author = User.objects.create_user(username='writer')

        cls.group1 = Group.objects.create(
            title='Right Group',
            slug='right-group',
            description='post should be here',
        )

        cls.group2 = Group.objects.create(
            title='Right Group',
            slug='wrong-group',
            description='post shouldn\'t be here',
        )

        Post.objects.create(
            text='Post',
            author=cls.post_author,
            group=cls.group1,
        )

    def setUp(self):
        self.post_author = Client()
        self.post_author.force_login(PostAppearanceTest.post_author)
        self.post_appearance_dict = {
            'index': reverse('posts:index'),
            'right': reverse(
                'posts:group_list',
                kwargs={'slug': 'right-group'}
            ),
            'wrong': reverse(
                'posts:group_list',
                kwargs={'slug': 'wrong-group'}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': 'writer'}
            ),
        }

    def test_post_appearance(self):
        for name in self.post_appearance_dict:
            response = self.post_author.get(self.post_appearance_dict[name])
            page_obj = response.context.get('page_obj')
            if name != 'wrong':
                self.assertNotIsInstance(page_obj.object_list, EmptyQuerySet)
            else:
                self.assertIsInstance(page_obj.object_list, EmptyQuerySet)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageInContextTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.img_uploader_usrnm = 'img_uploader'
        cls.img_uploader = User.objects.create(
            username=cls.img_uploader_usrnm
        )

        cls.group = Group.objects.create(
            title='Test Group',
            slug='test_group',
            description='Test group description',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client.force_login(ImageInContextTest.img_uploader)

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded_img = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.img_post = Post.objects.create(
            author=ImageInContextTest.img_uploader,
            text='Тестовый текст',
            group=ImageInContextTest.group,
            image=uploaded_img
        )

        self.pages_to_test = {
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': 'test_group'
                }
            ),
            reverse(
                'posts:profile',
                kwargs={
                    'username': ImageInContextTest.img_uploader_usrnm
                }
            )
        }
        self.reverse_for_pd = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.img_post.id}
        )

    def test_image_in_context_for_paginated_pages(self):
        for reverse_name in self.pages_to_test:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                page_obj = response.context.get('page_obj')
                images = []
                for post in page_obj:
                    images.append(post.image)
                for img in images:
                    self.assertIsNotNone(
                        img,
                        'Картинки нет в словаре "context"'
                    )

    def test_image_in_context_for_pd(self):
        response = self.client.get(self.reverse_for_pd)
        post = response.context.get('post')
        self.assertIsNotNone(
            post.image,
            'Картинки нет в словаре "context" на стр. поста'
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
        self.reverse_name_add = reverse(
            'posts:add_comment',
            kwargs={
                'post_id': CommentsTest.post_with_comment.id
            },
        )
        self.reverse_name_check = reverse(
            'posts:post_detail',
            kwargs={
                'post_id': CommentsTest.post_with_comment.id
            }
        )
        self.cm_text = 'Тестовый комментарий'

    def test_comment_in_context(self):
        form_data = {
            'text': self.cm_text
        }
        self.commenter.post(
            self.reverse_name_add,
            data=form_data,
        )
        response = self.client.get(self.reverse_name_check)
        comments = response.context.get('comments')
        self.assertTrue(len(comments) > 0)


class CacheTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.post_author = User.objects.create(
            username='author'
        )
        cls.post_in_cache = Post.objects.create(
            text='Тестовый текст',
            author=cls.post_author
        )
    
    def setUp(self):
        cache.clear()

    def test_cache(self):
        response1 = self.client.get(
            reverse('posts:index')
        )
        content1 = response1.content
        context1 = response1.context
        page_obj1 = context1.get('page_obj')
        self.assertTrue(
            len(page_obj1) > 0,
            'Поста нет изначально'
        )
        self.assertEqual(
            page_obj1[0].id, CacheTest.post_in_cache.id
        )

        Post.objects.filter(id=CacheTest.post_in_cache.id).delete()

        response2 = self.client.get(
            reverse('posts:index')
        )
        content2 = response2.content
        self.assertEqual(
            content1, content2,
            'Количество постов не равно тому, которое было до удаления'
        )

        cache.clear()

        response3 = self.client.get(
            reverse('posts:index')
        )
        content3 = response3.content
        self.assertNotEqual(
            content1,
            content3,
            'Пост остался на странице после очистки кэша'
        )


class SubscriptionTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create(
            username='author'
        )
        cls.follower = User.objects.create(
            username='follower'
        )
        cls.non_follower = User.objects.create(
            username='non follower'
        )

        cls.reverse_follow = reverse(
            'posts:profile_follow',
            kwargs={
                'username': cls.author.username
            }
        )

        cls.reverse_unfollow = reverse(
            'posts:profile_unfollow',
            kwargs={
                'username': cls.author.username
            }
        )

        cls.reverse_follow_index = reverse(
            'posts:follow_index'
        )

    def setUp(self):
        self.author = Client()
        self.author.force_login(SubscriptionTest.author)
        self.follower = Client()
        self.follower.force_login(SubscriptionTest.follower)
        self.non_follower = Client()
        self.non_follower.force_login(SubscriptionTest.non_follower)

        self.post = Post.objects.create(
            author=SubscriptionTest.author,
            text='Тестовый пост'
        )

    def test_subscription_unsubscription(self):
        follow_count = Follow.objects.count()
        self.follower.get(SubscriptionTest.reverse_follow)
        subscription_exists = Follow.objects.filter(
            user=SubscriptionTest.follower,
            author=SubscriptionTest.author
        )
        self.assertTrue(
            subscription_exists,
            'Подписка не оформилась'
        )

        self.follower.get(SubscriptionTest.reverse_unfollow)
        self.assertEqual(
            follow_count,
            Follow.objects.count(),
            'Подписка не удалилась'
        )

    def test_subscription_context(self):
        self.follower.get(SubscriptionTest.reverse_follow)

        response_follower = self.follower.get(
            SubscriptionTest.reverse_follow_index
        )
        response_non_follower = self.non_follower.get(
            SubscriptionTest.reverse_follow_index
        )
        self.assertNotEqual(
            len(response_follower.context['page_obj']),
            len(response_non_follower.context['page_obj']),
            'Подписчик и неподписчик получили одинаковое '
            'кол-во постов в ленту'
        )
