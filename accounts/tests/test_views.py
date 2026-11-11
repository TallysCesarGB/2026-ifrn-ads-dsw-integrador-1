import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import Follow
from posts.models import Post

User = get_user_model()


@pytest.mark.django_db
class TestAuthView:
    def test_register_creates_user_and_logs_in(self, client):
        url = reverse("accounts:login") + "?mode=register"
        response = client.post(
            url,
            {
                "mode": "register",
                "display_name": "Novo Usuário",
                "username": "novo",
                "email": "novo@example.com",
                "password": "senha123456",
            },
        )
        assert response.status_code == 302
        assert User.objects.filter(username="novo").exists()

    def test_register_rejects_duplicate_username(self, client, user):
        url = reverse("accounts:login") + "?mode=register"
        response = client.post(
            url,
            {
                "mode": "register",
                "username": "tallys",
                "email": "outro@example.com",
                "password": "senha123456",
            },
        )
        assert response.status_code == 200  # re-renderiza com erro
        assert User.objects.filter(username="tallys").count() == 1

    @pytest.mark.parametrize(
        "weak_password",
        ["123", "12345678", "password", "joaozinho123"],
    )
    def test_register_rejects_weak_password(self, client, weak_password):
        url = reverse("accounts:login") + "?mode=register"
        response = client.post(
            url,
            {
                "mode": "register",
                "username": "joaozinho",
                "email": "joaozinho@example.com",
                "password": weak_password,
            },
        )
        assert response.status_code == 200  # re-renderiza com erro
        assert not User.objects.filter(username="joaozinho").exists()

    def test_login_with_correct_credentials(self, client, user):
        url = reverse("accounts:login") + "?mode=login"
        response = client.post(
            url,
            {"mode": "login", "username": user.email, "password": "senha123456"},
        )
        assert response.status_code == 302

    def test_login_with_wrong_password_shows_error(self, client, user):
        url = reverse("accounts:login") + "?mode=login"
        response = client.post(
            url,
            {"mode": "login", "username": user.email, "password": "errada"},
        )
        assert response.status_code == 200

    def test_logged_in_user_redirected_away_from_auth_page(self, auth_client):
        response = auth_client.get(reverse("accounts:login"))
        assert response.status_code == 302

    def test_logout(self, auth_client):
        response = auth_client.post(reverse("accounts:logout"))
        assert response.status_code == 302


@pytest.mark.django_db
class TestProfileView:
    def test_requires_login(self, client, user):
        url = reverse("accounts:profile", kwargs={"username": user.username})
        response = client.get(url)
        assert response.status_code == 302  # redireciona para login

    def test_own_profile_shows_edit_option(self, auth_client, user):
        url = reverse("accounts:profile", kwargs={"username": user.username})
        response = auth_client.get(url)
        assert response.status_code == 200
        assert b"Editar perfil" in response.content

    def test_other_profile_shows_follow_button(self, auth_client, other_user):
        url = reverse("accounts:profile", kwargs={"username": other_user.username})
        response = auth_client.get(url)
        assert response.status_code == 200
        assert b"Seguir" in response.content

    def test_own_profile_no_longer_has_user_search(self, auth_client, user):
        """#41: a busca de usuários saiu do perfil e foi para o feed."""
        url = reverse("accounts:profile", kwargs={"username": user.username})
        html = auth_client.get(url).content.decode()

        assert 'id="userSearchInput"' not in html
        assert "Buscar usuários" not in html

    def test_profile_shows_users_posts(self, auth_client, user, post):
        url = reverse("accounts:profile", kwargs={"username": user.username})
        response = auth_client.get(url)
        assert post.title.encode() in response.content

    def test_edit_own_profile(self, auth_client, user):
        url = reverse("accounts:profile", kwargs={"username": user.username})
        response = auth_client.post(
            url,
            {"display_name": "Tallys Editado", "bio": "Bio nova"},
        )
        assert response.status_code == 302
        user.profile.refresh_from_db()
        assert user.profile.display_name == "Tallys Editado"
        assert user.profile.bio == "Bio nova"


@pytest.mark.django_db
class TestFollowToggle:
    def test_follow_and_unfollow(self, auth_client, user, other_user):
        url = reverse("accounts:toggle_follow", kwargs={"user_id": other_user.id})

        response = auth_client.post(url)
        assert response.status_code == 200
        assert response.json()["following"] is True
        assert Follow.objects.filter(follower=user, followed=other_user).exists()

        response = auth_client.post(url)
        assert response.status_code == 200
        assert response.json()["following"] is False
        assert not Follow.objects.filter(follower=user, followed=other_user).exists()

    def test_cannot_follow_self(self, auth_client, user):
        url = reverse("accounts:toggle_follow", kwargs={"user_id": user.id})
        response = auth_client.post(url)
        assert response.status_code == 400


@pytest.mark.django_db
class TestUserSearch:
    def test_search_by_username(self, auth_client, other_user):
        url = reverse("accounts:search_users") + "?q=mar"
        response = auth_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert any(u["username"] == "maria" for u in data)

    def test_search_requires_min_length(self, auth_client):
        url = reverse("accounts:search_users") + "?q=m"
        response = auth_client.get(url)
        assert response.json() == []


@pytest.mark.django_db
class TestProfileTabs:
    """#62: abas Todos / Filmes / Séries na grade do perfil."""

    @pytest.fixture
    def indicacoes(self, user):
        return {
            "matrix": Post.objects.create(
                user=user,
                tmdb_id=603,
                media_type="movie",
                title="Matrix",
            ),
            "duna": Post.objects.create(
                user=user,
                tmdb_id=438631,
                media_type="movie",
                title="Duna",
            ),
            "dark": Post.objects.create(
                user=user,
                tmdb_id=70523,
                media_type="tv",
                title="Dark",
            ),
        }

    def _get(self, client, user, tipo=None):
        url = reverse("accounts:profile", kwargs={"username": user.username})
        return client.get(url, {"tipo": tipo} if tipo else {})

    def test_defaults_to_all_posts(self, auth_client, user, indicacoes):
        response = self._get(auth_client, user)

        assert response.context["active_tab"] == "todos"
        assert set(response.context["posts"]) == set(indicacoes.values())

    @pytest.mark.parametrize(
        ("tipo", "esperados"),
        [("filmes", {"matrix", "duna"}), ("series", {"dark"})],
    )
    def test_filters_by_media_type(
        self,
        auth_client,
        user,
        indicacoes,
        tipo,
        esperados,
    ):
        response = self._get(auth_client, user, tipo)

        assert response.context["active_tab"] == tipo
        assert set(response.context["posts"]) == {indicacoes[k] for k in esperados}

    def test_counts_are_shown_in_every_tab(self, auth_client, user, indicacoes):
        response = self._get(auth_client, user, "series")

        assert response.context["tab_counts"] == {"todos": 3, "filmes": 2, "series": 1}

    def test_invalid_tab_falls_back_to_all(self, auth_client, user, indicacoes):
        response = self._get(auth_client, user, "banana")

        assert response.context["active_tab"] == "todos"
        assert len(response.context["posts"]) == len(indicacoes)

    def test_active_tab_is_marked_for_screen_readers(self, auth_client, user):
        html = self._get(auth_client, user, "filmes").content.decode()

        assert html.count('aria-current="page"') == 1
        assert 'href="/accounts/perfil/tallys/?tipo=filmes"' in html

    def test_series_badge_only_in_all_tab(self, auth_client, user, indicacoes):
        todos = self._get(auth_client, user).content.decode()
        series = self._get(auth_client, user, "series").content.decode()

        assert todos.count('class="post-grid-badge"') == 1
        assert 'class="post-grid-badge"' not in series

    def test_empty_tab_has_its_own_message(self, auth_client, user):
        Post.objects.create(user=user, tmdb_id=603, media_type="movie", title="Matrix")

        html = self._get(auth_client, user, "series").content.decode()

        assert "Nenhuma série indicada ainda." in html
