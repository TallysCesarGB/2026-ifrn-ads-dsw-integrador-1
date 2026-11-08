from rest_framework import serializers


class FilmSearchResultSerializer(serializers.Serializer):
    tmdb_id = serializers.IntegerField()
    media_type = serializers.ChoiceField(choices=["movie", "tv"])
    title = serializers.CharField()
    year = serializers.CharField(allow_blank=True)
    poster_url = serializers.CharField(allow_null=True)
    rating = serializers.FloatField(allow_null=True)
    overview = serializers.CharField(allow_blank=True, allow_null=True)


class StreamingLinkSerializer(serializers.Serializer):
    provider_id = serializers.IntegerField()
    name = serializers.CharField()
    emoji = serializers.CharField()
    kind = serializers.CharField()
    logo_url = serializers.CharField(allow_null=True)
    web_link = serializers.CharField()


class StreamingSerializer(serializers.Serializer):
    stream = StreamingLinkSerializer(many=True)
    rent = StreamingLinkSerializer(many=True)
    buy = StreamingLinkSerializer(many=True)


class CastMemberSerializer(serializers.Serializer):
    name = serializers.CharField()
    character = serializers.CharField(allow_null=True, allow_blank=True)
    photo_url = serializers.CharField(allow_null=True)


class TrailerSerializer(serializers.Serializer):
    key = serializers.CharField()
    url = serializers.CharField()


class FilmDetailSerializer(serializers.Serializer):
    tmdb_id = serializers.IntegerField()
    media_type = serializers.ChoiceField(choices=["movie", "tv"])
    title = serializers.CharField()
    tagline = serializers.CharField(allow_blank=True)
    overview = serializers.CharField(allow_null=True, allow_blank=True)
    poster_url = serializers.CharField(allow_null=True)
    backdrop_url = serializers.CharField(allow_null=True)
    rating = serializers.FloatField(allow_null=True)
    vote_count = serializers.IntegerField(allow_null=True)
    runtime = serializers.IntegerField(allow_null=True)
    release_date = serializers.CharField(allow_null=True)
    genres = serializers.ListField(child=serializers.CharField())
    seasons = serializers.IntegerField(allow_null=True)
    trailer = TrailerSerializer(allow_null=True)
    cast = CastMemberSerializer(many=True)
    directors = serializers.ListField(child=serializers.CharField())
    streaming = StreamingSerializer()


class RankingItemSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    tmdb_id = serializers.IntegerField()
    media_type = serializers.ChoiceField(choices=["movie", "tv"])
    title = serializers.CharField()
    overview = serializers.CharField(allow_null=True, allow_blank=True)
    poster_url = serializers.CharField(allow_null=True)
    backdrop_url = serializers.CharField(allow_null=True)
    rating = serializers.FloatField()
    year = serializers.CharField(allow_null=True, allow_blank=True)
    source = serializers.CharField()


class RankingSerializer(serializers.Serializer):
    category = serializers.CharField()
    label = serializers.CharField()
    items = RankingItemSerializer(many=True)
