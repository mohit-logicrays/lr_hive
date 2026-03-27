from django_otp_keygen.otp_service import OtpService
from postoffice.email_service import EmailService
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from user.api.serializers import (
    ProfileUpdateSerializer,
    ResendOTPSerializer,
    UserSerailizer,
    VerifyOTPSerializer,
)
from user.models import User


class UserViewSet(ModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerailizer
    filterset_fields = ["is_active"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["email"]
    lookup_field = "id"
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Override get_permissions to return the permission class based on action.
        The permissions are as follows:
        - list and create: AllowAny()
        - others: IsAuthenticated()
        """

        if self.action in ["create"]:
            return [AllowAny()]
        return super().get_permissions()

    def get_object(self):
        """
        Override get_object to return the current user object.
        """
        return self.queryset.get(id=self.request.user.id)

    def perform_create(self, serializer):
        """
        Saves the user instance and sends an OTP email to the user.

        Returns the saved user instance.
        """
        user = serializer.save()
        # Generate and send OTP
        otp_service = OtpService(user, "signup")
        otp = otp_service.generate_otp()
        EmailService().send_email_otp_verify_email(user, otp)
        return user


class VerifyOTPAPIView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Verify the OTP sent to the user.

        Returns a JSON response with the detail that the OTP was verified successfully
        and the email of the user.

        Status code: 200 OK
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Welcome Email
        EmailService().send_welcome_email(user)
        return Response(
            {
                "detail": "OTP verified successfully. You can now log in.",
                "email": user.email,
            },
            status=status.HTTP_200_OK,
        )


class ResendOTPAPIView(generics.GenericAPIView):
    serializer_class = ResendOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Send a new OTP to the user.

        Returns a JSON response with the detail that a new OTP has been sent to the user.

        Status code: 200 OK
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "A new OTP has been sent to your email."},
            status=status.HTTP_200_OK,
        )


class ProfileUpdateAPIView(generics.UpdateAPIView):
    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Override get_object to return the current user object.
        """
        return self.request.user


class LoginAPiView(TokenObtainPairView):
    """
    Custom login view that uses the TokenObtainPairView from Simple JWT.
    It allows users to obtain a token pair (access and refresh tokens).
    """

    _serializer_class = "user.api.serializers.JWTTokenSerializer"


login_api_view = LoginAPiView.as_view()


class RefreshTokenView(TokenRefreshView):
    """
    Custom token refresh view that uses the TokenRefreshView from Simple JWT.
    It allows users to refresh their access token using a valid refresh token.
    """

    _serializer_class = "user.api.serializers.JWTTokenRefreshSerializer"


token_refresh_view = RefreshTokenView.as_view()
