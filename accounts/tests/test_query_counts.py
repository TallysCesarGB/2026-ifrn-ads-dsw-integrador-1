"""#46: a busca de usuários não pode fazer um COUNT por usuário (N+1)."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import Follow
from posts.models import Post

User = get_user_model()

MAX_QUERIES = 10
N_USERS = 15


@pytest.fixture
def many_users(user):
    users = [
        User.objects.create_user(
            username=f"cinefilo{i}",
            email=f"cinefilo{i}@ifrn.edu.br",
            password="senha123456",
        )
        for i in range(N_USERS)
    ]
    for u in users:
        Follow.objects.create(follower=user, followed=u)
        Follow.objects.create(follower=u, followed=user)
        Post.objects.create(user=u, tmdb_id=1, media_type="movie", title="A")
        Post.objects.create(user=u, tmdb_id=2, media_type="tv", title="B")
    return users


@pytest.mark.django_db
class TestUserSearchQueryCount:
    def test_search_view(self, auth_client, many_users, django_assert_max_num_queries):
        url = reverse("accounts:search_users") + "?q=cinefilo"
        with django_assert_max_num_queries(MAX_QUERIES):
            data = auth_client.get(url).json()
        assert len(data) == N_USERS
        for item in data:
            assert item["posts_count"] == 2
            assert item["followers_count"] == 1

    def test_search_api(self, api_client, many_users, django_assert_max_num_queries):
        with django_assert_max_num_queries(MAX_QUERIES):
            response = api_client.get("/api/v1/users/search/?q=cinefilo")
        results = response.data["results"]
        assert len(results) == N_USERS
        for item in results:
            assert item["posts_count"] == 2
            assert item["followers_count"] == 1
            assert item["following_count"] == 1
