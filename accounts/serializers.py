from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["display_name", "bio", "avatar"]


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(
        source="profile.display_name_or_username",
        read_only=True,
    )
    bio = serializers.CharField(source="profile.bio", read_only=True)
    avatar_url = serializers.CharField(source="profile.avatar_url", read_only=True)
    followers_count = serializers.IntegerField(
        source="profile.followers_count",
        read_only=True,
    )
    following_count = serializers.IntegerField(
        source="profile.following_count",
        read_only=True,
    )
    posts_count = serializers.IntegerField(source="profile.posts_count", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "display_name",
            "bio",
            "avatar_url",
            "followers_count",
            "following_count",
            "posts_count",
            "date_joined",
        ]
        read_only_fields = fields


class PublicUserSerializer(UserSerializer):
    """Perfil público: os mesmos dados do UserSerializer, sem o e-mail."""

    class Meta(UserSerializer.Meta):
        fields = [
            "id",
            "username",
            "display_name",
            "bio",
            "avatar_url",
            "followers_count",
            "following_count",
            "posts_count",
            "date_joined",
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    display_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "display_name"]

    def validate_username(self, value):
        return value.lstrip("@").strip()

    def create(self, validated_data):
        display_name = validated_data.pop("display_name", "")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        user.profile.display_name = display_name or user.username
        user.profile.save()
        return user


class FollowActionSerializer(serializers.Serializer):
    following = serializers.BooleanField(read_only=True)
    followers_count = serializers.IntegerField(read_only=True)
