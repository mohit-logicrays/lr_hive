from django.contrib.auth.password_validation import validate_password
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
        """
        Validate the username field.

        Checks if the given username already exists or not in the database.
        If it already exists, raises a serializers.ValidationError with a message
        ValidationErrors.USERNAME_ALREADY_EXISTS.
        """

        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(ValidationErrors.USERNAME_ALREADY_EXISTS)
        return value

    def validate_email(self, value):
        """
        Validate the email field.

        Normalizes the email by removing any leading/trailing whitespace and
        converting the email to lowercase.
        """

        value = normalize_email(value)
        return value

    def validate(self, attrs):
        """
        Validate the entire serializer data.

        Checks if the password and confirm_password fields match.
        If they do not match, raises a serializers.ValidationError with a message
        indicating that the passwords do not match.
        """

        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError(
                {"confirm_password": ValidationErrors.PASSWORDS_DO_NOT_MATCH}
            )
        return attrs

    def create(self, validated_data):
        """
        Creates a new user and returns the created user object.

        Pops the confirm_password from the validated_data and assigns the
        username from the validated_data to the validate_password's username
        before calling the super().create() method to create the user.

        Args:
            validated_data (dict): Validated data to use for creating the user.

        Returns:
            User: The created user object.
        """
        password = validated_data.pop("confirm_password")
        if "username" not in validated_data:
            validated_data["username"] = validated_data.get("email")
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user


class JWTTokenSerializer(TokenObtainPairSerializer):
    """Serializer for user login using JWT."""

    default_error_messages = {
        "no_active_account": ValidationErrors.INVALID_CREDENTIALS,
    }


class JWTTokenRefreshSerializer(TokenRefreshSerializer):
    """Serializer for refreshing JWT tokens."""

    default_error_messages = {
        "token_not_valid": ValidationErrors.INVALID_CREDENTIALS,
    }
