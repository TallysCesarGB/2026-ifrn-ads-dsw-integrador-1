from django.conf import settings
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Avg
from django.db.models import Count

from posts.models import MEDIA_TYPE_CHOICES

MIN_SCORE = 0
MAX_SCORE = 10


class Rating(models.Model):
    """Nota (0-10) que um usuário dá a um filme/série (por tmdb_id)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    tmdb_id = models.PositiveIntegerField()
    media_type = models.CharField(
        max_length=5,
        choices=MEDIA_TYPE_CHOICES,
        default="movie",
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_SCORE), MaxValueValidator(MAX_SCORE)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "tmdb_id", "media_type"],
                name="unique_rating_per_user",
            ),
        ]
        indexes = [models.Index(fields=["tmdb_id", "media_type"])]

    def __str__(self):
        return (
            f"{self.user.username} avaliou {self.tmdb_id} "
            f"({self.media_type}) com {self.score}"
        )

    @classmethod
    def average_for(cls, tmdb_id, media_type="movie"):
        agg = cls.objects.filter(tmdb_id=tmdb_id, media_type=media_type).aggregate(
            average=Avg("score"),
            total=Count("id"),
        )
        average = round(agg["average"], 1) if agg["average"] else 0
        return average, agg["total"] or 0
