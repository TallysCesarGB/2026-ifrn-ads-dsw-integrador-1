from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path("", views.feed, name="feed"),
    path("feed/mais/", views.feed_more, name="feed_more"),
    path("indicar/", views.new_post, name="new_post"),
    path("posts/<int:post_id>/excluir/", views.delete_post, name="delete_post"),
    path(
        "comentarios/<int:comment_id>/excluir/",
        views.delete_comment,
        name="delete_comment",
    ),
    path("posts/<int:post_id>/curtir/", views.toggle_like, name="toggle_like"),
    path("posts/<int:post_id>/recomendar/", views.recommend_post, name="recommend"),
    path("posts/<int:post_id>/comentarios/", views.list_comments, name="list_comments"),
    path(
        "posts/<int:post_id>/comentarios/novo/",
        views.create_comment,
        name="create_comment",
    ),
]
