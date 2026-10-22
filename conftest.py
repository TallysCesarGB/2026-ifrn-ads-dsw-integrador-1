"""
Fixtures compartilhadas entre os testes de todos os apps do CineClub.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def user(db):
    u = User.objects.create_user(
        username="tallys",
        email="tallys@ifrn.edu.br",
        password="senha123456",
    )
    u.profile.display_name = "Tallys"
    u.profile.save()
    return u


@pytest.fixture
def other_user(db):
    u = User.objects.create_user(
        username="maria",
        email="maria@ifrn.edu.br",
        password="senha123456",
    )
    u.profile.display_name = "Maria"
    u.profile.save()
    return u


@pytest.fixture
def auth_client(client, user):
    """Client Django (sessão) já autenticado — para testar as views/templates."""
    client.force_login(user)
    return client


@pytest.fixture
def api_client():
    """Client da API sem autenticação."""
    return APIClient()


@pytest.fixture
def api_auth_client(api_client, user):
    """Client da API autenticado via JWT (SimpleJWT)."""
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


@pytest.fixture
def post(db, user):
    from posts.models import Post

    return Post.objects.create(
        user=user,
        tmdb_id=603,
        media_type="movie",
        title="Matrix",
        poster_url="https://image.tmdb.org/t/p/w500/matrix.jpg",
        comment="Filme incrível!",
    )
