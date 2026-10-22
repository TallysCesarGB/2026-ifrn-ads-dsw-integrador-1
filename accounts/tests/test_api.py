import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestRegisterAPI:
    def test_register_success(self, api_client):
        url = reverse("api-register")
        response = api_client.post(
            url,
            {
                "username": "novo_api",
                "email": "novo_api@example.com",
                "password": "SenhaForte123",
                "display_name": "Novo API",
            },
        )
        assert response.status_code == 201
        assert User.objects.filter(username="novo_api").exists()

    def test_register_weak_password_rejected(self, api_client):
        url = reverse("api-register")
        response = api_client.post(
            url,
            {"username": "fraco", "email": "fraco@example.com", "password": "123"},
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestLoginAPI:
    def test_login_returns_jwt_pair(self, api_client, user):
        url = reverse("api-token-obtain")
        response = api_client.post(
            url,
            {"email": user.email, "password": "senha123456"},
        )
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["username"] == user.username

    def test_login_wrong_password(self, api_client, user):
        url = reverse("api-token-obtain")
        response = api_client.post(url, {"email": user.email, "password": "errada"})
        assert response.status_code == 401


@pytest.mark.django_db
class TestMeAPI:
    def test_me_requires_auth(self, api_client):
        response = api_client.get(reverse("api-me"))
        assert response.status_code == 401

    def test_me_returns_current_user(self, api_auth_client, user):
        response = api_auth_client.get(reverse("api-me"))
        assert response.status_code == 200
        assert response.data["username"] == user.username


@pytest.mark.django_db
class TestFollowAPI:
    def test_follow_via_api(self, api_auth_client, other_user):
        url = reverse("api-follow-toggle", kwargs={"user_id": other_user.id})
        response = api_auth_client.post(url)
        assert response.status_code == 200
        assert response.data["following"] is True

        response = api_auth_client.delete(url)
        assert response.status_code == 200
        assert response.data["following"] is False


@pytest.mark.django_db
class TestUserSearchAPI:
    def test_search_users(self, api_client, other_user):
        url = reverse("api-user-search") + "?q=maria"
        response = api_client.get(url)
        assert response.status_code == 200
        usernames = [u["username"] for u in response.data["results"]]
        assert "maria" in usernames


@pytest.mark.django_db
class TestPublicUserPrivacy:
    def test_user_detail_hides_email(self, api_client, other_user):
        url = reverse("api-user-detail", kwargs={"username": other_user.username})
        response = api_client.get(url)
        assert response.status_code == 200
        assert "email" not in response.data

    def test_user_search_hides_email(self, api_client, other_user):
        response = api_client.get(reverse("api-user-search") + "?q=maria")
        assert response.status_code == 200
        assert response.data["results"]
        assert all("email" not in u for u in response.data["results"])

    def test_me_still_returns_own_email(self, api_auth_client, user):
        response = api_auth_client.get(reverse("api-me"))
        assert response.data["email"] == user.email
