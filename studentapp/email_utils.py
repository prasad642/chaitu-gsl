from django.conf import settings
from django.core.mail import send_mail as django_send_mail
import requests


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

    payload = {
        'sender': {
            'email': sender_email,
            'name': getattr(settings, 'BREVO_SENDER_NAME', 'Incendios'),
        },
        'to': [{'email': email} for email in recipients],
        'subject': subject,
        'textContent': message,
    }
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
    if response.status_code >= 400:
        raise EmailDeliveryError(f'Brevo API error {response.status_code}: {response.text}')

    return 1
