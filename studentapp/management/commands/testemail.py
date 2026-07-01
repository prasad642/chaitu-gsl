from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from smtplib import SMTPAuthenticationError
import socket


class Command(BaseCommand):
    help = 'Send a test email using the active Django email settings.'

    def add_arguments(self, parser):
        parser.add_argument('recipient', help='Email address that should receive the test email.')

    def handle(self, *args, **options):
        recipient = options['recipient']

        missing = []
        if not settings.EMAIL_HOST_USER:
            missing.append('EMAIL_HOST_USER')
        if not settings.EMAIL_HOST_PASSWORD:
            missing.append('EMAIL_HOST_PASSWORD')

        if missing:
            raise CommandError(
                'Email is not configured. Missing: '
                + ', '.join(missing)
                + '. Create studentproject/email_settings.py or set environment variables.'
            )

        try:
            sent_count = send_mail(
                'Incendios email test',
                'If you received this, Django email sending is working.',
                settings.EMAIL_HOST_USER,
                [recipient],
                fail_silently=False,
            )
        except SMTPAuthenticationError as exc:
            details = ''
            if len(exc.args) > 1:
                details = exc.args[1].decode(errors='ignore') if isinstance(exc.args[1], bytes) else str(exc.args[1])
            if 'Unauthorized IP address' in details:
                raise CommandError(
                    'Brevo rejected this server IP address. Add this server IP to Brevo authorized IPs, '
                    'or switch EMAIL_HOST settings to an approved SMTP provider.'
                ) from exc
            detail_text = details or str(exc)
            raise CommandError(
                f'SMTP login failed. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD. {detail_text}'
            ) from exc
        except (TimeoutError, socket.timeout) as exc:
            raise CommandError(
                'SMTP connection timed out. Check EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS, '
                'and whether your hosting provider can reach the SMTP server.'
            ) from exc

        self.stdout.write(self.style.SUCCESS(f'Sent {sent_count} email(s) to {recipient}.'))
