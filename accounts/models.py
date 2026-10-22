from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse


def avatar_upload_to(instance, filename):
    return f"avatars/{instance.user_id}/{filename}"


class Profile(models.Model):
    """Dados adicionais do usuário (equivalente aos campos extras da
    tabela `users` do projeto original: display_name, bio, avatar)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=120, blank=True)
    bio = models.TextField(max_length=280, blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_to, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse("accounts:profile", kwargs={"username": self.user.username})

    @property
    def display_name_or_username(self):
        return self.display_name or self.user.username

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        # Fallback idêntico ao usado no front-end original (Dicebear)
        return f"https://api.dicebear.com/7.x/avataaars/svg?seed={self.user.username}"

    @property
    def followers_count(self):
        return Follow.objects.filter(followed=self.user).count()

    @property
    def following_count(self):
        return Follow.objects.filter(follower=self.user).count()

    @property
    def posts_count(self):
        return self.user.posts.count()


class Follow(models.Model):
    """Relação de "seguir" entre dois usuários."""

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_set",
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers_set",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "followed"],
                name="unique_follow",
            ),
            models.CheckConstraint(
                condition=~Q(follower=models.F("followed")),
                name="cannot_follow_self",
            ),
        ]
        indexes = [
            models.Index(fields=["follower"]),
            models.Index(fields=["followed"]),
        ]

    def __str__(self):
        return f"{self.follower} → {self.followed}"
