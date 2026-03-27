from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django_otp_keygen.otp_service import OtpService
from postoffice.email_service import EmailService
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from user.constants import ExceptionMessages, ValidationErrors
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
        """
        Validate the username field.

        Check if a user with the same username already exists in the database.
        If the user exists, raise a serializers.ValidationError with the error message
        USERNAME_ALREADY_EXISTS.

        :param value: The username field value to be validated.
        :return: The validated username field value.
        :raises serializers.ValidationError: If a user with the same username already exists.
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(ValidationErrors.USERNAME_ALREADY_EXISTS)
        return value

    def validate_email(self, value):
        """
        Validate the email field.

        Check if a user with the same email already exists in the database.
        If the user exists, raise a serializers.ValidationError with the error message
        EMAIL_ALREADY_EXISTS.

        :param value: The email field value to be validated.
        :return: The validated email field value.
        :raises serializers.ValidationError: If a user with the same email already exists.
        """
        value = normalize_email(value)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(ValidationErrors.EMAIL_ALREADY_EXISTS)
        return value

    def validate(self, attrs):
        """
        Validates the user registration data.

        Checks if the password and confirm password fields match.
        If the fields do not match, raises a serializers.ValidationError with the error message
        PASSWORDS_DO_NOT_MATCH.

        :param attrs: The user registration data to be validated.
        :return: The validated user registration data.
        :raises serializers.ValidationError: If the password and confirm password fields do not match.
        """
        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError(
                {"confirm_password": ValidationErrors.PASSWORDS_DO_NOT_MATCH}
            )
        return attrs

    def create(self, validated_data):
        """
        Creates a new user instance with the provided validated data.

        The method first removes the confirm password field from the validated data.
        If the username field is not provided, it sets the
            username field to the email field value.
        It then sets the is_active field to False and
            creates a new user instance using the validated data.
        Finally, it sets the password for the user instance
            and saves it to the database.

        If any exception occurs during the creation process,
            it raises a serializers.ValidationError with the error message
            SOMETHING_WENT_WRONG.

        :param validated_data: The validated user registration data.
        :return: The created user instance.
        :raises serializers.ValidationError: If any exception occurs during the creation process.
        """
        try:
            with transaction.atomic():
                password = validated_data.pop("confirm_password")
                if "username" not in validated_data:
                    validated_data["username"] = validated_data.get("email")
                validated_data["is_active"] = False
                user = super().create(validated_data)
                user.set_password(password)
                user.save()
                return user
        except Exception as e:
            raise serializers.ValidationError(
                {"detail": ExceptionMessages.SOMETHING_WENT_WRONG}
            )


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        """
        Validates the verify OTP request data.

        It first normalizes the email address and retrieves the user instance with the same email address.
        If the user does not exist, it raises a serializers.ValidationError with the error message
        USER_DOES_NOT_EXIST.

        It then verifies the OTP using the OtpService class.
        If the OTP is invalid or expired, it raises a serializers.ValidationError with the error message
        INVALID_OR_EXPIRED_OTP.

        If the OTP is valid, it sets the user instance to the validated data and returns the validated data.

        :param attrs: The verified OTP request data.
        :return: The validated data.
        :raises serializers.ValidationError: If the user does not exist or if the OTP is invalid or expired.
        """
        email = normalize_email(attrs.get("email"))
        otp = attrs.get("otp")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": ValidationErrors.USER_DOES_NOT_EXIST}
            )

        otp_service = OtpService(user, "signup")
        if not otp_service.verify_otp(otp):
            raise serializers.ValidationError(
                {"otp": ValidationErrors.INVALID_OR_EXPIRED_OTP}
            )

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
            raise serializers.ValidationError(
                {"email": ValidationErrors.USER_DOES_NOT_EXIST}
            )

        if user.email_verified:
            raise serializers.ValidationError(
                {"email": ValidationErrors.EMAIL_ALREADY_VERIFIED}
            )

        attrs["user"] = user
        return attrs

    def save(self):
        """
        Generates a new OTP for the user and sends an email OTP verification to the user.

        :param self: The ResendOTPSerializer instance.
        :param attrs: The validated data containing the user instance.
        :return: None
        """
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
        """
        Validates the user login data.

        Calls the parent class's validate method to validate the username and password.
        Sets the email_verified field of the validated data
            to the email_verified field of the user instance.

        :param attrs: The user login data to be validated.
        :return: The validated user login data.
        """
        data = super().validate(attrs)
        data["email_verified"] = self.user.email_verified
        return data


class JWTTokenRefreshSerializer(TokenRefreshSerializer):
    """Serializer for refreshing JWT tokens."""

    default_error_messages = {
        "token_not_valid": ValidationErrors.INVALID_CREDENTIALS,
    }
