import random
import string

from django.utils.text import slugify
from organization.choices import OrganizationUserRole
from organization.models import Organization, OrganizationDetail, OrganizationUser
from rest_framework import serializers
from user.constants import ValidationErrors
from user.models import User


class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "description", "image", "email_domain", "slug")
        read_only_fields = ("id", "slug")
        extra_kwargs = {
            "email_domain": {"required": True},
        }

    def validate_name(self, value):
        """Ensure no organization with the same name or resulting slug already exists."""
        slug = slugify(value)
        if Organization.objects.filter(slug=slug).exists():
            raise serializers.ValidationError(
                ValidationErrors.ORGANIZATION_NAME_ALREADY_EXISTS
            )
        return value

    def validate_email_domain(self, value):
        """Validate email_domain format (e.g. 'company.com') and uniqueness."""
        import re

        value = value.strip().lower()
        # Must be a valid domain: label.tld, no @ symbol, no http
        domain_regex = re.compile(
            r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)" r"(\.[A-Za-z0-9-]{1,63})*\.[A-Za-z]{2,}$"
        )
        if not domain_regex.match(value):
            raise serializers.ValidationError(
                "Enter a valid domain name (e.g. company.com). Do not include '@' or 'http'."
            )
        if Organization.objects.filter(email_domain=value).exists():
            raise serializers.ValidationError(
                "An organization with the domain '{value}' already exists."
            )
        return value


class OrganizationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing organizations a user belongs to."""

    role = serializers.SerializerMethodField()
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "image", "email_domain", "role", "member_count")

    def get_role(self, obj):
        user = self.context.get("request").user
        try:
            return obj.organization_users.get(user=user).role
        except OrganizationUser.DoesNotExist:
            return None


class OrganizationDetailSerializer(serializers.ModelSerializer):
    organization = OrganizationCreateSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationDetail
        fields = (
            "id",
            "organization",
            "address",
            "phone",
            "email",
            "website",
            "member_count",
        )

    def get_member_count(self, obj):
        return obj.organization.member_count


class OrganizationUserSerializer(serializers.ModelSerializer):
    """Serializer for representing a user's membership in an organization."""

    organization = OrganizationCreateSerializer(read_only=True)

    class Meta:
        model = OrganizationUser
        fields = ("id", "organization", "role", "status")


class InviteUserSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        help_text="Username of the person to invite (email will be auto-built as username@org_domain)",
    )
    role = serializers.ChoiceField(choices=OrganizationUserRole.choices)
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), source="organization"
    )

    def validate_username(self, value):
        # Reject any value that looks like a full email (user should only provide the local part)
        if "@" in value:
            raise serializers.ValidationError(
                "Enter only the username part (e.g. 'john.doe'), not a full email address."
            )
        return value.strip().lower()

    def validate(self, attrs):
        organization = attrs["organization"]
        username = attrs["username"]

        if not organization.email_domain:
            raise serializers.ValidationError(
                {
                    "organization_id": "This organization does not have an email domain configured."
                }
            )

        # Build the full email from username + org domain
        email = f"{username}@{organization.email_domain}"
        attrs["email"] = email

        # Check if user already belongs to this org
        try:
            user = User.objects.get(email=email)
            if OrganizationUser.objects.filter(
                organization=organization, user=user
            ).exists():
                raise serializers.ValidationError(
                    {"username": ValidationErrors.USER_ALREADY_IN_ORGANIZATION}
                )
        except User.DoesNotExist:
            pass  # New user — no conflict
        return attrs

    def generate_random_password(self, length=12):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(random.choice(chars) for _ in range(length))

    def save(self, **kwargs):
        email = self.validated_data["email"]
        role = self.validated_data["role"]
        organization = self.validated_data["organization"]
        username = self.validated_data["username"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "is_active": True,
                "email_verified": False,
            },
        )

        temporary_password = None
        if created:
            temporary_password = self.generate_random_password()
            user.set_password(temporary_password)
            user.save()

        org_user = OrganizationUser.objects.create(
            organization=organization, user=user, role=role
        )

        from postoffice.email_service import EmailService

        if created and temporary_password:
            EmailService().send_invite_user_email(
                user, temporary_password, organization.name
            )
        else:
            EmailService().send_organization_added_email(user, organization)

        return org_user
