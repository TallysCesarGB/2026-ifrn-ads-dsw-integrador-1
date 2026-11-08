import pytest
from django.db import IntegrityError

from ratings.models import Rating


@pytest.mark.django_db
class TestRating:
    def test_average_for_no_ratings(self):
        average, total = Rating.average_for(999, "movie")
        assert average == 0
        assert total == 0

    def test_average_for_single_rating(self, user):
        Rating.objects.create(user=user, tmdb_id=603, media_type="movie", score=9)
        average, total = Rating.average_for(603, "movie")
        assert average == 9
        assert total == 1

    def test_average_for_multiple_ratings(self, user, other_user):
        Rating.objects.create(user=user, tmdb_id=603, media_type="movie", score=8)
        Rating.objects.create(user=other_user, tmdb_id=603, media_type="movie", score=10)
        average, total = Rating.average_for(603, "movie")
        assert average == 9.0
        assert total == 2

    def test_user_cannot_rate_same_film_twice(self, user):
        Rating.objects.create(user=user, tmdb_id=603, media_type="movie", score=8)
        with pytest.raises(IntegrityError):
            Rating.objects.create(user=user, tmdb_id=603, media_type="movie", score=9)
