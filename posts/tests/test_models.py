import pytest
from django.db import IntegrityError

from posts.models import Comment
from posts.models import Like
from posts.models import Post
from posts.models import Recommendation


@pytest.mark.django_db
class TestPost:
    def test_str_representation(self, post, user):
        assert str(post) == f"{user.username} → Matrix"

    def test_likes_and_comments_count_start_at_zero(self, post):
        assert post.likes_count == 0
        assert post.comments_count == 0

    def test_get_absolute_url(self, post):
        assert post.get_absolute_url() == f"/filmes/movie/{post.tmdb_id}/"

    def test_ordering_is_most_recent_first(self, user):
        older = Post.objects.create(
            user=user,
            tmdb_id=1,
            media_type="movie",
            title="Antigo",
        )
        newer = Post.objects.create(
            user=user,
            tmdb_id=2,
            media_type="movie",
            title="Novo",
        )
        assert list(Post.objects.all()) == [newer, older]


@pytest.mark.django_db
class TestLike:
    def test_like_increments_count(self, post, user):
        Like.objects.create(user=user, post=post)
        assert post.likes_count == 1

    def test_cannot_like_twice(self, post, user):
        Like.objects.create(user=user, post=post)
        with pytest.raises(IntegrityError):
            Like.objects.create(user=user, post=post)


@pytest.mark.django_db
class TestComment:
    def test_comment_increments_count(self, post, user):
        Comment.objects.create(post=post, user=user, content="Muito bom!")
        assert post.comments_count == 1

    def test_comments_ordered_by_creation(self, post, user):
        c1 = Comment.objects.create(post=post, user=user, content="Primeiro")
        c2 = Comment.objects.create(post=post, user=user, content="Segundo")
        assert list(post.comment_set.all()) == [c1, c2]


@pytest.mark.django_db
class TestRecommendation:
    def test_create_recommendation(self, post, other_user):
        rec = Recommendation.objects.create(
            original_post=post,
            recommended_by=other_user,
        )
        assert rec.original_post == post
        assert post.recommendations.count() == 1
