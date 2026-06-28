import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create or update the single admin user from environment variables.'

    def handle(self, *args, **options):
        username = os.environ.get('ADMIN_USERNAME', '').strip()
        password = os.environ.get('ADMIN_PASSWORD', '').strip()
        email = os.environ.get('ADMIN_EMAIL', '').strip()

        if not username or not password:
            self.stdout.write(
                self.style.WARNING(
                    'Skipping admin setup because ADMIN_USERNAME or ADMIN_PASSWORD is not set.'
                )
            )
            return

        User = get_user_model()
        admin_user = (
            User.objects.filter(is_staff=True).first()
            or User.objects.filter(username=username).first()
        )

        if admin_user is None:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user "{username}".'))
            return

        admin_user.username = username
        if email:
            admin_user.email = email
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password(password)
        admin_user.save()
        self.stdout.write(self.style.SUCCESS(f'Updated admin user "{username}".'))
