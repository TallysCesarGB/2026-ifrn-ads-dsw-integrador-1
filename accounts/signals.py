from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_profile(sender, instance, created, **kwargs):
    """Garante que todo usuário tenha um Profile associado, assim como o
    projeto original criava as colunas extras junto do registro em `users`.

    Roda em todo save (não só na criação): se um usuário ficou sem perfil,
    ele é recriado no próximo save, por exemplo no login, que atualiza
    `last_login`. Ver #60.

    Ignora saves `raw` (loaddata): a fixture traz os próprios perfis, e
    criar um aqui conflitaria com o da fixture.
    """
    if kwargs.get("raw"):
        return
    Profile.objects.get_or_create(user=instance)
