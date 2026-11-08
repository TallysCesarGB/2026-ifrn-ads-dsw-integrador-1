from django.contrib import admin

from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("user", "tmdb_id", "media_type", "score", "created_at")
    list_filter = ("media_type", "score")
    search_fields = ("user__username",)
