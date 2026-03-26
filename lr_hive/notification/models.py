from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import (
    ActivatorModel,
    TimeStampedModel,
    TitleSlugDescriptionModel,
)


class Notification(TitleSlugDescriptionModel, TimeStampedModel, ActivatorModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text=_("User"),
    )
    organization = models.ForeignKey(
        "organization.Organization",
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text=_("Organization"),
    )

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["organization"]),
        ]

    def __str__(self):
        return self.title
