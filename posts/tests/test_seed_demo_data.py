import sys
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse

from accounts.models import Follow
from posts.models import Comment
from posts.models import Like
from posts.models import Post
from ratings.models import Rating

User = get_user_model()


def seed(seed=42, **options):
    out = StringIO()
    call_command("seed_demo_data", stdout=out, seed=seed, **options)
    return out.getvalue()


@pytest.mark.django_db
class TestSeedDemoData:
    def test_creates_demo_data(self):
        output = seed(users=3, posts=5)

        # 3 fictícios + o usuário demo
        assert User.objects.count() == 4
        assert Post.objects.count() == 5
        assert Follow.objects.exists()
        assert Rating.objects.exists()
        assert Like.objects.exists()
        assert Comment.objects.exists()
        assert "Seed concluído" in output

    def test_demo_user_exists_and_can_log_in(self, client):
        seed(users=3, posts=5)

        demo = User.objects.get(email="demo@cineclub.com")
        assert demo.profile.display_name == "Usuário Demo"

        response = client.post(
            reverse("accounts:login"),
            {
                "mode": "login",
                "username": "demo@cineclub.com",
                "password": "cineclub123",
            },
        )
        assert response.status_code == 302
        assert response.url == reverse("posts:feed")

    def test_reset_does_not_duplicate(self):
        seed(users=3, posts=5)
        output = seed(users=3, posts=5, reset=True)

        assert "Removendo dados de demonstração" in output
        assert User.objects.count() == 4
        assert User.objects.filter(email="demo@cineclub.com").count() == 1
        assert Post.objects.count() == 5

    def test_reset_keeps_superusers(self):
        User.objects.create_superuser("admin", "admin@example.com", "senha123456")
        seed(users=2, posts=2, reset=True)
        assert User.objects.filter(username="admin").exists()

    def test_rerun_without_reset_reuses_demo_user(self):
        seed(users=2, posts=2)
        # outra seed: a mesma geraria os mesmos usernames fictícios
        output = seed(users=2, posts=2, seed=7)
        assert User.objects.filter(username="demo").count() == 1
        assert "Usuário de demonstração criado" not in output

    def test_without_faker_prints_error(self, mocker):
        mocker.patch.dict(sys.modules, {"faker": None})
        err = StringIO()
        call_command("seed_demo_data", stderr=err)
        assert "Faker" in err.getvalue()
        assert not User.objects.exists()
