from organization.api.serializers import (
    InviteUserSerializer,
    OrganizationCreateSerializer,
)
from organization.choices import OrganizationUserRole
from organization.models import OrganizationUser
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class OrganizationCreateAPIView(generics.CreateAPIView):
    serializer_class = OrganizationCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        org = serializer.save()
        OrganizationUser.objects.create(
            organization=org, user=self.request.user, role=OrganizationUserRole.OWNER
        )


class InviteUserAPIView(generics.GenericAPIView):
    serializer_class = InviteUserSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org = serializer.validated_data["organization"]

        try:
            requester_org_user = OrganizationUser.objects.get(
                organization=org, user=request.user, is_active=True
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
