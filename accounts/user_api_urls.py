from django.urls import path

from . import api

urlpatterns = [
    path("users/search/", api.UserSearchView.as_view(), name="api-user-search"),
    path("users/<str:username>/", api.UserDetailView.as_view(), name="api-user-detail"),
    path(
        "users/id/<int:user_id>/follow/",
        api.FollowToggleView.as_view(),
        name="api-follow-toggle",
    ),
]
