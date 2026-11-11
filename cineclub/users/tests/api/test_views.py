from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIClient
from rest_framework.test import APIRequestFactory

from cineclub.users.api.views import UserViewSet
from cineclub.users.tests.factories import UserFactory

if TYPE_CHECKING:
    from cineclub.users.models import User


class TestUserViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    def test_get_queryset(self, user: User, api_rf: APIRequestFactory):
        view = UserViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert user in view.get_queryset()

    def test_me(self, user: User, api_rf: APIRequestFactory):
        view = UserViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        response = view.me(request)  # type: ignore[misc,call-arg,arg-type]

        assert response.data == {
            "username": user.username,
            "url": f"http://testserver/api/users/{user.username}/",
            "name": user.name,
        }


class TestUserViewSetPermissions:
    """Regressão #42: acesso anônimo retornava 500 (AssertionError)."""

    @pytest.mark.parametrize(
        ("method", "url"),
        [
            ("get", "/api/users/"),
            ("get", "/api/users/me/"),
            ("get", "/api/users/qualquer/"),
            ("patch", "/api/users/qualquer/"),
        ],
    )
    def test_anonymous_is_rejected(self, db, method: str, url: str):
        response = getattr(APIClient(), method)(url)

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_list_only_returns_the_authenticated_user(self, user: User):
        UserFactory()
        client = APIClient()
        client.force_authenticate(user)

        response = client.get("/api/users/")

        assert response.status_code == HTTPStatus.OK
        assert [u["username"] for u in response.data["results"]] == [user.username]
