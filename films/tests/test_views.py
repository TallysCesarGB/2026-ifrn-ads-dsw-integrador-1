import pytest
from django.urls import reverse

from films import services

FAKE_FILM = {
    "tmdb_id": 603,
    "media_type": "movie",
    "title": "Matrix",
    "tagline": "Bem-vindo ao deserto do real.",
    "overview": "Um hacker descobre a verdade.",
    "poster_url": "https://image.tmdb.org/t/p/w500/matrix.jpg",
    "backdrop_url": "https://image.tmdb.org/t/p/original/matrix-bg.jpg",
    "rating": 8.7,
    "vote_count": 25000,
    "runtime": 136,
    "release_date": "1999-03-30",
    "genres": ["Ficção Científica"],
    "seasons": None,
    "trailer": {"key": "abc123", "url": "https://www.youtube.com/embed/abc123"},
    "cast": [{"name": "Keanu Reeves", "character": "Neo", "photo_url": None}],
    "directors": ["Lana Wachowski"],
    "streaming": {"stream": [], "rent": [], "buy": []},
}

FAKE_RANKING = {"category": "movies", "label": "Top 10 Filmes 🇧🇷", "items": []}


@pytest.mark.django_db
class TestFilmDetailView:
    def test_requires_login(self, client):
        response = client.get(
            reverse("films:detail", kwargs={"media_type": "movie", "tmdb_id": 603}),
        )
        assert response.status_code == 302

    def test_renders_film_detail(self, auth_client, mocker):
        mocker.patch("films.services.get_detail", return_value=FAKE_FILM)
        response = auth_client.get(
            reverse("films:detail", kwargs={"media_type": "movie", "tmdb_id": 603}),
        )
        assert response.status_code == 200
        assert b"Matrix" in response.content

    def test_trailer_iframe_sends_referrer_to_youtube(self, auth_client, mocker):
        """Regressão #40: com Referrer-Policy: same-origin (padrão do Django), o
        iframe carregaria sem Referer e o YouTube responderia com o Erro 153.
        O atributo no iframe sobrepõe a política só para o trailer."""
        mocker.patch("films.services.get_detail", return_value=FAKE_FILM)
        url = reverse("films:detail", kwargs={"media_type": "movie", "tmdb_id": 603})

        html = auth_client.get(url).content.decode()
        assert 'id="trailerFrame"' in html
        assert 'referrerpolicy="strict-origin-when-cross-origin"' in html
        assert 'data-trailer-url="https://www.youtube.com/embed/abc123"' in html

    def test_no_trailer_player_when_film_has_no_trailer(self, auth_client, mocker):
        film_sem_trailer = {**FAKE_FILM, "trailer": None}
        mocker.patch("films.services.get_detail", return_value=film_sem_trailer)
        url = reverse("films:detail", kwargs={"media_type": "movie", "tmdb_id": 603})

        html = auth_client.get(url).content.decode()
        assert 'id="trailerFrame"' not in html
        assert 'id="playTrailerBtn"' not in html

    def test_404_when_tmdb_fails(self, auth_client, mocker):
        mocker.patch(
            "films.services.get_detail",
            side_effect=services.TMDBError("not found"),
        )
        response = auth_client.get(
            reverse("films:detail", kwargs={"media_type": "movie", "tmdb_id": 999999}),
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestFilmSearchJSON:
    def test_requires_login(self, client):
        response = client.get(reverse("films:search_json") + "?q=matrix")
        assert response.status_code == 302

    def test_returns_results(self, auth_client, mocker):
        mocker.patch(
            "films.services.search",
            return_value=[{"tmdb_id": 603, "title": "Matrix"}],
        )
        response = auth_client.get(reverse("films:search_json") + "?q=matrix")
        assert response.status_code == 200
        assert response.json()[0]["title"] == "Matrix"

    def test_short_query_returns_empty(self, auth_client):
        response = auth_client.get(reverse("films:search_json") + "?q=m")
        assert response.json() == []


@pytest.mark.django_db
class TestRankingsJSON:
    def test_valid_category(self, auth_client, mocker):
        mocker.patch("films.services.get_ranking", return_value=FAKE_RANKING)
        response = auth_client.get(
            reverse("films:rankings_json", kwargs={"category": "movies"}),
        )
        assert response.status_code == 200
        assert response.json()["category"] == "movies"

    def test_invalid_category_returns_404(self, auth_client, mocker):
        mocker.patch("films.services.get_ranking", side_effect=ValueError())
        response = auth_client.get(
            reverse("films:rankings_json", kwargs={"category": "invalida"}),
        )
        assert response.status_code == 404
