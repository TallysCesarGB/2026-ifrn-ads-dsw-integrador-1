from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.auth_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("perfil/<str:username>/", views.profile_view, name="profile"),
    path("seguir/<int:user_id>/", views.toggle_follow, name="toggle_follow"),
    path("buscar/", views.search_users, name="search_users"),
]
