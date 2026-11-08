from rest_framework import serializers

from .models import Rating


class RatingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ["tmdb_id", "media_type", "score"]


class RatingSummarySerializer(serializers.Serializer):
    average = serializers.FloatField()
    total = serializers.IntegerField()


class MyRatingSerializer(serializers.Serializer):
    score = serializers.IntegerField(allow_null=True)
