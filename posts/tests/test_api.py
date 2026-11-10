import pytest
from django.urls import reverse

from accounts.models import Follow
from posts.models import Post


@pytest.mark.django_db
class TestPostListCreateAPI:
    def test_list_is_public(self, api_client, post):
        response = api_client.get(reverse("api-posts"))
        assert response.status_code == 200

    def test_create_requires_auth(self, api_client):
        response = api_client.post(
            reverse("api-posts"),
            {"tmdb_id": 1, "media_type": "movie", "title": "Sem login"},
        )
        assert response.status_code == 401

    def test_create_post_authenticated(self, api_auth_client, user):
        response = api_auth_client.post(
            reverse("api-posts"),
            {"tmdb_id": 603, "media_type": "movie", "title": "Matrix"},
        )
        assert response.status_code == 201
        assert Post.objects.filter(user=user, title="Matrix").exists()


@pytest.mark.django_db
class TestFeedAPI:
    def test_requires_auth(self, api_client):
        response = api_client.get(reverse("api-feed"))
        assert response.status_code == 401

    def test_feed_falls_back_to_global(self, api_auth_client, other_user):
        Post.objects.create(
            user=other_user,
            tmdb_id=1,
            media_type="movie",
            title="Global",
        )
        response = api_auth_client.get(reverse("api-feed"))
        assert response.status_code == 200
        titles = [p["title"] for p in response.data["results"]]
        assert "Global" in titles

    def test_feed_shows_only_followed_when_following_someone(
        self,
        api_auth_client,
        user,
        other_user,
    ):
        Follow.objects.create(follower=user, followed=other_user)
        Post.objects.create(
            user=other_user,
            tmdb_id=1,
            media_type="movie",
            title="Da Maria",
        )
        Post.objects.create(
            user=user,
            tmdb_id=2,
            media_type="movie",
            title="Do próprio usuário",
        )
        response = api_auth_client.get(reverse("api-feed"))
        titles = [p["title"] for p in response.data["results"]]
        assert "Da Maria" in titles
        assert "Do próprio usuário" not in titles


@pytest.mark.django_db
class TestPostLikeAndRecommendAPI:
    def test_like_toggle(self, api_auth_client, post):
        url = reverse("api-post-like", kwargs={"post_id": post.id})
        response = api_auth_client.post(url)
        assert response.status_code == 200
        assert response.data["liked"] is True

        response = api_auth_client.post(url)
        assert response.data["liked"] is False

    def test_recommend(self, api_auth_client, post):
        url = reverse("api-post-recommend", kwargs={"post_id": post.id})
        response = api_auth_client.post(url)
        assert response.status_code == 200
        assert response.data["ok"] is True


@pytest.mark.django_db
class TestPostCommentsAPI:
    def test_create_and_list(self, api_auth_client, post):
        url = reverse("api-post-comments", kwargs={"post_id": post.id})
        response = api_auth_client.post(url, {"content": "Comentário via API"})
        assert response.status_code == 201

        response = api_auth_client.get(url)
        assert response.status_code == 200
        assert response.data["results"][0]["content"] == "Comentário via API"
