from django.test import TestCase, Client
from .models import Post, Group, User, Follow, Comment
from .forms import PostForm
from django.urls import reverse
from django.core.cache import cache
from django.test.utils import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile


DUMMY_CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        }
    }

class TestUnauthorizedUser(TestCase):
    def setUp(self):
        self.client = Client()

    def test_unauthorized_create_post(self):
        response = self.client.get(reverse("new_post"))
        self.assertEqual(response.status_code, 302, msg="New post unavailable for unauthorized")
        

@override_settings(
    CACHES=DUMMY_CACHES,
)
class TestAuthorizedUser(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="kenga",
            email="kenga@yatube.com",
            password="Ru0987"
        )
        self.group = Group.objects.create(title="group to test", slug="gtt")
        self.group_2 = Group.objects.create(title="just another group", slug="jag")
        self.text = "Where is Kroshka Ru?"
        self.client.force_login(self.user)

    
    def test_profile_creation(self):
        response = self.client.get(reverse("profile", kwargs={"username": "kenga"}))
        self.assertEqual(response.status_code, 200, msg="profile created")
        self.assertIsInstance(response.context["author"], User, msg="author is instance of User")
        self.assertEqual(response.context["author"].username, self.user.username, msg="author is user")
        
    def check_post_on_pages(self, username="kenga", post_id=1, text=None, group=None):
        if text is None:
            text = self.text
        response = self.client.get(reverse("profile", kwargs={"username": username}))
        self.assertContains(response, text)
        response = self.client.get(reverse("index"))
        self.assertContains(response, text)
        response = self.client.get(reverse("post", kwargs={"username": username, "post_id": post_id}))
        self.assertContains(response, text)
        if group:
            response = self.client.get(reverse("group_posts", kwargs={"slug": group}))
            self.assertEqual(len(response.context["page"]), 1)

    def check_post_in_database(self, username="kenga", post_id=1, text=None, group=None):
        if text is None:
            text = self.text
        self.assertEqual(Post.objects.count(), 1)
        post_to_check = Post.objects.get(id=1)
        self.assertEqual(post_to_check.author, self.user)
        self.assertEqual(post_to_check.text, text)
        if group:
            self.assertEqual(post_to_check.group, Group.objects.get(slug=group))

    def test_new_post(self):
        response = self.client.get(reverse("new_post"))
        self.assertEqual(response.status_code, 200, msg="new post page is available")
        self.client.post(reverse("new_post"), {'text': self.text})
        self.check_post_on_pages()
        self.check_post_in_database()    

        response = self.client.get(
            reverse(
                "post_edit",
                kwargs={"username": "kenga", "post_id": 1}
            )
        )
        self.assertEqual(response.status_code, 200)
        self.client.post(
            reverse(
                "post_edit",
                kwargs={"username": "kenga", "post_id": 1}
            ),
            {'text': "Just text"}
        )
        self.check_post_on_pages(text="Just text")
        self.check_post_in_database(text="Just text")
    
    def test_new_post_in_group(self):
        self.client.post(reverse("new_post"), {'text': self.text, 'group': self.group.id})
        self.check_post_on_pages(group="gtt")
        self.check_post_in_database(group="gtt")

        response = self.client.get(
            reverse(
                "post_edit",
                kwargs={"username": "kenga", "post_id": 1}
            )
        )
        self.assertEqual(response.status_code, 200)
        self.client.post(
            reverse(
                "post_edit",
                kwargs={"username": "kenga", "post_id": 1}
            ),
            {'text': "Just text", 'group': self.group_2.id}
        )
        self.check_post_on_pages(text="Just text", group="jag")
        self.check_post_in_database(text="Just text", group="jag")
        response = self.client.get(reverse("group_posts", kwargs={"slug": "gtt"}))
        self.assertEqual(len(response.context["page"]), 0, msg="post deleted in previous group")


class TestErrorPages(TestCase):
    def setUp(self):
        self.client = Client()

    def test_404(self):
        response = self.client.get(reverse("profile", kwargs={"username": "somecrazybullshitidontknow"}), follow=True)
        self.assertEqual(response.status_code, 404, msg="404")
        self.assertTemplateUsed("misc/404.html")


@override_settings(
    CACHES=DUMMY_CACHES,
)
class TestImageUpload(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="kenga",
            email="kenga@yatube.com",
            password="Ru0987"
        )
        self.group = Group.objects.create(title="group to test", slug="gtt")
        self.client.force_login(self.user)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        img = SimpleUploadedFile("test-img.gif", small_gif, content_type='image/gif')
        post = self.client.post(
            reverse("new_post"),
            {'text': 'post with image', 'image': img, 'group': self.group.id}
        )

    def check_image(self, username="kenga", post_id=1, group=None):
        response = self.client.get(reverse("profile", kwargs={"username": username}))
        self.assertContains(response, "<img")
        response = self.client.get(reverse("index"))
        self.assertContains(response, "<img")
        response = self.client.get(reverse("post", kwargs={"username": username, "post_id": post_id}))
        self.assertContains(response, "<img")
        if group:
            response = self.client.get(reverse("group_posts", kwargs={"slug": group}))
            self.assertContains(response, "<img")
    
    def test_new_post_with_image(self):
        self.check_image(group="gtt")

    def test_image_post_edit(self):
        self.group_2 = Group.objects.create(title="just another group", slug="jag")
        small_gif_2 = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        img = SimpleUploadedFile("test-img-2.gif", small_gif_2, content_type='image/gif')
        post = self.client.post(
            reverse("post_edit",
                kwargs={"username": "kenga", "post_id": 1}
                ),
            {'text': 'changed post with image', 'image': img, 'group': self.group_2.id}
        )
        self.assertEqual(Post.objects.count(), 1)
        response = self.client.get(reverse("group_posts", kwargs={"slug": "jag"}))
        self.assertContains(response, "<img")

    
    def test_non_image_upload(self):
        self.assertEqual(Post.objects.count(), 1)
        img = SimpleUploadedFile("test.txt", b'ifuckinghatefakeimageupload')
        post = self.client.post(
            reverse("new_post"),
            {'text': 'post with no-image', 'image': img}
        )
        self.assertFormError(
            post,
            form='form',
            field='image',
            errors='Загрузите правильное изображение. Файл, который вы загрузили, поврежден или не является изображением.',
            msg_prefix=''
        )


class TestCacheIndexPage(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username="kenga",
            email="kenga@yatube.com",
            password="Ru0987"
        )
        self.client.force_login(self.user)
    
    def test_if_caching(self):
        text_1 = 'first test post to test caching'
        post1 = self.client.post(
            reverse('new_post'),
            {'text': text_1}
        )
        response_1 = self.client.get(reverse('index'))
        self.assertContains(response_1, text_1)
        text_2 = 'second post just to check'
        post2 = self.client.post(
            reverse('new_post'),
            {'text': text_2}
        )
        response_2 = self.client.get(reverse('index'))
        self.assertNotContains(response_2, text_2)


@override_settings(
    CACHES=DUMMY_CACHES,
)
class TestPostComments(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="kenga",
            email="kenga@yatube.com",
            password="Ru0987"
        )
        self.post_to_comment = Post.objects.create(author=self.user, text="Just post")

    def test_unauthorized_to_comment(self):
        response = self.client.get(reverse('post', kwargs={"username": "kenga", "post_id": 1}))
        self.assertContains(response, self.post_to_comment.text)
        comment = self.client.get(reverse('add_comment', kwargs={"username": "kenga", "post_id": 1}))
        self.assertEqual(comment.status_code, 302, msg='commenting not available to unauthorized')
        self.assertEqual(Comment.objects.count(), 0)

    def test_authorized_to_comment(self):
        self.user_2 = User.objects.create_user(
            username="snork",
            email="snork@yatube.com",
            password="Mummi0987"
        )
        self.client.force_login(self.user_2)
        post = self.client.post(reverse('add_comment', kwargs={"username": "kenga", "post_id": 1}), {'text': 'Just comment'})
        response = self.client.get(reverse('post', kwargs={"username": "kenga", "post_id": 1}))
        self.assertContains(response, 'Just comment')
        self.assertIsInstance(response.context["comments"][0], Comment, msg="comment added")
        self.assertEqual(len(response.context['comments']), 1)

        self.assertEqual(Comment.objects.count(), 1)
        comment_to_check = Comment.objects.get(id=1)
        self.assertEqual(comment_to_check.author, self.user_2)
        self.assertEqual(comment_to_check.text, "Just comment")
        self.assertEqual(comment_to_check.post.id, 1)


@override_settings(
    CACHES=DUMMY_CACHES,
)
class TestFollowSystem(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="kenga",
            email="kenga@yatube.com",
            password="Ru0987"
        )
        self.post = Post.objects.create(author=self.user, text="Just post")
        self.user_2 = User.objects.create_user(
            username="snork",
            email="snork@yatube.com",
            password="Mummi0987"
        )
        self.user_3 = User.objects.create_user(
            username="peppi",
            email="peppi@yatube.com",
            password="Stocking0987"
        )

    def test_follow(self):
        self.client.force_login(self.user)
        follow = self.client.get(reverse('profile_follow', kwargs={"username":"snork"}))
        self.assertTrue(Follow.objects.filter(user=self.user, author=self.user_2).exists())
        self.assertEqual(Follow.objects.count(), 1)
        follower = Follow.objects.get(id=1)
        self.assertEqual(follower.user, self.user)
        self.assertEqual(follower.author, self.user_2)

    def test_unfollow(self):
        unfollow = self.client.get(reverse('profile_unfollow', kwargs={"username":"snork"}))
        self.assertFalse(Follow.objects.filter(user=self.user, author=self.user_2).exists())
        self.assertEqual(Follow.objects.count(), 0)

    def test_following_post_appearance(self):
        link_1 = Follow.objects.create(user=self.user_3, author=self.user_2)
        link_2 = Follow.objects.create(user=self.user_3, author=self.user)
        link_3 = Follow.objects.create(user=self.user_2, author=self.user_3)
        self.client.force_login(self.user_3)
        response_1 = self.client.get(reverse('follow_index'))
        self.assertEqual(len(response_1.context["page"]), 1, msg="post in follower follow index page")
        self.client.logout()
    
    def test_nonfollowing_post_not_appear(self):
        self.client.force_login(self.user_2)
        response_2 = self.client.get(reverse('follow_index'))
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(len(response_2.context['page']), 0, msg='no post in non-follower page')
