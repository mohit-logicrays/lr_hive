from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField
from django_extensions.db.models import ActivatorModel, TimeStampedModel
from organization.choices import OrganizationUserRole


class Organization(TimeStampedModel, ActivatorModel):
    name = models.CharField(
        max_length=255, unique=True, help_text=_("Organization Name")
    )
    slug = AutoSlugField(
        populate_from="name",
        max_length=255,
        unique=True,
        help_text=_("Organization Slug"),
    )
    description = models.TextField(blank=True, help_text=_("Organization Description"))
    image = models.ImageField(
        upload_to="organization/images/",
        blank=True,
        null=True,
        help_text=_("Organization Image"),
    )
    email_domain = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        help_text=_("Email domain of the organization (e.g. company.com)"),
    )

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["email_domain"]),
        ]

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.organization_users.filter(
            status=ActivatorModel.ACTIVE_STATUS
        ).count()


class OrganizationDetail(TimeStampedModel):
    organization = models.OneToOneField(
        "organization.Organization",
        on_delete=models.CASCADE,
        related_name="organization_details",
        help_text=_("Organization"),
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Organization Address"),
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text=_("Organization Phone"),
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text=_("Organization Email"),
    )
    website = models.URLField(
        blank=True,
        null=True,
        help_text=_("Organization Website"),
    )

    class Meta:
        verbose_name = _("Organization Detail")
        verbose_name_plural = _("Organization Details")
        indexes = [
            models.Index(fields=["organization"]),
        ]

    def __str__(self):
        return "%s Details" % self.organization.name


class OrganizationUser(TimeStampedModel, ActivatorModel):
    organization = models.ForeignKey(
        "organization.Organization",
        on_delete=models.CASCADE,
        related_name="organization_users",
        help_text=_("Organization"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_users",
        help_text=_("User"),
    )
    role = models.CharField(
        max_length=20,
        choices=OrganizationUserRole.choices,
        default=OrganizationUserRole.MEMBER,
        help_text=_("Role"),
    )

    class Meta:
        verbose_name = _("Organization User")
        verbose_name_plural = _("Organization Users")
        unique_together = ("organization", "user")
        indexes = [
            models.Index(fields=["organization"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.organization.name}"
