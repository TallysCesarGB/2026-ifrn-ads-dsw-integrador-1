from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenVerifyView

from . import api

urlpatterns = [
    path("register/", api.RegisterView.as_view(), name="api-register"),
    path("token/", api.LoginView.as_view(), name="api-token-obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="api-token-verify"),
    path("me/", api.MeView.as_view(), name="api-me"),
]
