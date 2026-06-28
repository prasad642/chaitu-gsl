from django.core.management.base import BaseCommand
from django.utils import timezone

from studentapp.models import ContactMessage


class Command(BaseCommand):
    help = 'Delete contact messages older than 24 hours.'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timezone.timedelta(hours=24)
        deleted_count, _ = ContactMessage.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} old contact messages.'))
