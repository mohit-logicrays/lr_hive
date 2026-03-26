from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


def _upload_user_avatar(self, filename):
    return f"users/{self.id}/{filename}"


class User(AbstractUser):
    """User Model"""

    email = models.EmailField(verbose_name=_("Email"), unique=True)
    avatar = models.ImageField(
        verbose_name=_("Avatar"), upload_to=_upload_user_avatar, blank=True, null=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("username",)

    def __str__(self):
        return self.email
