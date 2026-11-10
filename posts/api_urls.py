from django.urls import path

from . import api

urlpatterns = [
    path("posts/", api.PostListCreateView.as_view(), name="api-posts"),
    path("posts/<int:post_id>/like/", api.PostLikeView.as_view(), name="api-post-like"),
    path(
        "posts/<int:post_id>/recommend/",
        api.PostRecommendView.as_view(),
        name="api-post-recommend",
    ),
    path(
        "posts/<int:post_id>/comments/",
        api.PostCommentsView.as_view(),
        name="api-post-comments",
    ),
    path("feed/", api.FeedView.as_view(), name="api-feed"),
]
