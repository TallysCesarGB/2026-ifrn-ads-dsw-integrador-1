from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_profile(sender, instance, created, **kwargs):
    """Garante que todo usuário tenha um Profile associado, assim como o
    projeto original criava as colunas extras junto do registro em `users`."""
    if created:
        Profile.objects.get_or_create(user=instance)
