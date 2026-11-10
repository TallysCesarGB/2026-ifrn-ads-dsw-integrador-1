from django.contrib import admin

from .models import Comment
from .models import Like
from .models import Post
from .models import Recommendation


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "media_type",
        "tmdb_id",
        "likes_count",
        "comments_count",
        "created_at",
    )
    search_fields = ("title", "user__username")
    list_filter = ("media_type", "created_at")
    inlines = [CommentInline]


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "content", "created_at")


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("recommended_by", "original_post", "created_at")
