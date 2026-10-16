
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"

    # The full Python import path includes the apps package.
    name = "apps.accounts"

    # The shorter label is used in Django model references,
    # migrations, and AUTH_USER_MODEL.
    label = "accounts"
