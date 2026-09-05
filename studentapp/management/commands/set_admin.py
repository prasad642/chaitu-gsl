from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create or update the single superuser admin account.'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='chaitu_9493', help='Admin username')
        parser.add_argument('--password', type=str, default='12341234', help='Admin password')
        parser.add_argument('--email', type=str, default='admin@incendios.local', help='Admin email')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        # Find any existing superuser or staff
        existing_admin = User.objects.filter(is_staff=True).first() or User.objects.filter(username=username).first()

        if existing_admin:
            existing_admin.username = username
            existing_admin.email = email
            existing_admin.is_staff = True
            existing_admin.is_superuser = True
            existing_admin.set_password(password)
            existing_admin.save()
            self.stdout.write(self.style.SUCCESS(f'Admin user "{username}" updated successfully with the new password.'))
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Admin superuser "{username}" created successfully.'))
