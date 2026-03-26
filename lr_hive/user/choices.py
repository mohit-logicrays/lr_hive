from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class EmailTemplateType(TextChoices):

    WELCOME = "welcome", _("Welcome")
    EMAIL_OTP_VERIFY = "email_otp_verify", _("Email OTP Verify")
    EMAIL_VERIFIED = "email_verified", _("Email Verified")
    PASSWORD_RESET = "password_reset", _("Password Reset")
    PASSWORD_CHANGE = "password_change", _("Password Change")
    PASSWORD_RESET_LINK = "password_reset_link", _("Password Reset Link")
    PASSWORD_RESET_SUCCESS = "password_reset_success", _("Password Reset Success")
    INVITE_USER = "invite_user", _("Invite User")
