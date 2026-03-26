"""
postoffice/email_service.py
Class-based email service for sending and logging emails through postoffice.
All application emails route through EmailService for CCPA compliance & audit trail.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.html import strip_tags
from postoffice.tasks import send_delayed_email, send_email as send_email_sync_task

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailService:
    """
    Service class for sending and tracking emails through postoffice.
    Handles both async and sync email sending with automatic Email model logging.

    Usage:
        service = EmailService()
        email_record = service.send_async(
            template_type='privacy',
            recipient_email='user@example.com',
            subject='Your Export is Ready',
            body='<html>...</html>',
            is_html=True,
            user=request.user
        )
    """

    VALID_TEMPLATE_TYPES = [
        "account",
        "privacy",
        "order",
        "marketing",
        "system",
        "custom",
    ]

    def __init__(self):
        """Initialize email service."""
        self.from_email = getattr(
            settings, "DEFAULT_FROM_EMAIL", "noreply@jointcommerce.com"
        )
        self.frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

    def send_async(
        self,
        template_type: str,
        recipient_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        user: Optional[User] = None,
        metadata: Optional[Dict[str, Any]] = None,
        reply_to: Optional[str] = None,
    ) -> Tuple[Any, Any]:
        """
        Send email asynchronously via Celery task and log to Database.

        Args:
            template_type: Email category (account|privacy|order|marketing|system|custom)
            recipient_email: Recipient email address
            subject: Email subject line
            body: Email body (HTML if is_html=True)
            is_html: Whether body contains HTML
            user: Related User object (optional)
            metadata: Additional context data (dict)
            reply_to: Reply-to email address

        Returns:
            tuple: (Email model instance, Celery task object)

        Raises:
            ValueError: If template_type is invalid
        """
        from users.models import Email

        # Validate template type
        template_type = self._validate_template_type(template_type)

        try:
            # Create audit log
            email_record = Email.objects.create(
                user=user,
                recipient_email=recipient_email,
                template_type=template_type,
                subject=subject,
                body=body,
                is_html=is_html,
                metadata=metadata or {},
            )

            # Prepare reply-to
            reply_to_email = reply_to or self.from_email

            # Queue async task
            task = send_delayed_email(
                subject=subject,
                message=body,
                from_email=self.from_email,
                recipient_list=[recipient_email],
                reply_to_emails=reply_to_email,
                is_html=is_html,
            )

            # Mark sent and store task ID
            email_record.mark_sent()
            if task and hasattr(task, "id"):
                email_record.metadata["celery_task_id"] = str(task.id)
                email_record.save(update_fields=["metadata"])

            logger.info(
                f"[EmailService] Async email queued: {email_record.id} → "
                f"{recipient_email} (type={template_type})"
            )

            return email_record, task

        except Exception as e:
            logger.error(
                f"[EmailService] Error sending async email to {recipient_email} "
                f"(type={template_type}): {e}",
                exc_info=True,
            )
            raise

    def send_sync(
        self,
        template_type: str,
        recipient_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        user: Optional[User] = None,
        metadata: Optional[Dict[str, Any]] = None,
        reply_to: Optional[str] = None,
    ) -> Any:
        """
        Send email synchronously (blocking) and log to Database.

        Use only for critical emails requiring immediate delivery.
        Prefer send_async() for standard use cases.

        Args:
            Same as send_async()

        Returns:
            Email model instance

        Raises:
            Exception: If sending fails
        """
        from users.models import Email

        # Validate template type
        template_type = self._validate_template_type(template_type)

        try:
            # Create audit log
            email_record = Email.objects.create(
                user=user,
                recipient_email=recipient_email,
                template_type=template_type,
                subject=subject,
                body=body,
                is_html=is_html,
                metadata=metadata or {},
            )

            # Prepare reply-to
            reply_to_email = reply_to or self.from_email

            # Send synchronously
            send_email_sync_task(
                subject=subject,
                message=body,
                from_email=self.from_email,
                recipient_list=[recipient_email],
                reply_to_emails=reply_to_email,
                is_html=is_html,
            )

            # Mark sent
            email_record.mark_sent()

            logger.info(
                f"[EmailService] Sync email sent: {email_record.id} → "
                f"{recipient_email} (type={template_type})"
            )

            return email_record

        except Exception as e:
            logger.error(
                f"[EmailService] Error sending sync email to {recipient_email} "
                f"(type={template_type}): {e}",
                exc_info=True,
            )

            # Mark failed
            try:
                email_record.mark_failed(str(e))
            except Exception:
                pass

            raise

    def _validate_template_type(self, template_type: str) -> str:
        """
        Validate and normalize template type.

        Args:
            template_type: Template type string to validate

        Returns:
            str: Valid template type (or 'custom' if invalid)
        """
        if template_type not in self.VALID_TEMPLATE_TYPES:
            logger.warning(
                f"[EmailService] Invalid template_type '{template_type}', "
                f"using 'custom'"
            )
            return "custom"
        return template_type

    def get_email_records(
        self,
        user: Optional[User] = None,
        template_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ):
        """
        Retrieve email records with optional filtering.

        Args:
            user: Filter by user
            template_type: Filter by template type
            status: Filter by status (sent|failed|pending|bounced)
            limit: Max records to return

        Returns:
            QuerySet: Filtered Email records
        """
        from users.models import Email

        query = Email.objects.all()

        if user:
            query = query.filter(user=user)
        if template_type:
            query = query.filter(template_type=template_type)
        if status:
            query = query.filter(status=status)

        return query.order_by("-created_at")[:limit]


# Convenience function for backward compatibility and simple use cases
def send_email_and_log(
    template_type: str,
    recipient_email: str,
    subject: str,
    body: str,
    is_html: bool = False,
    user: Optional[User] = None,
    metadata: Optional[Dict[str, Any]] = None,
    reply_to: Optional[str] = None,
    sync: bool = False,
) -> Any:
    """
    Convenience function wrapping EmailService for one-off email sends.

    Args:
        template_type: Email category
        recipient_email: Recipient email
        subject: Email subject
        body: Email body
        is_html: Whether body is HTML
        user: Related user
        metadata: Additional context
        reply_to: Reply-to address
        sync: Whether to send synchronously (False = async)

    Returns:
        Email model instance if sync=True, (Email, Task) tuple if sync=False
    """
    service = EmailService()

    if sync:
        return service.send_sync(
            template_type=template_type,
            recipient_email=recipient_email,
            subject=subject,
            body=body,
            is_html=is_html,
            user=user,
            metadata=metadata,
            reply_to=reply_to,
        )
    else:
        return service.send_async(
            template_type=template_type,
            recipient_email=recipient_email,
            subject=subject,
            body=body,
            is_html=is_html,
            user=user,
            metadata=metadata,
            reply_to=reply_to,
        )
