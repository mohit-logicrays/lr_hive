from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class TicketStatus(TextChoices):
    NEW = "new", _("New")
    OPEN = "open", _("Open")
    PENDING = "pending", _("Pending")
    RESOLVED = "resolved", _("Resolved")
    CLOSED = "closed", _("Closed")


class TicketPriority(TextChoices):
    LOW = "low", _("Low")
    MEDIUM = "medium", _("Medium")
    HIGH = "high", _("High")
    URGENT = "urgent", _("Urgent")


class TicketCategory(TextChoices):
    GENERAL = "general", _("General")
    TECHNICAL = "technical", _("Technical")
    BILLING = "billing", _("Billing")
    OTHER = "other", _("Other")
