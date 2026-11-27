"""
Testes de films/services.py usando mocks para a TMDB — não fazem
nenhuma chamada de rede real, garantindo que o CI funcione offline.

_tmdb_get e _build_streaming são testados diretamente porque concentram
os caminhos de erro da integração (#49).
"""

# ruff: noqa: SLF001

import logging

import pytest
import requests
from django.conf import settings
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


def _movie(tmdb_id, **extra):
    """Item mínimo de lista da TMDB (trending/discover/top_rated)."""
    return {"id": tmdb_id, "title": f"Filme {tmdb_id}", "vote_average": 7, **extra}


class TestTmdbGet:
    def test_network_error_becomes_tmdb_error(self, mocker):
        mocker.patch(
            "films.services.requests.get",
            side_effect=requests.ConnectionError("sem rede"),
        )
        with pytest.raises(services.TMDBError, match="sem rede"):
            services._tmdb_get("/movie/603")

    def test_timeout_becomes_tmdb_error(self, mocker):
        mocker.patch("films.services.requests.get", side_effect=requests.Timeout())
        with pytest.raises(services.TMDBError):
            services._tmdb_get("/movie/603")

    def test_non_2xx_response_becomes_tmdb_error(self, mocker):
        response = mocker.Mock(ok=False, status_code=401)
        mocker.patch("films.services.requests.get", return_value=response)
        with pytest.raises(services.TMDBError, match="TMDB 401: /movie/603"):
            services._tmdb_get("/movie/603")
        response.json.assert_not_called()

    def test_sends_api_key_language_and_extra_params(self, mocker):
        response = mocker.Mock(ok=True)
        response.json.return_value = {"id": 603}
        get = mocker.patch("films.services.requests.get", return_value=response)

        data = services._tmdb_get("/search/movie", {"query": "matrix"})

        assert data == {"id": 603}
        get.assert_called_once_with(
            f"{settings.TMDB_BASE_URL}/search/movie",
            params={
                "api_key": settings.TMDB_API_KEY,
                "language": settings.TMDB_LANGUAGE,
                "query": "matrix",
            },
            timeout=8,
        )

    def test_extra_params_override_language(self, mocker):
        response = mocker.Mock(ok=True)
        response.json.return_value = {}
        get = mocker.patch("films.services.requests.get", return_value=response)

        services._tmdb_get("/movie/603/videos", {"language": "en-US"})

        assert get.call_args.kwargs["params"]["language"] == "en-US"


class TestGetTrailerFallbacks:
    @staticmethod
    def _videos(pt, en=()):
        """Simula as duas chamadas de get_trailer: pt-BR e en-US."""

        def fake_get(path, params=None):
            videos = en if params and params.get("language") == "en-US" else pt
            return {"results": list(videos)}

        return fake_get

    def test_teaser_when_there_is_no_trailer(self, mocker):
        mocker.patch(
            "films.services._tmdb_get",
            side_effect=self._videos(
                [
                    {"site": "YouTube", "type": "Clip", "key": "clip"},
                    {"site": "YouTube", "type": "Teaser", "key": "teaser"},
                ],
            ),
        )
        assert services.get_trailer("movie", 603)["key"] == "teaser"

    def test_any_youtube_video_as_last_resort(self, mocker):
        mocker.patch(
            "films.services._tmdb_get",
            side_effect=self._videos(
                [
                    {"site": "Vimeo", "type": "Trailer", "key": "vimeo"},
                    {"site": "YouTube", "type": "Featurette", "key": "extra"},
                ],
            ),
        )
        assert services.get_trailer("movie", 603)["key"] == "extra"

    def test_uses_english_videos_when_portuguese_has_none(self, mocker):
        mocker.patch(
            "films.services._tmdb_get",
            side_effect=self._videos(
                pt=[],
                en=[{"site": "YouTube", "type": "Trailer", "key": "en"}],
            ),
        )
        assert services.get_trailer("tv", 1399)["key"] == "en"

    def test_ignores_videos_outside_youtube(self, mocker):
        mocker.patch(
            "films.services._tmdb_get",
            side_effect=self._videos(
                [{"site": "Vimeo", "type": "Trailer", "key": "vimeo"}],
            ),
        )
        assert services.get_trailer("movie", 603) is None

    def test_no_videos_returns_none(self, mocker):
        mocker.patch("films.services._tmdb_get", return_value={"results": None})
        assert services.get_trailer("movie", 603) is None


class TestBuildStreaming:
    def test_ignores_providers_outside_platforms(self):
        br = {
            "flatrate": [
                {"provider_id": 99999, "logo_path": "/desconhecido.png"},
                {"provider_id": 8, "logo_path": "/netflix.png"},
            ],
        }
        streaming = services._build_streaming(br, 603)

        assert [p["name"] for p in streaming["stream"]] == ["Netflix"]
        assert streaming["rent"] == []
        assert streaming["buy"] == []

    def test_maps_rent_and_buy_with_kind_and_links(self):
        br = {
            "rent": [{"provider_id": 119, "logo_path": "/prime.png"}],
            "buy": [{"provider_id": 350}],
        }
        streaming = services._build_streaming(br, 603)

        assert streaming["rent"] == [
            {
                "provider_id": 119,
                "name": "Prime Video",
                "emoji": "🔵",
                "kind": "rent",
                "logo_url": "https://image.tmdb.org/t/p/original/prime.png",
                "web_link": "https://www.primevideo.com/search?phrase=603",
            },
        ]
        assert streaming["buy"][0]["kind"] == "buy"
        assert streaming["buy"][0]["logo_url"] is None


class TestGetStreaming:
    @pytest.mark.parametrize(
        ("media_type", "expected"),
        [("tv", "tv"), ("movie", "movie"), ("qualquer", "movie")],
    )
    def test_normalizes_media_type(self, mocker, media_type, expected):
        mocked = mocker.patch(
            "films.services._tmdb_get",
            return_value=TMDB_PROVIDERS,
        )
        streaming = services.get_streaming(media_type, 603)

        mocked.assert_called_once_with(f"/{expected}/603/watch/providers")
        assert streaming["stream"][0]["name"] == "Netflix"

    def test_without_br_providers_returns_empty_lists(self, mocker):
        mocker.patch(
            "films.services._tmdb_get",
            return_value={"results": {"US": {"flatrate": [{"provider_id": 8}]}}},
        )
        assert services.get_streaming("movie", 603) == {
            "stream": [],
            "rent": [],
            "buy": [],
        }

    def test_is_cached(self, mocker):
        mocked = mocker.patch(
            "films.services._tmdb_get",
            return_value=TMDB_PROVIDERS,
        )
        services.get_streaming("movie", 603)
        services.get_streaming("movie", 603)
        assert mocked.call_count == 1


class TestTmdbRankings:
    def test_movies_limited_to_ten_and_typed_as_movie(self, mocker):
        mocked = mocker.patch(
            "films.services._tmdb_get",
            return_value={"results": [_movie(i) for i in range(15)]},
        )
        items = services.ranking_movies()

        mocked.assert_called_once_with("/trending/movie/day", {"region": "BR"})
        assert len(items) == 10
        assert [it["rank"] for it in items] == list(range(1, 11))
        assert {it["media_type"] for it in items} == {"movie"}

    def test_series_limited_to_ten_and_typed_as_tv(self, mocker):
        mocked = mocker.patch(
            "films.services._tmdb_get",
            return_value={"results": [{"id": i, "name": f"S{i}"} for i in range(12)]},
        )
        items = services.ranking_series()

        mocked.assert_called_once_with("/trending/tv/day", {"region": "BR"})
        assert len(items) == 10
        assert {it["media_type"] for it in items} == {"tv"}
        assert items[0]["title"] == "S0"

    def test_world_drops_items_that_are_not_movie_or_tv(self, mocker):
        results = [
            {"id": 1, "media_type": "person", "name": "Keanu Reeves"},
            _movie(2, media_type="movie"),
            {"id": 3, "media_type": "tv", "name": "Série"},
        ] + [_movie(i, media_type="movie") for i in range(10, 25)]
        mocker.patch("films.services._tmdb_get", return_value={"results": results})

        items = services.ranking_world()

        assert len(items) == 10
        assert 1 not in [it["tmdb_id"] for it in items]
        assert items[0]["tmdb_id"] == 2
        assert items[1]["media_type"] == "tv"

    def test_rankings_handle_missing_results(self, mocker):
        mocker.patch("films.services._tmdb_get", return_value={"results": None})
        assert services.ranking_movies() == []
        assert services.ranking_series() == []
        assert services.ranking_world() == []

    def test_rankings_are_cached(self, mocker):
        mocked = mocker.patch(
            "films.services._tmdb_get",
            return_value={"results": [_movie(1)]},
        )
        services.ranking_movies()
        services.ranking_movies()
        assert mocked.call_count == 1


class TestRankingUpcoming:
    def test_filters_without_poster_and_sorts_by_release_date(self, mocker):
        mocked = mocker.patch(
            "films.services._tmdb_get",
            return_value={
                "results": [
                    _movie(1, poster_path="/a.jpg", release_date="2026-12-20"),
                    _movie(2, poster_path=None, release_date="2026-12-01"),
                    _movie(3, poster_path="/c.jpg"),
                    _movie(4, poster_path="/d.jpg", release_date="2026-12-05"),
                ],
            },
        )
        items = services.ranking_upcoming()

        assert mocked.call_count == 1
        assert mocked.call_args.args[0] == "/discover/movie"
        # Sem data vai para o fim; o item sem pôster some.
        assert [it["tmdb_id"] for it in items] == [4, 1, 3]
        assert [it["rank"] for it in items] == [1, 2, 3]
        assert items[0]["release_date"] == "2026-12-05"
        assert items[2]["release_date"] is None

    def test_falls_back_to_movie_upcoming_when_discover_is_empty(self, mocker):
        def fake_get(path, params=None):
            if path == "/discover/movie":
                # Só itens sem pôster: equivale a vazio depois do filtro.
                return {"results": [_movie(1, poster_path=None)]}
            return {
                "results": [
                    _movie(2, poster_path="/b.jpg", release_date="2026-12-10"),
                    _movie(3, poster_path=None),
                ],
            }

        mocked = mocker.patch("films.services._tmdb_get", side_effect=fake_get)
        items = services.ranking_upcoming()

        assert [c.args[0] for c in mocked.call_args_list] == [
            "/discover/movie",
            "/movie/upcoming",
        ]
        assert [it["tmdb_id"] for it in items] == [2]

    def test_limits_to_ten(self, mocker):
        mocker.patch(
            "films.services._tmdb_get",
            return_value={
                "results": [_movie(i, poster_path="/p.jpg") for i in range(20)],
            },
        )
        assert len(services.ranking_upcoming()) == 10


class TestRankingRatedFallback:
    def test_falls_back_to_tmdb_top_rated_without_ratings(self, db, mocker):
        mocked = mocker.patch(
            "films.services._tmdb_get",
            return_value={
                "results": [_movie(i, vote_average=8.456) for i in range(12)],
            },
        )
        items = services.ranking_rated()

        mocked.assert_called_once_with("/movie/top_rated", {"region": "BR"})
        assert len(items) == 10
        assert items[0]["total_ratings"] == 0
        assert items[0]["rating"] == 8.5
        assert items[0]["source"] == "tmdb"

    def test_rating_without_post_uses_placeholder_title(self, db, user):
        Rating.objects.create(user=user, tmdb_id=42, media_type="tv", score=6)

        item = services.ranking_rated()[0]

        assert item["title"] == "#42"
        assert item["poster_url"] is None


class TestGetRankingErrors:
    def test_tmdb_error_returns_empty_items_and_logs_warning(self, mocker, caplog):
        mocker.patch(
            "films.services._tmdb_get",
            side_effect=services.TMDBError("TMDB 503: /trending/movie/day"),
        )
        with caplog.at_level(logging.WARNING, logger="films.services"):
            data = services.get_ranking("movies")

        assert data == {
            "category": "movies",
            "label": services.RANKINGS["movies"][0],
            "items": [],
        }
        assert "movies" in caplog.text
        assert "TMDB 503" in caplog.text

    def test_tmdb_error_is_not_cached(self, mocker):
        mocked = mocker.patch(
            "films.services._tmdb_get",
            side_effect=[services.TMDBError("fora do ar"), {"results": [_movie(1)]}],
        )
        assert services.get_ranking("movies")["items"] == []
        # A falha não fica no cache: a próxima chamada volta à TMDB.
        assert services.get_ranking("movies")["items"][0]["tmdb_id"] == 1
        assert mocked.call_count == 2
