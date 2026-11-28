from django.urls import path

from . import api

urlpatterns = [
    path("posts/", api.PostListCreateView.as_view(), name="api-posts"),
    path("posts/<int:post_id>/", api.PostDetailView.as_view(), name="api-post-detail"),
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
    path(
        "posts/<int:post_id>/comments/<int:comment_id>/",
        api.CommentDetailView.as_view(),
        name="api-post-comment-detail",
    ),
    path("feed/", api.FeedView.as_view(), name="api-feed"),
]
