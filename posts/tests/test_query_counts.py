"""#46: as listagens de posts não podem fazer um COUNT por post (N+1)."""

import pytest
from django.urls import reverse

from posts.models import Comment
from posts.models import Like
from posts.models import Post

MAX_QUERIES = 10
N_POSTS = 20


@pytest.fixture
def many_posts(user, other_user):
    posts = [
        Post.objects.create(
            user=other_user,
            tmdb_id=1000 + i,
            media_type="movie",
            title=f"Filme {i}",
        )
        for i in range(N_POSTS)
    ]
    # Curtidas e comentários em todos, para cada contador ter algo a contar.
    for p in posts:
        Like.objects.create(user=user, post=p)
        Like.objects.create(user=other_user, post=p)
        Comment.objects.create(post=p, user=user, content="Bom")
    return posts


@pytest.mark.django_db
class TestPostListQueryCount:
    def test_feed(self, auth_client, many_posts, django_assert_max_num_queries):
        with django_assert_max_num_queries(MAX_QUERIES):
            response = auth_client.get(reverse("posts:feed"))
        assert response.status_code == 200

    def test_feed_more(self, auth_client, many_posts, django_assert_max_num_queries):
        with django_assert_max_num_queries(MAX_QUERIES):
            response = auth_client.get(reverse("posts:feed_more") + "?page=1")
        assert response.status_code == 200

    def test_api_posts(
        self,
        api_auth_client,
        many_posts,
        django_assert_max_num_queries,
    ):
        with django_assert_max_num_queries(MAX_QUERIES):
            response = api_auth_client.get("/api/v1/posts/")
        assert response.status_code == 200

    def test_api_feed(self, api_auth_client, many_posts, django_assert_max_num_queries):
        with django_assert_max_num_queries(MAX_QUERIES):
            response = api_auth_client.get("/api/v1/feed/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestAnnotatedCounts:
    """As contagens anotadas precisam bater com as reais (sem duplicar pelo
    JOIN de curtidas x comentários)."""

    def test_api_returns_correct_counts(self, api_auth_client, many_posts):
        results = api_auth_client.get("/api/v1/posts/").data["results"]
        assert results
        for item in results:
            assert item["likes_count"] == 2
            assert item["comments_count"] == 1
            assert item["is_liked"] is True

    def test_queryset_annotation(self, many_posts):
        post = Post.objects.with_counts().get(pk=many_posts[0].pk)
        assert post.likes_count == 2
        assert post.comments_count == 1

    def test_unannotated_post_still_counts(self, many_posts):
        post = Post.objects.get(pk=many_posts[0].pk)
        assert post.likes_count == 2
        assert post.comments_count == 1
