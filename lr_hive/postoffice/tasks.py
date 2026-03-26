from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django_rq import job


def send_email(
    subject: str,
    message: str,
    from_email: str,
    recipient_list: list,
    reply_to_emails: list,
    is_html: bool = False,
):
    """
    Send an email.

    :param subject: The email subject.
    :param message: The email body.
    :param from_email: The email sender.
    :param to_emails: The email recipient(s).
    :param reply_to_emails: The email reply-to address.
    :param is_html: Whether the message is HTML, default False.
    :return: None
    """
    mail = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(message),
        from_email=from_email,
        to=recipient_list,
        reply_to=[reply_to_emails],
    )
    if is_html:
        mail.attach_alternative(message, "text/html")
    mail.send(fail_silently=False)
    return


@job(func_or_queue="default")
def send_delayed_email(
    subject: str,
    message: str,
    from_email: str,
    recipient_list: list,
    reply_to_emails: list,
    is_html: bool = False,
):
    """
    Sends an email with a delay using a background task.

    :param subject: The email subject.
    :param message: The email body.
    :param from_email: The sender's email address.
    :param to_emails: List of recipient email addresses.
    :param reply_to_emails: List of reply-to email addresses.
    :param is_html: Flag to indicate if the message is HTML formatted, default is False.
    """

    send_email(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipient_list,
        reply_to_emails=reply_to_emails,
        is_html=is_html,
    )
