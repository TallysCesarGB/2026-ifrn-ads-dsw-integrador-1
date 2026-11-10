from django.conf import settings
from django.db import models
from django.urls import reverse

MEDIA_TYPE_CHOICES = [("movie", "Filme"), ("tv", "Série")]


class Post(models.Model):
    """Indicação de filme/série feita por um usuário."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    tmdb_id = models.PositiveIntegerField()
    media_type = models.CharField(
        max_length=5,
        choices=MEDIA_TYPE_CHOICES,
        default="movie",
    )
    title = models.CharField(max_length=255)
    poster_url = models.URLField(blank=True, null=True)  # noqa: DJ001
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tmdb_id", "media_type"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.title}"

    def get_absolute_url(self):
        return reverse(
            "films:detail",
            kwargs={"media_type": self.media_type, "tmdb_id": self.tmdb_id},
        )

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def comments_count(self):
        return self.comment_set.count()


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="unique_like"),
        ]

    def __str__(self):
        return f"{self.user.username} curtiu #{self.post_id}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comment_set")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"


class Recommendation(models.Model):
    """Registro de "recomendar/repostar" a indicação de outra pessoa
    (equivalente ao evento `post.recomendado` do projeto original)."""

    original_post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="recommendations",
    )
    recommended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommendations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recommended_by.username} recomendou #{self.original_post_id}"
