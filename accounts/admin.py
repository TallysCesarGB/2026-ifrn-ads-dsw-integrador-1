from django.contrib import admin

from .models import Follow
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "display_name",
        "followers_count",
        "following_count",
        "posts_count",
    )
    search_fields = ("user__username", "display_name", "user__email")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "followed", "created_at")
    search_fields = ("follower__username", "followed__username")
