from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import ActivatorModel, TimeStampedModel
from support.choices import TicketCategory, TicketPriority, TicketStatus


def _upload_support_attachment(self, filename):
    return f"support/{self.ticket.id}/{filename}"


class SupportTicket(TimeStampedModel, ActivatorModel):
    """Main support ticket model."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets",
        help_text=_("User"),
    )
    organization = models.ForeignKey(
        "organization.Organization",
        on_delete=models.CASCADE,
        related_name="support_tickets",
        help_text=_("Organization"),
    )
    subject = models.CharField(max_length=255, help_text=_("Subject"))
    message = models.TextField(help_text=_("Initial Message"))
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.NEW,
        help_text=_("Status"),
    )
    priority = models.CharField(
        max_length=20,
        choices=TicketPriority.choices,
        default=TicketPriority.MEDIUM,
        help_text=_("Priority"),
    )
    category = models.CharField(
        max_length=20,
        choices=TicketCategory.choices,
        default=TicketCategory.GENERAL,
        help_text=_("Category"),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        help_text=_("Assigned Agent"),
    )

    class Meta:
        verbose_name = _("Support Ticket")
        verbose_name_plural = _("Support Tickets")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["organization"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Ticket #{self.id}: {self.subject}"


class SupportComment(TimeStampedModel, ActivatorModel):
    """Threading comments for support tickets."""

    ticket = models.ForeignKey(
        "support.SupportTicket",
        on_delete=models.CASCADE,
        related_name="comments",
        help_text=_("Ticket"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_comments",
        help_text=_("User"),
    )
    message = models.TextField(help_text=_("Message"))
    is_internal = models.BooleanField(
        default=False, help_text=_("Staff only internal note")
    )
    attachment = models.FileField(
        upload_to=_upload_support_attachment,
        null=True,
        blank=True,
        help_text=_("Attachment"),
    )

    class Meta:
        verbose_name = _("Support Comment")
        verbose_name_plural = _("Support Comments")
        ordering = ["created"]

    def __str__(self):
        return f"Comment by {self.user} on Ticket #{self.ticket.id}"
