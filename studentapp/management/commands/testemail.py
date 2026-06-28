from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


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

        sent_count = send_mail(
            'Incendios email test',
            'If you received this, Django email sending is working.',
            settings.EMAIL_HOST_USER,
            [recipient],
            fail_silently=False,
        )

        self.stdout.write(self.style.SUCCESS(f'Sent {sent_count} email(s) to {recipient}.'))
