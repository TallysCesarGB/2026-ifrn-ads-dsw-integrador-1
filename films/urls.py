from django.urls import path

from . import views

app_name = "films"

urlpatterns = [
    path("buscar/", views.search_json, name="search_json"),
    path("rankings/<str:category>/", views.rankings_json, name="rankings_json"),
    path("<str:media_type>/<int:tmdb_id>/", views.film_detail, name="detail"),
]
