"""Usuários sem Profile (#60)."""

import importlib

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.urls import reverse

from accounts.models import Profile
from posts.models import Comment
from posts.models import Post

User = get_user_model()

migration = importlib.import_module("accounts.migrations.0002_create_missing_profiles")


def _create_missing_profiles():
    with connection.schema_editor() as schema_editor:
        migration.create_missing_profiles(apps, schema_editor)


@pytest.fixture
def user_without_profile(db):
    """Simula um usuário que já existia antes do app `accounts`."""
    user = User.objects.create_user("antigo", "antigo@ifrn.edu.br", "senha123456")
    Profile.objects.filter(user=user).delete()
    return User.objects.get(pk=user.pk)


@pytest.mark.django_db
class TestCreateMissingProfilesMigration:
    def test_creates_profile_for_users_without_one(self, user_without_profile):
        _create_missing_profiles()

        assert Profile.objects.filter(user=user_without_profile).exists()

    def test_keeps_existing_profiles_and_is_idempotent(
        self,
        user,
        user_without_profile,
    ):
        user.profile.bio = "Bio que não pode sumir"
        user.profile.save()

        _create_missing_profiles()
        _create_missing_profiles()

        user.profile.refresh_from_db()
        assert user.profile.bio == "Bio que não pode sumir"
        assert Profile.objects.count() == User.objects.count()


@pytest.mark.django_db
class TestProfileSignal:
    def test_recreates_missing_profile_on_next_save(self, user_without_profile):
        user_without_profile.save()

        assert Profile.objects.filter(user=user_without_profile).exists()

    def test_login_restores_missing_profile(self, client, user_without_profile):
        assert client.login(username="antigo", password="senha123456")

        assert Profile.objects.filter(user=user_without_profile).exists()

    def test_loaddata_uses_the_fixture_profiles(self):
        """Saves raw não criam perfil: a fixture traz os seus."""
        call_command("loaddata", "fixtures/demo_data.json", verbosity=0)

        demo = User.objects.get(username="demo")
        assert demo.profile.display_name == "Usuário Demo"
        assert Profile.objects.count() == User.objects.count()


@pytest.mark.django_db
class TestPagesAfterRepair:
    """Rotas que davam 500 com um usuário sem perfil."""

    def test_pages_work_after_migration(self, auth_client, user_without_profile):
        post = Post.objects.create(
            user=user_without_profile,
            tmdb_id=1,
            media_type="movie",
            title="Matrix",
        )
        Comment.objects.create(post=post, user=user_without_profile, content="oi")

        _create_missing_profiles()

        profile_url = reverse("accounts:profile", args=[user_without_profile.username])
        follow_url = reverse("accounts:toggle_follow", args=[user_without_profile.id])
        comments_url = reverse("posts:list_comments", args=[post.id])
        assert auth_client.get(profile_url).status_code == 200
        assert auth_client.get(reverse("accounts:search_users") + "?q=antigo").json()
        assert auth_client.post(follow_url).status_code == 200
        assert auth_client.get(comments_url).status_code == 200
