import pytest
from django.urls import reverse

from ratings.models import Rating


@pytest.mark.django_db
class TestRateView:
    def test_requires_login(self, client):
        response = client.post(
            reverse("ratings:rate"),
            {"tmdb_id": 603, "media_type": "movie", "score": 9},
        )
        assert response.status_code == 302

    def test_create_rating(self, auth_client, user):
        response = auth_client.post(
            reverse("ratings:rate"),
            {"tmdb_id": 603, "media_type": "movie", "score": 9},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["average"] == 9.0
        assert Rating.objects.filter(user=user, tmdb_id=603, score=9).exists()

    def test_update_existing_rating(self, auth_client, user):
        Rating.objects.create(user=user, tmdb_id=603, media_type="movie", score=5)
        auth_client.post(
            reverse("ratings:rate"),
            {"tmdb_id": 603, "media_type": "movie", "score": 10},
        )
        assert Rating.objects.filter(user=user, tmdb_id=603).count() == 1
        assert Rating.objects.get(user=user, tmdb_id=603).score == 10

    def test_score_out_of_range_rejected(self, auth_client):
        response = auth_client.post(
            reverse("ratings:rate"),
            {"tmdb_id": 603, "media_type": "movie", "score": 15},
        )
        assert response.status_code == 400

    def test_invalid_params_rejected(self, auth_client):
        response = auth_client.post(
            reverse("ratings:rate"),
            {"tmdb_id": "abc", "media_type": "movie", "score": 9},
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("media_type", ["banana", "xpto", ""])
    def test_invalid_media_type_rejected(self, auth_client, media_type):
        response = auth_client.post(
            reverse("ratings:rate"),
            {"tmdb_id": 603, "media_type": media_type, "score": 9},
        )
        assert response.status_code == 400
        assert "media_type" in response.json()["fields"]
        assert not Rating.objects.exists()

    def test_media_type_defaults_to_movie(self, auth_client, user):
        response = auth_client.post(
            reverse("ratings:rate"),
            {"tmdb_id": 603, "score": 7},
        )
        assert response.status_code == 200
        assert Rating.objects.get(user=user, tmdb_id=603).media_type == "movie"

    def test_tv_rating_accepted(self, auth_client, user):
        response = auth_client.post(
            reverse("ratings:rate"),
            {"tmdb_id": 1399, "media_type": "tv", "score": 8},
        )
        assert response.status_code == 200
        assert Rating.objects.filter(user=user, tmdb_id=1399, media_type="tv").exists()

    @pytest.mark.parametrize("score", [0, -1, 11])
    def test_score_outside_1_to_10_rejected(self, auth_client, score):
        response = auth_client.post(
            reverse("ratings:rate"),
            {"tmdb_id": 603, "media_type": "movie", "score": score},
        )
        assert response.status_code == 400
        assert not Rating.objects.exists()

    @pytest.mark.parametrize("score", [1, 10])
    def test_score_limits_accepted(self, auth_client, score):
        response = auth_client.post(
            reverse("ratings:rate"),
            {"tmdb_id": 603, "media_type": "movie", "score": score},
        )
        assert response.status_code == 200
        assert response.json()["my_score"] == score

    def test_missing_score_rejected(self, auth_client):
        response = auth_client.post(
            reverse("ratings:rate"),
            {"tmdb_id": 603, "media_type": "movie"},
        )
        assert response.status_code == 400
