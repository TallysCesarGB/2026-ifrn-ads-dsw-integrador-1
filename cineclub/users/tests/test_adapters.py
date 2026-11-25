import pytest
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.test import RequestFactory

from cineclub.users.adapters import AccountAdapter
from cineclub.users.adapters import SocialAccountAdapter
from cineclub.users.models import User


@pytest.fixture
def request_():
    return RequestFactory().get("/")


class TestIsOpenForSignup:
    @pytest.mark.parametrize("allowed", [True, False])
    def test_account_adapter_follows_setting(self, settings, request_, allowed):
        settings.ACCOUNT_ALLOW_REGISTRATION = allowed
        assert AccountAdapter().is_open_for_signup(request_) is allowed

    @pytest.mark.parametrize("allowed", [True, False])
    def test_social_adapter_follows_setting(self, settings, request_, allowed):
        settings.ACCOUNT_ALLOW_REGISTRATION = allowed
        adapter = SocialAccountAdapter()
        assert adapter.is_open_for_signup(request_, sociallogin=None) is allowed


class TestPopulateUser:
    @pytest.fixture
    def populate(self, mocker, request_):
        """Chama populate_user com o super() devolvendo um User sem `name`."""

        def _populate(data, name=""):
            mocker.patch.object(
                DefaultSocialAccountAdapter,
                "populate_user",
                return_value=User(name=name),
            )
            return SocialAccountAdapter().populate_user(request_, None, data)

        return _populate

    def test_uses_name_from_provider(self, populate):
        user = populate({"name": "Ana Souza", "first_name": "Outro"})
        assert user.name == "Ana Souza"

    def test_builds_name_from_first_and_last_name(self, populate):
        user = populate({"first_name": "Ana", "last_name": "Souza"})
        assert user.name == "Ana Souza"

    def test_first_name_only(self, populate):
        user = populate({"first_name": "Ana"})
        assert user.name == "Ana"

    def test_no_name_data_keeps_empty(self, populate):
        user = populate({})
        assert user.name == ""

    def test_keeps_name_already_set(self, populate):
        user = populate({"name": "Outro Nome"}, name="Já Definido")
        assert user.name == "Já Definido"
