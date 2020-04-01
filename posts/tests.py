from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from .models import User, Post, Group, Follow


class PostTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
                username='yandex', email='praktikum@yandex.ru',
                password='12345')
        self.following_user = User.objects.create_user(
                username='author', email='story@yandex.ru',
                password='12345')
        self.password = '12345'
        self.post = Post.objects.create(text='This is test post for tests',
                                        author=self.user)
        self.group = Group.objects.create(title='Test Group', slug='testsslug',
                                          description='Test group!')
        self.group_post = Post.objects.create(
                                text='This is test post in group',
                                author=self.user, group=self.group)

    def test_signup_user(self):
        new_user = {'first_name': 'Test',
                    'last_name': 'Mr.Test',
                    'username': 'test007',
                    'email': 'test@yandex.ru',
                    'password1': 'J5x-7wC-n7H-Tbs',
                    'password2': 'J5x-7wC-n7H-Tbs'}
        responce_registration = self.client.post(reverse('signup'), new_user)
        self.assertEqual(responce_registration.status_code, 302,
                         msg='User not created')
        responce_profile_page = self.client.get(reverse('profile',
                                                        args=['test007']))
        self.assertEqual(responce_profile_page.status_code, 200,
                         msg="Profile page doesn't exist")

    def test_new_post(self):
        responce = self.client.get(reverse('new_post'), follow=True)
        self.assertEqual(responce.resolver_match.url_name, 'login',
                         msg="Unauthorized users must redirect to login")
        self.client.post(reverse('login'), {'username': self.user.username,
                                            'password': self.password})
        responce = self.client.get(reverse('new_post'))
        self.assertEqual(responce.status_code, 200,
                         msg='Authorised user access to /new/ issues')
        test_post = 'Test auth new post!'
        self.client.post(reverse('new_post'), {'text': test_post})
        cache.clear()
        responce = self.client.get(reverse('index'))
        self.assertContains(responce, test_post)

    def test_group_exist(self):
        responce = self.client.get(reverse('goup_all'))
        self.assertContains(responce, self.group)

    def test_post_edit(self):
        self.client.post(reverse('login'), {'username': self.user.username,
                                            'password': self.password})
        new_post = 'This is new post for tests'
        new_group_post = 'This is new group post'
        self.client.post(reverse('post_edit', args=[self.user.username,
                                                    self.post.id]),
                         {'text': new_post})
        self.client.post(reverse('post_edit', args=[self.user.username,
                                                    self.group_post.id]),
                         {'text': new_group_post, 'group': self.group.id})
        edited_post = Post.objects.get(id=self.post.id)
        edited_group_post = Post.objects.get(id=self.group_post.id)
        self.assertEqual(new_post, edited_post.text, msg="Post hasn't changed")
        self.assertEqual(new_group_post, edited_group_post.text,
                         msg="Group post hasn't changed")
        cache.clear()
        responce = self.client.get(reverse('index'))
        self.assertContains(responce, edited_post)
        self.assertContains(responce, edited_group_post)
        responce = self.client.get(reverse('profile',
                                           args=[self.user.username]))
        self.assertContains(responce, edited_post)
        self.assertContains(responce, edited_group_post)
        responce = self.client.get(reverse('group_list',
                                           args=[self.group.slug]))
        self.assertContains(responce, edited_group_post)
        responce = self.client.get(reverse('post', args=[self.user.username,
                                                         self.post.id]))
        responce_group = self.client.get(reverse('post',
                                                 args=[self.user.username,
                                                       self.group_post.id]))
        self.assertContains(responce, edited_post)
        self.assertContains(responce_group, edited_group_post)

    def test_post_exist(self):
        cache.clear()
        responce = self.client.get(reverse('index'))
        self.assertContains(responce, self.post)
        self.assertContains(responce, self.group_post, status_code=200)
        responce = self.client.get(reverse('profile', args=['yandex']))
        self.assertContains(responce, self.post)
        self.assertContains(responce, self.group_post)
        responce = self.client.get(reverse('group_list',
                                           args=[self.group.slug]))
        self.assertContains(responce, self.group_post)
        responce = self.client.get(reverse('post',
                                   args=[self.user.username, self.post.id]))
        responce_group = self.client.get(reverse('post',
                                         args=[self.user.username,
                                               self.group_post.id]))
        self.assertContains(responce, self.post)
        self.assertContains(responce_group, self.group_post)

    def test_error_404(self):
        responce = self.client.get(reverse('page_not_found'))
        self.assertEqual(responce.status_code, 404,
                         msg="Error 404 page work incorrect")
        responce = self.client.get('/get_to_page_witch_does_not_exist/')
        self.assertEqual(responce.status_code, 404,
                         msg="Error 404 page work incorrect")

    def test_image_validation(self):
        self.client.post(reverse('login'), {'username': self.user.username,
                                            'password': self.password})

        with open('requirements.txt') as image:
            responce = self.client.post(reverse('post_edit',
                                                args=[self.user.username,
                                                      self.post.id]),
                                        {'text': 'text', 'image': image})
        self.assertIsNotNone(responce.context['form']['image'].errors,
                             msg='Not image uploaded!')

    def test_cache(self):
        cache.clear()
        responce = self.client.get(reverse('index'))
        new_post = Post.objects.create(text='Post for cache',
                                       author=self.user)
        responce = self.client.get(reverse('index'))
        self.assertNotContains(responce, new_post)

    def test_follow(self):
        self.client.post(reverse('login'), {'username': self.user.username,
                                            'password': self.password})
        follow = Follow.objects.filter(user=self.user).all() or None
        self.assertIsNone(follow)
        self.client.get(reverse('profile_follow',
                                args=[self.following_user.username]))
        follow = Follow.objects.filter(user=self.user).all() or None
        self.assertIsNotNone(follow)
        self.client.get(reverse('profile_unfollow',
                                args=[self.following_user.username]))
        follow = Follow.objects.filter(user=self.user).all() or None
        self.assertIsNone(follow)
        new_post = Post.objects.create(text='This is follow post',
                                       author=self.following_user)
        responce = self.client.get(reverse('follow_index'))
        self.assertNotContains(responce, new_post)
        self.client.get(reverse('profile_follow',
                                args=[self.following_user.username]))
        responce = self.client.get(reverse('follow_index'))
        self.assertContains(responce, new_post)

    def test_comment(self):
        responce = self.client.post(reverse('add_comment',
                                            args=[self.user, self.post.id]),
                                    {'text': 'test_comment'},
                                    follow=True)
        self.assertEqual(responce.resolver_match.url_name, 'login',
                         msg="Unauthorized users must redirect to login")
