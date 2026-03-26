import logging
from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import mail_admins
from postoffice.tasks import send_delayed_email, send_email as send_email_sync_task
from user.choices import EmailTemplateType
from user.models import EmailTemplate

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailService:
    def __init__(
        self,
        sender_email: Optional[str] = None,
        reply_to: Optional[list] = None,
    ):
        self.sender_email = sender_email or settings.EMAIL_HOST_USER
        self.reply_to = reply_to or [self.sender_email]

    def get_template(self, email_type: str) -> Optional[EmailTemplate]:
        """Fetch email template by type, notify admins if missing."""
        try:
            return EmailTemplate.objects.get(email_type=email_type)
        except EmailTemplate.DoesNotExist:
            logger.error(f"Email template not found for type: {email_type}")
            mail_admins(
                subject=f"Missing Email Template: {email_type}",
                message=f"The email template for '{email_type}' is missing from the database. Please create it in the admin panel.",
            )
            return None

    def render_template(
        self, template: EmailTemplate, context: Dict[str, Any]
    ) -> Tuple[str, str]:
        """Render template subject and body with context."""
        subject = template.subject.format(**context)
        body = template.body.format(**context)
        return subject, body

    def send_email(
        self,
        to_email: Any,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        from_email: Optional[str] = None,
        cc: Optional[list] = None,
        bcc: Optional[list] = None,
        attachments: Optional[list] = None,
        reply_to: Optional[list] = None,
        is_html: bool = False,
        delay_seconds: Optional[int] = None,
        template: Optional[EmailTemplate] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Unified email sending method supporting templates and delayed delivery."""
        if template:
            subject, body = self.render_template(template, context or {})
            is_html = template.is_html

        recipient_list = [to_email] if isinstance(to_email, str) else to_email
        from_email = from_email or self.sender_email
        reply_to = reply_to or self.reply_to

        if delay_seconds:
            send_delayed_email.delay(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=recipient_list,
                reply_to_emails=reply_to,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                is_html=is_html,
            )
        else:
            send_email_sync_task(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=recipient_list,
                reply_to_emails=reply_to,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                is_html=is_html,
            )

    def _send_templated_email(
        self, email_type: str, user: User, context: Optional[Dict[str, Any]] = None
    ):
        """Helper to send templated emails based on EmailTemplateType."""
        template = self.get_template(email_type)
        if template:
            ctx = {"user": user}
            if context:
                ctx.update(context)
            self.send_email(to_email=user.email, template=template, context=ctx)

    def send_welcome_email(self, user: User):
        self._send_templated_email(EmailTemplateType.WELCOME, user)

    def send_email_otp_verify_email(self, user: User, otp: str):
        self._send_templated_email(
            EmailTemplateType.EMAIL_OTP_VERIFY, user, {"otp": otp}
        )

    def send_email_verified_email(self, user: User):
        self._send_templated_email(EmailTemplateType.EMAIL_VERIFIED, user)

    def send_password_reset_email(self, user: User, reset_link: str):
        self._send_templated_email(
            EmailTemplateType.PASSWORD_RESET, user, {"reset_link": reset_link}
        )

    def send_password_change_email(self, user: User):
        self._send_templated_email(EmailTemplateType.PASSWORD_CHANGE, user)

    def send_password_reset_link_email(self, user: User, reset_link: str):
        self._send_templated_email(
            EmailTemplateType.PASSWORD_RESET_LINK, user, {"reset_link": reset_link}
        )

    def send_password_reset_success_email(self, user: User):
        self._send_templated_email(EmailTemplateType.PASSWORD_RESET_SUCCESS, user)
