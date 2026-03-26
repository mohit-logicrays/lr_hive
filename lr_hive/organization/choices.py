from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class OrganizationUserRole(TextChoices):
    OWNER = "owner", _("Owner")
    ADMIN = "admin", _("Admin")
    MEMBER = "member", _("Member")
    GUEST = "guest", _("Guest")
