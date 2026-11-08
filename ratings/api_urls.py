from django.urls import path

from . import api

urlpatterns = [
    path("ratings/", api.RatingCreateView.as_view(), name="api-rating-create"),
    path("ratings/<int:tmdb_id>/", api.RatingSummaryView.as_view(), name="api-rating-summary"),
    path("ratings/<int:tmdb_id>/me/", api.MyRatingView.as_view(), name="api-rating-me"),
]
