from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import ActivatorModel, TimeStampedModel
from leave.choices import LeaveStatus, LeaveType


class Leave(TimeStampedModel, ActivatorModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leaves",
        help_text=_("User"),
    )
    organization = models.ForeignKey(
        "organization.Organization",
        on_delete=models.CASCADE,
        related_name="leaves",
        help_text=_("Organization"),
    )
    leave_type = models.CharField(
        max_length=20,
        choices=LeaveType.choices,
        default=LeaveType.PAID,
        help_text=_("Leave Type"),
    )
    leave_status = models.CharField(
        max_length=20,
        choices=LeaveStatus.choices,
        default=LeaveStatus.PENDING,
        help_text=_("Leave Status"),
    )
    start_date = models.DateField(help_text=_("Start Date"))
    end_date = models.DateField(help_text=_("End Date"))
    reason = models.TextField(blank=True, help_text=_("Reason"))

    class Meta:
        verbose_name = "Leave"
        verbose_name_plural = "Leaves"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["organization"]),
        ]

    def __str__(self):
        return self.title
