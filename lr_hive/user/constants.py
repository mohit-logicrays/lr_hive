# User App's Constants
from django.utils.translation import gettext_lazy as _


class ValidationErrors:
    EMAIL_ALREADY_EXISTS = _("Email already exists.")
    USERNAME_ALREADY_EXISTS = _("Username already exists.")
    PASSWORDS_DO_NOT_MATCH = _("Passwords do not match.")
    INVALID_CREDENTIALS = _("Invalid credentials provided.")
    INVALID_IMAGE_FILE = _("Invalid image file. Only image files are allowed.")
    USER_DOES_NOT_EXIST = _("User does not exist.")
    INVALID_OR_EXPIRED_OTP = _("Invalid or expired OTP.")
    EMAIL_ALREADY_VERIFIED = _("Email is already verified.")
    # Organization
    ORGANIZATION_NAME_ALREADY_EXISTS = _(
        "An organization with this name already exists."
    )
    ORGANIZATION_DOMAIN_ALREADY_EXISTS = _(
        "An organization with the domain '@{domain}' is already registered."
    )
    USER_ALREADY_IN_ORGANIZATION = _(
        "This user is already a member of the organization."
    )


class ExceptionMessages:
    SOMETHING_WENT_WRONG = _("Something went wrong, Please try again later.")
