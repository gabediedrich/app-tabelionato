from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "app_tabelionato.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import app_tabelionato.users.signals  # noqa F401
        except ImportError:
            pass
