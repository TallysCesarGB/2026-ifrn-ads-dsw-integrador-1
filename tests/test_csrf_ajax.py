"""Chamadas AJAX de escrita com a checagem de CSRF ligada (#50).

O Client padrão do Django desliga o CSRF, por isso o #39 (todo POST via
fetchJSON voltando 403) passou com a suíte verde. Aqui cada endpoint é
chamado como o navegador faz: com `enforce_csrf_checks=True` e o token
lido da <meta name="csrf-token"> da página, não do cookie.
"""

import re

import pytest
from django.urls import reverse

from films import services

FAKE_FILM = {
    "tmdb_id": 603,
    "media_type": "movie",
    "title": "Matrix",
    "tagline": "",
    "overview": "",
    "poster_url": None,
    "backdrop_url": None,
    "rating": 8.7,
    "vote_count": 1,
    "runtime": 136,
    "release_date": "1999-03-30",
    "genres": [],
    "seasons": None,
    "trailer": None,
    "cast": [],
    "directors": [],
    "streaming": {"stream": [], "rent": [], "buy": []},
}


def _endpoints(post, other_user):
    """(nome, url, dados do POST, status esperado com token válido)."""
    return {
        "curtir": (reverse("posts:toggle_like", args=[post.id]), {}, 200),
        "recomendar": (reverse("posts:recommend", args=[post.id]), {}, 200),
        "comentar": (
            reverse("posts:create_comment", args=[post.id]),
            {"content": "Que filme!"},
            201,
        ),
        "avaliar": (
            reverse("ratings:rate"),
            {"tmdb_id": 603, "media_type": "movie", "score": 8},
            200,
        ),
        "seguir": (reverse("accounts:toggle_follow", args=[other_user.id]), {}, 200),
    }


ACTIONS = ["curtir", "recomendar", "comentar", "avaliar", "seguir"]


@pytest.mark.django_db
@pytest.mark.parametrize("action", ACTIONS)
def test_ajax_post_without_csrf_token_is_rejected(
    csrf_client,
    post,
    other_user,
    action,
):
    url, data, _ = _endpoints(post, other_user)[action]

    assert csrf_client.post(url, data).status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("action", ACTIONS)
def test_ajax_post_with_token_from_page_succeeds(
    csrf_client,
    page_csrf_token,
    post,
    other_user,
    action,
):
    url, data, expected = _endpoints(post, other_user)[action]

    response = csrf_client.post(url, data, HTTP_X_CSRFTOKEN=page_csrf_token)

    assert response.status_code == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name",
    ["feed", "new_post", "profile", "film_detail"],
)
def test_pages_with_ajax_expose_csrf_meta_tag(csrf_client, user, mocker, url_name):
    """Toda página que usa fetchJSON precisa da <meta> com um token válido."""
    mocker.patch.object(services, "get_detail", return_value=FAKE_FILM)
    urls = {
        "feed": reverse("posts:feed"),
        "new_post": reverse("posts:new_post"),
        "profile": reverse("accounts:profile", args=[user.username]),
        "film_detail": reverse(
            "films:detail",
            kwargs={"media_type": "movie", "tmdb_id": 603},
        ),
    }

    html = csrf_client.get(urls[url_name]).content.decode()

    match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
    assert match
    assert len(match.group(1)) >= 32
