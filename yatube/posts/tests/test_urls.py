from http import HTTPStatus as hs

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.urls_dict = {
            'index': '/',
            'about-author': '/about/author/',
            'about-tech': '/about/tech/',
        }

    def test_static_pages_availability(self):
        for address in self.urls_dict.values():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, hs.OK.value)


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Создаем записи в БД под тестовых юзеров
        cls.non_author = User.objects.create_user(username='reader')
        cls.post_author = User.objects.create_user(username='writer')

        cls.test_dict = {
            'group_title': 'Doki-Doki',
            'group_slug': 'doki-doki',
            'group_description': 'Literature Club',
            'post_text': 'I\'m writing for my favourite literature club',
            'post_id': '',
            'profile': 'reader',
        }

        cls.group = Group.objects.create(
            title=cls.test_dict['group_title'],
            slug=cls.test_dict['group_slug'],
            description=cls.test_dict['group_description'],
        )

        post = Post.objects.create(
            text=cls.test_dict['post_text'],
            author=cls.post_author,
            group=cls.group,
        )
        cls.test_dict['post_id'] = str(post.id)

        cls.urls_templates_anon = {
            '/': 'posts/index.html',
            '/group/{}/'.format(cls.test_dict['group_slug']):
                'posts/group_list.html',
            '/profile/{}/'.format(cls.test_dict['profile']):
                'posts/profile.html',
            '/posts/{}/'.format(cls.test_dict['post_id']):
                'posts/post_detail.html',
        }

        cls.urls_templates_author = {
            '/create/': 'posts/create_post.html',
            '/posts/{}/edit/'.format(cls.test_dict['post_id']):
                'posts/create_post.html',
        }

        cls.urls_templates_nauthor = {
            '/create/': 'posts/create_post.html',
        }

    def setUp(self):
        # Создаем и логиним тестовых юзеров
        self.non_author = Client()
        self.non_author.force_login(PostsURLTests.non_author)
        self.post_author = Client()
        self.post_author.force_login(PostsURLTests.post_author)

    def test_pages_access_for_anonymous_user(self):
        for address, template in PostsURLTests.urls_templates_anon.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(
                    response.status_code, hs.OK.value,
                    f'Получен неверный код для адреса: {address}'
                )
                self.assertTemplateUsed(response, template)

    def test_pages_access_for_author(self):
        for address, template in PostsURLTests.urls_templates_author.items():
            with self.subTest(address=address):
                response = self.post_author.get(address)
                self.assertEqual(
                    response.status_code, hs.OK.value,
                    f'Получен неверный код для адреса: {address}'
                )
                self.assertTemplateUsed(response, template)

    def test_pages_access_for_non_author(self):
        for address, template in PostsURLTests.urls_templates_nauthor.items():
            with self.subTest(address=address):
                response = self.non_author.get(address)
                self.assertEqual(
                    response.status_code, hs.OK.value,
                    f'Получен неверный код для адреса: {address}'
                )
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, hs.NOT_FOUND.value)
