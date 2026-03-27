import random
import string

from organization.choices import OrganizationUserRole
from organization.models import Organization, OrganizationUser
from rest_framework import serializers
from user.models import User


class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "description")


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

        org_user, user_added = OrganizationUser.objects.get_or_create(
            organization=organization, user=user, defaults={"role": role}
        )
        if not user_added:
            org_user.role = role
            org_user.save()

        if created and temporary_password:
            from postoffice.email_service import EmailService

            EmailService().send_invite_user_email(
                user, temporary_password, organization.name
            )

        return org_user
