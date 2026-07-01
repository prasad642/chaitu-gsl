from django.conf import settings
from django.core.mail import send_mail as django_send_mail
import logging
import requests
from requests import RequestException, Timeout


logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    pass


def send_app_email(subject, message, recipients):
    if getattr(settings, 'BREVO_API_KEY', ''):
        return send_brevo_api_email(subject, message, recipients)

    return django_send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False,
    )


def send_brevo_api_email(subject, message, recipients):
    sender_email = getattr(settings, 'BREVO_SENDER_EMAIL', '') or settings.DEFAULT_FROM_EMAIL
    if not sender_email:
        raise EmailDeliveryError('Brevo sender email is missing. Set BREVO_SENDER_EMAIL or EMAIL_HOST_USER.')
    if sender_email.endswith('@smtp-brevo.com'):
        raise EmailDeliveryError(
            'Brevo sender email is invalid. Set BREVO_SENDER_EMAIL to a sender address verified in Brevo, '
            'not the SMTP login address.'
        )

    payload = {
        'sender': {
            'email': sender_email,
            'name': getattr(settings, 'BREVO_SENDER_NAME', 'Incendios'),
        },
        'to': [{'email': email} for email in recipients],
        'subject': subject,
        'textContent': message,
    }
    try:
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={
                'accept': 'application/json',
                'api-key': settings.BREVO_API_KEY,
                'content-type': 'application/json',
            },
            json=payload,
            timeout=getattr(settings, 'EMAIL_TIMEOUT', 25),
        )
    except Timeout as exc:
        raise EmailDeliveryError('Brevo API request timed out. Check Railway outbound HTTPS access and try again.') from exc
    except RequestException as exc:
        raise EmailDeliveryError(f'Brevo API request failed: {exc}') from exc

    if response.status_code >= 400:
        raise EmailDeliveryError(f'Brevo API error {response.status_code}: {response.text}')

    try:
        response_data = response.json()
    except ValueError:
        response_data = {}
    message_id = response_data.get('messageId', 'unknown')
    logger.info('Brevo API accepted email messageId=%s recipients=%s', message_id, ','.join(recipients))
    print(f'Brevo API accepted email messageId={message_id} recipients={",".join(recipients)}')

    return 1
