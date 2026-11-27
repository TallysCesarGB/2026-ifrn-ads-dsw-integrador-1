from rest_framework import serializers

from posts.models import MEDIA_TYPE_CHOICES

from .models import Rating


class RatingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ["tmdb_id", "media_type", "score"]


class MediaTypeQuerySerializer(serializers.Serializer):
    """Valida o ?media_type= dos GETs de avaliação."""

    media_type = serializers.ChoiceField(choices=MEDIA_TYPE_CHOICES, default="movie")


class RatingSummarySerializer(serializers.Serializer):
    average = serializers.FloatField()
    total = serializers.IntegerField()


class MyRatingSerializer(serializers.Serializer):
    score = serializers.IntegerField(allow_null=True)
