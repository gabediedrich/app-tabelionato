from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Default user for App Tabelionato."""

    fullname = models.CharField(
        verbose_name=_("Nome completo"),
        help_text=_('Insira o nome completo não abreviado'),
        blank=True,
        max_length=255,
    )

    profile_pic = models.ImageField(
        upload_to='profile_pics/%Y%m%d_',
        blank=True,
        null=True,
        default='profile_pics/0001_default.jpg',
    )

    small_intro = models.CharField(
        verbose_name=_("Nome completo"),
        help_text=_('Insira o nome completo não abreviado'),
        max_length=300,
        blank=True,
    )

    # TODO Desenvolver mestre e guru
    #   Quais são as definições de cada cargo?
    #   Tabela de autorizações

    is_guru = models.BooleanField(
        verbose_name=_("É guru"),
        help_text=_('Insira o nome completo não abreviado'),
        default=False,
    )

    is_master = models.BooleanField(
        verbose_name=_("É mestre"),
        help_text=_('Insira o nome completo não abreviado'),
        default=False,
    )

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

    def user_directory_path(self, instance, filename):
        # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
        return 'user_{0}/{1}'.format(instance.user.id, filename)

    def __str__(self):
        return self.user.fullname
