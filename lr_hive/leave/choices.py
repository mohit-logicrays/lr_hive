from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class LeaveType(TextChoices):
    PAID = "paid", _("Paid")
    UNPAID = "unpaid", _("Unpaid")
    SICK = "sick", _("Sick")
    VACATION = "vacation", _("Vacation")
    OTHER = "other", _("Other")


class LeaveStatus(TextChoices):
    PENDING = "pending", _("Pending")
    APPROVED = "approved", _("Approved")
    REJECTED = "rejected", _("Rejected")
