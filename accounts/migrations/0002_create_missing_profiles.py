"""Cria o Profile de usuários que existiam antes do app `accounts` (#60).

O signal `accounts.signals.create_or_update_profile` só cobre usuários
salvos depois da instalação do app; quem já existia no banco ficava sem
perfil e derrubava perfil, busca, seguir e comentários com 500.
"""

from django.conf import settings
from django.db import migrations


def create_missing_profiles(apps, schema_editor):
    user_model = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    profile_model = apps.get_model("accounts", "Profile")
    db = schema_editor.connection.alias

    users_without_profile = user_model.objects.using(db).filter(profile__isnull=True)
    profile_model.objects.using(db).bulk_create(
        [profile_model(user=user) for user in users_without_profile],
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_missing_profiles, migrations.RunPython.noop),
    ]
