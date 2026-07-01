from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Print safe email configuration status without revealing secrets.'

    def handle(self, *args, **options):
        has_api_key = bool(getattr(settings, 'BREVO_API_KEY', ''))
        sender_email = getattr(settings, 'BREVO_SENDER_EMAIL', '') or settings.DEFAULT_FROM_EMAIL

        self.stdout.write(f"method={'Brevo API' if has_api_key else 'SMTP'}")
        self.stdout.write(f"brevo_api_key_set={has_api_key}")
        self.stdout.write(f"brevo_sender_email_set={bool(sender_email)}")
        self.stdout.write(f"brevo_sender_email={sender_email or '(missing)'}")
        self.stdout.write(f"email_host={settings.EMAIL_HOST}")
        self.stdout.write(f"email_port={settings.EMAIL_PORT}")
        self.stdout.write(f"email_use_tls={settings.EMAIL_USE_TLS}")
        self.stdout.write(f"email_timeout={settings.EMAIL_TIMEOUT}")
