from organization.api.serializers import (
    InviteUserSerializer,
    OrganizationCreateSerializer,
    OrganizationListSerializer,
    OrganizationUserSerializer,
)
from organization.choices import OrganizationUserRole
from organization.models import Organization, OrganizationUser
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from user.constants import ValidationErrors


class OrganizationCreateAPIView(generics.CreateAPIView):
    serializer_class = OrganizationCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Save the organization, set the email_domain from the request user's email,
        and create the requesting user as the OWNER.
        """
        user = self.request.user
        # Extract domain from the creator's email e.g. "abc@company.com" -> "company.com"
        email_domain = user.email.split("@")[-1].lower()

        # Validate domain uniqueness here (serializer handles name uniqueness)
        if Organization.objects.filter(email_domain=email_domain).exists():
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {
                    "email_domain": str(
                        ValidationErrors.ORGANIZATION_DOMAIN_ALREADY_EXISTS
                    ).format(domain=email_domain)
                }
            )

        org = serializer.save(email_domain=email_domain)
        OrganizationUser.objects.create(
            organization=org, user=user, role=OrganizationUserRole.OWNER
        )

        # Send org created email
        from postoffice.email_service import EmailService

        EmailService().send_organization_created_email(user, org)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrganizationListAPIView(generics.ListAPIView):
    """Returns all active organizations the current user belongs to."""

    serializer_class = OrganizationListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Organization.objects.filter(
            organization_users__user=self.request.user,
            organization_users__status=1,  # ACTIVE_STATUS
        ).distinct()


class OrganizationSwitchAPIView(generics.GenericAPIView):
    """
    Switch the active organization context for the current user.
    Returns the membership details (role, org info) for the selected organization.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        organization_id = request.data.get("organization_id")
        if not organization_id:
            return Response(
                {"detail": "organization_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            org_user = OrganizationUser.objects.select_related("organization").get(
                organization_id=organization_id,
                user=request.user,
                status=1,  # ACTIVE_STATUS
            )
        except OrganizationUser.DoesNotExist:
            return Response(
                {"detail": "You are not a member of this organization."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = OrganizationUserSerializer(org_user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InviteUserAPIView(generics.GenericAPIView):
    serializer_class = InviteUserSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org = serializer.validated_data["organization"]

        try:
            requester_org_user = OrganizationUser.objects.get(
                organization=org, user=request.user, status=1
            )
        except OrganizationUser.DoesNotExist:
            return Response(
                {"detail": "You are not a member of this organization."},
                status=status.HTTP_403_FORBIDDEN,
            )

        allowed_roles = [
            OrganizationUserRole.OWNER,
            OrganizationUserRole.ADMIN,
            OrganizationUserRole.MANAGER,
            OrganizationUserRole.HR_EXECUTIVE,
        ]

        if requester_org_user.role not in allowed_roles:
            return Response(
                {
                    "detail": "You do not have permission to invite users to this organization."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.save()
        return Response(
            {"detail": "User invited successfully."}, status=status.HTTP_200_OK
        )
