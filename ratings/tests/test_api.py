import pytest
from django.urls import reverse

from ratings.models import Rating


@pytest.mark.django_db
class TestRatingAPI:
    def test_create_requires_auth(self, api_client):
        response = api_client.post(
            reverse("api-rating-create"),
            {"tmdb_id": 603, "media_type": "movie", "score": 9},
        )
        assert response.status_code == 401

    def test_create_rating(self, api_auth_client, user):
        response = api_auth_client.post(
            reverse("api-rating-create"),
            {"tmdb_id": 603, "media_type": "movie", "score": 9},
        )
        assert response.status_code == 200
        assert response.data["average"] == 9.0
        assert Rating.objects.filter(user=user, tmdb_id=603).exists()

    def test_score_out_of_range_rejected(self, api_auth_client):
        response = api_auth_client.post(
            reverse("api-rating-create"),
            {"tmdb_id": 603, "media_type": "movie", "score": 15},
        )
        assert response.status_code == 400

    def test_summary_is_public(self, api_client, user):
        Rating.objects.create(user=user, tmdb_id=603, media_type="movie", score=8)
        url = (
            reverse("api-rating-summary", kwargs={"tmdb_id": 603}) + "?media_type=movie"
        )
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["average"] == 8.0
        assert response.data["total"] == 1

    def test_my_rating_requires_auth(self, api_client):
        url = reverse("api-rating-me", kwargs={"tmdb_id": 603})
        response = api_client.get(url)
        assert response.status_code == 401

    def test_my_rating_returns_null_when_not_rated(self, api_auth_client):
        url = reverse("api-rating-me", kwargs={"tmdb_id": 603}) + "?media_type=movie"
        response = api_auth_client.get(url)
        assert response.status_code == 200
        assert response.data["score"] is None

    @pytest.mark.parametrize("score", [0, 11])
    def test_score_outside_1_to_10_rejected(self, api_auth_client, score):
        response = api_auth_client.post(
            reverse("api-rating-create"),
            {"tmdb_id": 603, "media_type": "movie", "score": score},
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("media_type", ["banana", "xpto"])
    def test_create_invalid_media_type_rejected(self, api_auth_client, media_type):
        response = api_auth_client.post(
            reverse("api-rating-create"),
            {"tmdb_id": 603, "media_type": media_type, "score": 9},
        )
        assert response.status_code == 400
        assert "media_type" in response.data

    @pytest.mark.parametrize("media_type", ["banana", "xpto"])
    def test_summary_invalid_media_type_rejected(self, api_client, media_type):
        url = reverse("api-rating-summary", kwargs={"tmdb_id": 603})
        response = api_client.get(url, {"media_type": media_type})
        assert response.status_code == 400
        assert "media_type" in response.data

    def test_summary_media_type_defaults_to_movie(self, api_client, user):
        Rating.objects.create(user=user, tmdb_id=603, media_type="movie", score=6)
        url = reverse("api-rating-summary", kwargs={"tmdb_id": 603})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["total"] == 1

    @pytest.mark.parametrize("media_type", ["banana", "xpto"])
    def test_my_rating_invalid_media_type_rejected(self, api_auth_client, media_type):
        url = reverse("api-rating-me", kwargs={"tmdb_id": 603})
        response = api_auth_client.get(url, {"media_type": media_type})
        assert response.status_code == 400
        assert "media_type" in response.data
