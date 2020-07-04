from django.test import TestCase, Client
from .models import Post, Group, User, Follow, Comment
from .forms import PostForm
from django.urls import reverse


class TestUnauthorizedUser(TestCase):
    def setUp(self):
        self.client = Client()

    def test_unauthorized_create_post(self):
        response = self.client.get(reverse("new_post"))
        self.assertEqual(response.status_code, 302, msg="New post unavailable for unauthorized")
        

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
        with open('posts/media/file.jpg','rb') as img:
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
        with open('posts/media/file_2.jpg','rb') as img:
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
        with open('posts/urls.py','rb') as img:
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
        self.client = Client()
    
    def test_if_caching(self):
        response_1 = self.client.get(reverse('index'))
        self.assertEqual(len(response_1.context["page"]), 0)

