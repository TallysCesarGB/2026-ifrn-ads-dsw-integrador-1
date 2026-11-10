from rest_framework import serializers

from .models import Comment
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    avatar_url = serializers.CharField(source="user.profile.avatar_url", read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "username",
            "avatar_url",
            "tmdb_id",
            "media_type",
            "title",
            "poster_url",
            "comment",
            "likes_count",
            "comments_count",
            "is_liked",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    avatar_url = serializers.CharField(source="user.profile.avatar_url", read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "post",
            "user",
            "username",
            "avatar_url",
            "content",
            "created_at",
        ]
        read_only_fields = ["id", "post", "user", "created_at"]


class LikeActionSerializer(serializers.Serializer):
    liked = serializers.BooleanField()
    likes_count = serializers.IntegerField()


class RecommendActionSerializer(serializers.Serializer):
    ok = serializers.BooleanField(default=True)
