import pytest
from django.urls import reverse

from films import services
from films.tests.test_views import FAKE_FILM, FAKE_RANKING


@pytest.mark.django_db
class TestFilmSearchAPI:
    def test_search_is_public(self, api_client, mocker):
        mocker.patch("films.services.search", return_value=[
            {"tmdb_id": 603, "media_type": "movie", "title": "Matrix", "year": "1999", "poster_url": None, "rating": 8.7, "overview": "..."}
        ])
        response = api_client.get(reverse("api-film-search") + "?q=matrix")
        assert response.status_code == 200
        assert response.data[0]["title"] == "Matrix"

    def test_search_requires_min_length(self, api_client):
        response = api_client.get(reverse("api-film-search") + "?q=m")
        assert response.status_code == 400


@pytest.mark.django_db
class TestFilmDetailAPI:
    def test_detail_is_public(self, api_client, mocker):
        mocker.patch("films.services.get_detail", return_value=FAKE_FILM)
        response = api_client.get(reverse("api-film-detail", kwargs={"media_type": "movie", "tmdb_id": 603}))
        assert response.status_code == 200
        assert response.data["title"] == "Matrix"

    def test_detail_404_on_tmdb_error(self, api_client, mocker):
        mocker.patch("films.services.get_detail", side_effect=services.TMDBError("erro"))
        response = api_client.get(reverse("api-film-detail", kwargs={"media_type": "movie", "tmdb_id": 999999}))
        assert response.status_code == 404


@pytest.mark.django_db
class TestRankingAPI:
    def test_valid_category(self, api_client, mocker):
        mocker.patch("films.services.get_ranking", return_value=FAKE_RANKING)
        response = api_client.get(reverse("api-film-rankings", kwargs={"category": "movies"}))
        assert response.status_code == 200
        assert response.data["category"] == "movies"

    def test_invalid_category(self, api_client, mocker):
        mocker.patch("films.services.get_ranking", side_effect=ValueError())
        response = api_client.get(reverse("api-film-rankings", kwargs={"category": "x"}))
        assert response.status_code == 404


@pytest.mark.django_db
class TestStreamingAPI:
    def test_streaming_is_public(self, api_client, mocker):
        mocker.patch("films.services.get_streaming", return_value={"stream": [], "rent": [], "buy": []})
        response = api_client.get(reverse("api-streaming", kwargs={"media_type": "movie", "tmdb_id": 603}))
        assert response.status_code == 200
