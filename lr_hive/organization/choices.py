from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class OrganizationUserRole(TextChoices):
    OWNER = "owner", _("Owner")
    ADMIN = "admin", _("Admin")
    MANAGER = "manager", _("Manager")
    PROJECT_MANAGER = "project_manager", _("Project Manager")
    TEAM_LEAD = "team_lead", _("Team Lead")
    HR_EXECUTIVE = "hr_executive", _("HR Executive")
    EMPLOYEE = "employee", _("Employee")
    MEMBER = "member", _("Member")
    GUEST = "guest", _("Guest")
