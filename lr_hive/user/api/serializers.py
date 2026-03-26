from django.contrib.auth.password_validation import validate_password
from django_otp_keygen.otp_service import OtpService
from postoffice.email_service import EmailService
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from user.constants import ValidationErrors
from user.models import User
from utils.serializers import DynamicFieldsModelSerializer
from utils.utils import normalize_email


class UserSerailizer(DynamicFieldsModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "avatar",
            "first_name",
            "last_name",
            "is_active",
            "username",
            "password",
            "confirm_password",
        )
        read_only_fields = ("id", "is_active")
        extra_kwargs = {
            "id": {"read_only": True},
            "is_active": {"read_only": True},
            "avatar": {"required": False},
            "password": {
                "write_only": True,
                "required": True,
                "validators": [validate_password],
            },
            "email": {"required": True},
            "username": {"required": False},
            "first_name": {"required": True},
            "last_name": {"required": False},
        }

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(ValidationErrors.USERNAME_ALREADY_EXISTS)
        return value

    def validate_email(self, value):
        value = normalize_email(value)
        return value

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError(
                {"confirm_password": ValidationErrors.PASSWORDS_DO_NOT_MATCH}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("confirm_password")
        if "username" not in validated_data:
            validated_data["username"] = validated_data.get("email")
        validated_data["is_active"] = False
        user = super().create(validated_data)
        user.set_password(password)
        user.save()

        # Generate and send OTP
        otp_service = OtpService(user, "signup")
        otp = otp_service.generate_otp()
        EmailService().send_email_otp_verify_email(user, otp)

        return user


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = normalize_email(attrs.get("email"))
        otp = attrs.get("otp")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User does not exist."})

        otp_service = OtpService(user, "signup")
        if not otp_service.verify_otp(otp):
            raise serializers.ValidationError({"otp": "Invalid or expired OTP."})

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.is_active = True
        user.email_verified = True
        user.save()
        return user


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = normalize_email(attrs.get("email"))
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User does not exist."})

        if user.email_verified:
            raise serializers.ValidationError({"email": "Email is already verified."})

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        otp_service = OtpService(user, "signup")
        otp = otp_service.generate_otp()
        EmailService().send_email_otp_verify_email(user, otp)


class ProfileUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "avatar", "password", "email_verified")
        read_only_fields = ("email_verified",)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
            instance.email_verified = True
        instance.save()
        return instance


class JWTTokenSerializer(TokenObtainPairSerializer):
    """Serializer for user login using JWT."""

    default_error_messages = {
        "no_active_account": ValidationErrors.INVALID_CREDENTIALS,
    }

    def validate(self, attrs):
        data = super().validate(attrs)
        data["email_verified"] = self.user.email_verified
        return data


class JWTTokenRefreshSerializer(TokenRefreshSerializer):
    """Serializer for refreshing JWT tokens."""

    default_error_messages = {
        "token_not_valid": ValidationErrors.INVALID_CREDENTIALS,
    }
