from django.urls import path

from . import api

urlpatterns = [
    path("films/search/", api.FilmSearchView.as_view(), name="api-film-search"),
    path("films/rankings/<str:category>/", api.RankingView.as_view(), name="api-film-rankings"),
    path("films/<str:media_type>/<int:tmdb_id>/", api.FilmDetailView.as_view(), name="api-film-detail"),
    path("streaming/<str:media_type>/<int:tmdb_id>/", api.StreamingView.as_view(), name="api-streaming"),
]
