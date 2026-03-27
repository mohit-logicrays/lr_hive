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
        read_only_fields = ("id", "slug", "email_domain")

    def validate_name(self, value):
        """Ensure no organization with the same name or resulting slug already exists."""
        slug = slugify(value)
        if Organization.objects.filter(slug=slug).exists():
            raise serializers.ValidationError(
                ValidationErrors.ORGANIZATION_NAME_ALREADY_EXISTS
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
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=OrganizationUserRole.choices)
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), source="organization"
    )

    def validate_email(self, value):
        from utils.utils import normalize_email

        return normalize_email(value)

    def validate(self, attrs):
        organization = attrs["organization"]
        email = attrs["email"]
        try:
            user = User.objects.get(email=email)
            if OrganizationUser.objects.filter(
                organization=organization, user=user
            ).exists():
                raise serializers.ValidationError(
                    {"email": ValidationErrors.USER_ALREADY_IN_ORGANIZATION}
                )
        except User.DoesNotExist:
            pass  # New user - no conflict possible
        return attrs

    def generate_random_password(self, length=12):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(random.choice(chars) for _ in range(length))

    def save(self, **kwargs):
        email = self.validated_data["email"]
        role = self.validated_data["role"]
        organization = self.validated_data["organization"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
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
