"""Exclusão de indicações e comentários (#47).

Regras: a indicação só pode ser excluída pelo autor; o comentário, pelo
autor dele ou pelo dono do post em que foi feito. Os demais recebem 403
e nada é apagado.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from posts.models import Comment
from posts.models import Like
from posts.models import Post
from posts.models import Recommendation

User = get_user_model()

JSON = {"HTTP_ACCEPT": "application/json"}


@pytest.fixture
def third_user(db):
    return User.objects.create_user(
        username="joao",
        email="joao@ifrn.edu.br",
        password="senha123456",
    )


@pytest.fixture
def other_post(other_user):
    return Post.objects.create(
        user=other_user,
        tmdb_id=550,
        media_type="movie",
        title="Clube da Luta",
    )


@pytest.fixture
def other_client(client, other_user):
    client.force_login(other_user)
    return client


def _api_client_for(user):
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


# ---------------------------------------------------------------- site: post


@pytest.mark.django_db
class TestDeletePostView:
    def url(self, post_id):
        return reverse("posts:delete_post", args=[post_id])

    def test_requires_login(self, client, post):
        response = client.post(self.url(post.id))
        assert response.status_code == 302
        assert response.url.startswith(reverse("accounts:login"))
        assert Post.objects.filter(id=post.id).exists()

    def test_get_not_allowed(self, auth_client, post):
        assert auth_client.get(self.url(post.id)).status_code == 405
        assert Post.objects.filter(id=post.id).exists()

    def test_author_deletes_via_form_and_is_redirected(self, auth_client, post):
        response = auth_client.post(self.url(post.id), follow=True)
        assert response.redirect_chain[-1][0] == reverse("posts:feed")
        assert not Post.objects.filter(id=post.id).exists()
        assert "excluída".encode() in response.content

    def test_author_deletes_via_ajax(self, auth_client, post):
        response = auth_client.post(self.url(post.id), **JSON)
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        assert not Post.objects.filter(id=post.id).exists()

    def test_other_user_gets_403_via_ajax(self, other_client, post):
        response = other_client.post(self.url(post.id), **JSON)
        assert response.status_code == 403
        assert Post.objects.filter(id=post.id).exists()

    def test_other_user_gets_403_via_form(self, other_client, post):
        response = other_client.post(self.url(post.id))
        assert response.status_code == 403
        assert Post.objects.filter(id=post.id).exists()

    def test_missing_post_is_404(self, auth_client):
        assert auth_client.post(self.url(999999), **JSON).status_code == 404

    def test_cascades_likes_comments_and_recommendations(
        self,
        auth_client,
        post,
        other_user,
    ):
        Like.objects.create(user=other_user, post=post)
        Comment.objects.create(post=post, user=other_user, content="Top")
        Recommendation.objects.create(original_post=post, recommended_by=other_user)

        auth_client.post(self.url(post.id), **JSON)

        assert not Like.objects.filter(post_id=post.id).exists()
        assert not Comment.objects.filter(post_id=post.id).exists()
        assert not Recommendation.objects.filter(original_post_id=post.id).exists()

    def test_feed_shows_delete_button_only_on_own_posts(
        self,
        auth_client,
        post,
        other_post,
    ):
        html = auth_client.get(reverse("posts:feed")).content.decode()
        assert self.url(post.id) in html
        assert self.url(other_post.id) not in html

    def test_feed_more_shows_delete_button_only_on_own_posts(
        self,
        auth_client,
        post,
        other_post,
    ):
        html = auth_client.get(reverse("posts:feed_more")).json()["html"]
        assert self.url(post.id) in html
        assert self.url(other_post.id) not in html


# ----------------------------------------------------------- site: comentário


@pytest.mark.django_db
class TestDeleteCommentView:
    def url(self, comment_id):
        return reverse("posts:delete_comment", args=[comment_id])

    def test_requires_login(self, client, post, user):
        comment = Comment.objects.create(post=post, user=user, content="Oi")
        response = client.post(self.url(comment.id))
        assert response.status_code == 302
        assert Comment.objects.filter(id=comment.id).exists()

    def test_get_not_allowed(self, auth_client, post, user):
        comment = Comment.objects.create(post=post, user=user, content="Oi")
        assert auth_client.get(self.url(comment.id)).status_code == 405

    def test_comment_author_deletes_on_someone_elses_post(
        self,
        auth_client,
        user,
        other_post,
    ):
        comment = Comment.objects.create(post=other_post, user=user, content="Meu")
        Comment.objects.create(post=other_post, user=other_post.user, content="Fica")

        response = auth_client.post(self.url(comment.id))

        assert response.status_code == 200
        assert response.json() == {"ok": True, "comments_count": 1}
        assert not Comment.objects.filter(id=comment.id).exists()

    def test_post_owner_deletes_comment_from_someone_else(
        self,
        auth_client,
        post,
        other_user,
    ):
        comment = Comment.objects.create(post=post, user=other_user, content="Spoiler")
        response = auth_client.post(self.url(comment.id))
        assert response.status_code == 200
        assert not Comment.objects.filter(id=comment.id).exists()

    def test_third_user_gets_403(self, client, post, other_user, third_user):
        comment = Comment.objects.create(post=post, user=other_user, content="Oi")
        client.force_login(third_user)
        response = client.post(self.url(comment.id))
        assert response.status_code == 403
        assert Comment.objects.filter(id=comment.id).exists()

    def test_missing_comment_is_404(self, auth_client):
        assert auth_client.post(self.url(999999)).status_code == 404

    def test_list_comments_flags_what_viewer_can_delete(
        self,
        client,
        post,
        user,
        other_user,
        third_user,
    ):
        own = Comment.objects.create(post=post, user=third_user, content="Meu")
        Comment.objects.create(post=post, user=other_user, content="Alheio")
        url = reverse("posts:list_comments", args=[post.id])

        client.force_login(third_user)
        flags = {c["id"]: c["can_delete"] for c in client.get(url).json()}
        assert flags[own.id] is True
        assert sum(flags.values()) == 1

        client.force_login(user)  # dono do post pode apagar todos
        assert all(c["can_delete"] for c in client.get(url).json())

    def test_created_comment_is_deletable_by_author(self, other_client, post):
        response = other_client.post(
            reverse("posts:create_comment", args=[post.id]),
            {"content": "Novo"},
        )
        assert response.json()["can_delete"] is True


# ------------------------------------------------------------------ API: post


@pytest.mark.django_db
class TestPostDetailAPI:
    def url(self, post_id):
        return reverse("api-post-detail", args=[post_id])

    def test_retrieve_is_public(self, api_client, post):
        response = api_client.get(self.url(post.id))
        assert response.status_code == 200
        assert response.data["title"] == "Matrix"

    def test_delete_requires_auth(self, api_client, post):
        assert api_client.delete(self.url(post.id)).status_code == 401
        assert Post.objects.filter(id=post.id).exists()

    def test_author_deletes(self, api_auth_client, post):
        assert api_auth_client.delete(self.url(post.id)).status_code == 204
        assert not Post.objects.filter(id=post.id).exists()

    def test_other_user_gets_403(self, post, other_user):
        response = _api_client_for(other_user).delete(self.url(post.id))
        assert response.status_code == 403
        assert Post.objects.filter(id=post.id).exists()

    def test_missing_post_is_404(self, api_auth_client):
        assert api_auth_client.delete(self.url(999999)).status_code == 404

    def test_put_not_allowed(self, api_auth_client, post):
        response = api_auth_client.put(self.url(post.id), {"title": "Outro"})
        assert response.status_code == 405


# ------------------------------------------------------------ API: comentário


@pytest.mark.django_db
class TestCommentDetailAPI:
    def url(self, comment):
        return reverse("api-post-comment-detail", args=[comment.post_id, comment.id])

    def test_retrieve_is_public(self, api_client, post, other_user):
        comment = Comment.objects.create(post=post, user=other_user, content="Oi")
        response = api_client.get(self.url(comment))
        assert response.status_code == 200
        assert response.data["content"] == "Oi"

    def test_delete_requires_auth(self, api_client, post, user):
        comment = Comment.objects.create(post=post, user=user, content="Oi")
        assert api_client.delete(self.url(comment)).status_code == 401
        assert Comment.objects.filter(id=comment.id).exists()

    def test_comment_author_deletes(self, other_post, user, api_auth_client):
        comment = Comment.objects.create(post=other_post, user=user, content="Meu")
        assert api_auth_client.delete(self.url(comment)).status_code == 204
        assert not Comment.objects.filter(id=comment.id).exists()

    def test_post_owner_deletes(self, api_auth_client, post, other_user):
        comment = Comment.objects.create(post=post, user=other_user, content="Alheio")
        assert api_auth_client.delete(self.url(comment)).status_code == 204
        assert not Comment.objects.filter(id=comment.id).exists()

    def test_third_user_gets_403(self, post, other_user, third_user):
        comment = Comment.objects.create(post=post, user=other_user, content="Oi")
        response = _api_client_for(third_user).delete(self.url(comment))
        assert response.status_code == 403
        assert Comment.objects.filter(id=comment.id).exists()

    def test_comment_from_another_post_is_404(
        self,
        api_auth_client,
        post,
        other_post,
        user,
    ):
        comment = Comment.objects.create(post=other_post, user=user, content="Meu")
        url = reverse("api-post-comment-detail", args=[post.id, comment.id])
        assert api_auth_client.delete(url).status_code == 404
        assert Comment.objects.filter(id=comment.id).exists()
