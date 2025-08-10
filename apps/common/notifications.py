import logging
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

def notify_user(alert, message: str, price: Decimal):
    """
    Send a notification email to the user.
    """
    user = alert.user
    subject = f"[Stock Alert] {alert.stock.ticker}"
    body = f"""
    Hi {user.username},

    Your alert "{alert.name or alert.id}" was triggered.

    Details:
    - Stock: {alert.stock.ticker}
    - Price: {price}
    - Message: {message}

    Regards,
    Stock Alerting System
    """
    email_to = [user.email] if user.email else []
    try:
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD and email_to:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                email_to,
                fail_silently=False,
            )
            logger.info(f"Notification sent to {user.email} for alert {alert.id}.")
            return True
    except Exception as e:
        logger.warning(f"Failed to send notification for alert {alert.id} to {user.email}: {e}")

    logger.info(f"Notification fallback for alert {alert.id} to {user.email}: {user.username}, {message}")
    return False
