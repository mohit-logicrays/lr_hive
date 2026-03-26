from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel, TitleDescriptionModel
from user.choices import EmailTemplateType


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


class EmailTemplate(TimeStampedModel, TitleDescriptionModel):
    is_html = models.BooleanField(default=False)
    email_type = models.CharField(
        max_length=255, choices=EmailTemplateType.choices, help_text=_("Email Type")
    )
    subject = models.CharField(max_length=255, help_text=_("Subject"))
    body = models.TextField(verbose_name=_("Body"), help_text=_("Body"))

    def __str__(self):
        return self.title
