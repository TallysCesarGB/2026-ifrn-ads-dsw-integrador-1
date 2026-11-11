"""
Testes de films/services.py usando mocks para a TMDB — não fazem
nenhuma chamada de rede real, garantindo que o CI funcione offline.
"""

import pytest
from django.core.cache import cache

from films import services
from posts.models import Post
from ratings.models import Rating

TMDB_SEARCH_RESPONSE = {
    "results": [
        {
            "id": 603,
            "media_type": "movie",
            "title": "Matrix",
            "release_date": "1999-03-30",
            "poster_path": "/matrix.jpg",
            "vote_average": 8.7,
            "overview": "Um hacker descobre a verdade sobre a realidade.",
        },
    ],
}

TMDB_MOVIE_DETAILS = {
    "id": 603,
    "title": "Matrix",
    "tagline": "Bem-vindo ao deserto do real.",
    "overview": "Um hacker descobre a verdade sobre a realidade.",
    "poster_path": "/matrix.jpg",
    "backdrop_path": "/matrix-bg.jpg",
    "vote_average": 8.7,
    "vote_count": 25000,
    "runtime": 136,
    "release_date": "1999-03-30",
    "genres": [{"name": "Ficção Científica"}, {"name": "Ação"}],
}

TMDB_CREDITS = {
    "cast": [
        {"name": "Keanu Reeves", "character": "Neo", "profile_path": "/keanu.jpg"},
    ],
    "crew": [{"name": "Lana Wachowski", "job": "Director"}],
}

TMDB_PROVIDERS = {
    "results": {"BR": {"flatrate": [{"provider_id": 8, "logo_path": "/netflix.png"}]}},
}

TMDB_VIDEOS = {
    "results": [{"site": "YouTube", "type": "Trailer", "key": "abc123"}],
}


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


class TestSearch:
    def test_search_maps_tmdb_fields(self, mocker):
        mocker.patch("films.services._tmdb_get", return_value=TMDB_SEARCH_RESPONSE)
        results = services.search("matrix", "movie")
        assert len(results) == 1
        assert results[0]["title"] == "Matrix"
        assert results[0]["tmdb_id"] == 603
        assert results[0]["media_type"] == "movie"
        assert results[0]["year"] == "1999"

    def test_search_is_cached(self, mocker):
        mocked = mocker.patch(
            "films.services._tmdb_get",
            return_value=TMDB_SEARCH_RESPONSE,
        )
        services.search("matrix", "movie")
        services.search("matrix", "movie")
        assert mocked.call_count == 1

    def test_search_skips_items_without_title(self, mocker):
        mocker.patch("films.services._tmdb_get", return_value={"results": [{"id": 1}]})
        results = services.search("algo", "movie")
        assert results == []


class TestGetDetail:
    def test_get_detail_combines_endpoints(self, mocker):
        def fake_get(path, params=None):
            if "credits" in path:
                return TMDB_CREDITS
            if "watch/providers" in path:
                return TMDB_PROVIDERS
            if "videos" in path:
                return TMDB_VIDEOS
            return TMDB_MOVIE_DETAILS

        mocker.patch("films.services._tmdb_get", side_effect=fake_get)
        film = services.get_detail("movie", 603)

        assert film["title"] == "Matrix"
        assert film["directors"] == ["Lana Wachowski"]
        assert film["cast"][0]["name"] == "Keanu Reeves"
        assert film["streaming"]["stream"][0]["name"] == "Netflix"
        assert film["trailer"]["key"] == "abc123"

    def test_get_detail_raises_tmdb_error_on_failure(self, mocker):
        mocker.patch("films.services._tmdb_get", side_effect=services.TMDBError("404"))
        with pytest.raises(services.TMDBError):
            services.get_detail("movie", 999999)


class TestGetTrailer:
    def test_embed_url_autoplays_muted_without_js_api(self, mocker):
        """Regressão #40: o ▶ do site já é o clique do usuário, então o vídeo
        começa sozinho (sem som, exigência de autoplay dos navegadores).
        enablejsapi exigiria também o parâmetro `origin` e não é usado."""
        mocker.patch("films.services._tmdb_get", return_value=TMDB_VIDEOS)

        trailer = services.get_trailer("movie", 603)

        assert trailer == {
            "key": "abc123",
            "url": "https://www.youtube.com/embed/abc123?rel=0&autoplay=1&mute=1",
        }

    def test_prefers_trailer_over_teaser(self, mocker):
        videos = {
            "results": [
                {"site": "YouTube", "type": "Teaser", "key": "teaser"},
                {"site": "Vimeo", "type": "Trailer", "key": "vimeo"},
                {"site": "YouTube", "type": "Trailer", "key": "trailer"},
            ],
        }
        mocker.patch("films.services._tmdb_get", return_value=videos)

        assert services.get_trailer("movie", 603)["key"] == "trailer"

    def test_returns_none_when_tmdb_fails(self, mocker):
        mocker.patch("films.services._tmdb_get", side_effect=services.TMDBError("500"))

        assert services.get_trailer("movie", 603) is None


class TestRankings:
    def test_ranking_app_falls_back_to_tmdb_when_no_posts(self, db, mocker):
        mocker.patch(
            "films.services._tmdb_get",
            return_value={
                "results": [
                    {
                        "id": 1,
                        "media_type": "movie",
                        "title": "Fallback",
                        "vote_average": 5,
                    },
                ],
            },
        )
        data = services.get_ranking("app")
        assert data["category"] == "app"
        assert data["items"][0]["title"] == "Fallback"
        assert data["items"][0]["total_posts"] == 0

    def test_ranking_app_uses_internal_posts_when_available(self, db, user):
        Post.objects.create(
            user=user,
            tmdb_id=603,
            media_type="movie",
            title="Matrix",
            poster_url="x",
        )
        Post.objects.create(
            user=user,
            tmdb_id=603,
            media_type="movie",
            title="Matrix",
            poster_url="x",
        )

        data = services.get_ranking("app")
        assert data["items"][0]["title"] == "Matrix"
        assert data["items"][0]["total_posts"] == 2

    def test_ranking_rated_uses_internal_ratings(self, db, user, other_user):
        Post.objects.create(
            user=user,
            tmdb_id=603,
            media_type="movie",
            title="Matrix",
            poster_url="x",
        )
        Rating.objects.create(user=user, tmdb_id=603, media_type="movie", score=9)
        Rating.objects.create(user=other_user, tmdb_id=603, media_type="movie", score=7)

        data = services.get_ranking("rated")
        assert data["items"][0]["title"] == "Matrix"
        assert data["items"][0]["rating"] == 8.0
        assert data["items"][0]["total_ratings"] == 2

    def test_invalid_category_raises_value_error(self):
        with pytest.raises(ValueError, match="Categoria de ranking inválida"):
            services.get_ranking("categoria-invalida")
