"""
Fixtures compartilhadas entre os testes de todos os apps do CineClub.
"""

import re

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
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


@pytest.fixture
def csrf_client(user):
    """Client de sessão logado COM checagem de CSRF (o Client padrão do
    Django a desliga). Use para testar as chamadas AJAX como o navegador faz."""
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    return client


@pytest.fixture
def page_csrf_token(csrf_client):
    """Token CSRF lido da <meta name="csrf-token"> do feed, o mesmo lugar de
    onde o window.fetchJSON (base.html) o lê."""
    html = csrf_client.get(reverse("posts:feed")).content.decode()
    match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
    assert match, "base.html não expõe o token CSRF na <meta>"
    return match.group(1)
