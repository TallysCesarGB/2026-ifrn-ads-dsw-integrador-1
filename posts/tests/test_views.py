import pytest
from django.urls import reverse

from accounts.models import Follow
from posts.models import Comment
from posts.models import Like
from posts.models import Post
from posts.models import Recommendation


@pytest.mark.django_db
class TestFeedView:
    def test_requires_login(self, client):
        response = client.get(reverse("posts:feed"))
        assert response.status_code == 302

    def test_empty_feed_shows_call_to_action(self, auth_client):
        response = auth_client.get(reverse("posts:feed"))
        assert response.status_code == 200
        assert "Seu feed está vazio".encode() in response.content

    def test_feed_falls_back_to_global_timeline_when_not_following_anyone(
        self,
        auth_client,
        other_user,
    ):
        Post.objects.create(
            user=other_user,
            tmdb_id=1,
            media_type="movie",
            title="De outra pessoa",
        )
        response = auth_client.get(reverse("posts:feed"))
        assert b"De outra pessoa" in response.content

    def test_feed_shows_posts_from_followed_users(self, auth_client, user, other_user):
        Follow.objects.create(follower=user, followed=other_user)
        Post.objects.create(
            user=other_user,
            tmdb_id=1,
            media_type="movie",
            title="Indicado pela Maria",
        )
        response = auth_client.get(reverse("posts:feed"))
        assert b"Indicado pela Maria" in response.content

    def test_feed_has_user_search(self, auth_client):
        """#41: a busca de usuários fica na página principal."""
        html = auth_client.get(reverse("posts:feed")).content.decode()

        assert 'id="userSearchInput"' in html
        assert 'id="userSearchResults"' in html
        assert "js/user_search.js" in html

    def test_feed_pagination_endpoint(self, auth_client, post):
        response = auth_client.get(reverse("posts:feed_more") + "?page=1")
        assert response.status_code == 200
        data = response.json()
        assert "html" in data
        assert "has_next" in data


@pytest.mark.django_db
class TestNewPostView:
    def test_requires_login(self, client):
        response = client.get(reverse("posts:new_post"))
        assert response.status_code == 302

    def test_create_post_success(self, auth_client, user):
        response = auth_client.post(
            reverse("posts:new_post"),
            {
                "tmdb_id": 603,
                "media_type": "movie",
                "title": "Matrix",
                "poster_url": "https://image.tmdb.org/t/p/w500/matrix.jpg",
                "comment": "Excelente!",
            },
        )
        assert response.status_code == 302
        assert Post.objects.filter(user=user, title="Matrix").exists()

    def test_create_post_missing_required_field(self, auth_client):
        response = auth_client.post(
            reverse("posts:new_post"),
            {"comment": "sem filme selecionado"},
        )
        assert response.status_code == 200
        assert Post.objects.count() == 0


@pytest.mark.django_db
class TestPostActions:
    def test_toggle_like(self, auth_client, post):
        url = reverse("posts:toggle_like", kwargs={"post_id": post.id})

        response = auth_client.post(url)
        assert response.status_code == 200
        assert response.json()["liked"] is True
        assert Like.objects.filter(post=post).exists()

        response = auth_client.post(url)
        assert response.json()["liked"] is False
        assert not Like.objects.filter(post=post).exists()

    def test_recommend_post(self, auth_client, post, user):
        url = reverse("posts:recommend", kwargs={"post_id": post.id})
        response = auth_client.post(url)
        assert response.status_code == 200
        assert Recommendation.objects.filter(
            original_post=post,
            recommended_by=user,
        ).exists()

    def test_create_and_list_comments(self, auth_client, post):
        create_url = reverse("posts:create_comment", kwargs={"post_id": post.id})
        response = auth_client.post(create_url, {"content": "Muito bom mesmo!"})
        assert response.status_code == 201
        assert Comment.objects.filter(post=post, content="Muito bom mesmo!").exists()

        list_url = reverse("posts:list_comments", kwargs={"post_id": post.id})
        response = auth_client.get(list_url)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Muito bom mesmo!"

    def test_actions_require_login(self, client, post):
        like_url = reverse("posts:toggle_like", kwargs={"post_id": post.id})
        response = client.post(like_url)
        assert response.status_code == 302
