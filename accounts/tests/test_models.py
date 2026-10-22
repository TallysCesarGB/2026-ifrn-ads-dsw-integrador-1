import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from accounts.models import Follow
from accounts.models import Profile

User = get_user_model()


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

    def test_cannot_follow_self(self, user):
        with pytest.raises(IntegrityError):
            Follow.objects.create(follower=user, followed=user)
