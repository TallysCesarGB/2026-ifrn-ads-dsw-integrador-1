import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.urls import reverse

from accounts.models import Follow
from accounts.models import Profile
from accounts.models import avatar_upload_to

User = get_user_model()

# GIF 1x1 transparente, suficiente para o ImageField validar o arquivo.
GIF_1PX = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
    b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
    b"\x00\x02\x02D\x01\x00;"
)


@pytest.mark.django_db
class TestProfile:
    def test_profile_is_created_automatically_via_signal(self):
        u = User.objects.create_user(
            username="joao",
            email="joao@example.com",
            password="12345678",
        )
        assert Profile.objects.filter(user=u).exists()

    def test_display_name_or_username_fallback(self, user):
        user.profile.display_name = ""
        user.profile.save()
        assert user.profile.display_name_or_username == "tallys"

    def test_avatar_url_fallback_to_dicebear(self, user):
        assert "dicebear.com" in user.profile.avatar_url
        assert "tallys" in user.profile.avatar_url

    def test_str_is_username(self, user):
        assert str(user.profile) == "tallys"

    def test_get_absolute_url(self, user):
        assert user.profile.get_absolute_url() == reverse(
            "accounts:profile",
            kwargs={"username": "tallys"},
        )

    def test_avatar_upload_to_uses_user_id(self, user):
        path = avatar_upload_to(user.profile, "foto.png")
        assert path == f"avatars/{user.id}/foto.png"

    def test_avatar_url_with_uploaded_avatar(self, user, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        settings.MEDIA_URL = "/media/"
        user.profile.avatar = SimpleUploadedFile(
            "foto.gif",
            GIF_1PX,
            content_type="image/gif",
        )
        user.profile.save()

        assert user.profile.avatar_url == f"/media/avatars/{user.id}/foto.gif"
        assert (tmp_path / "avatars" / str(user.id) / "foto.gif").exists()

    def test_counts_start_at_zero(self, user):
        assert user.profile.followers_count == 0
        assert user.profile.following_count == 0
        assert user.profile.posts_count == 0

    def test_posts_count_reflects_created_posts(self, user, post):
        assert user.profile.posts_count == 1


@pytest.mark.django_db
class TestFollow:
    def test_follow_creates_relationship(self, user, other_user):
        Follow.objects.create(follower=user, followed=other_user)
        assert user.profile.following_count == 1
        assert other_user.profile.followers_count == 1

    def test_cannot_follow_twice(self, user, other_user):
        Follow.objects.create(follower=user, followed=other_user)
        with pytest.raises(IntegrityError):
            Follow.objects.create(follower=user, followed=other_user)

    def test_str_representation(self, user, other_user):
        follow = Follow.objects.create(follower=user, followed=other_user)
        assert str(follow) == "tallys → maria"

    def test_cannot_follow_self(self, user):
        with pytest.raises(IntegrityError):
            Follow.objects.create(follower=user, followed=user)
