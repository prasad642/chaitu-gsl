from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=User)
def prevent_multiple_admins(sender, instance, **kwargs):
    if not instance.is_staff and not instance.is_superuser:
        return

    existing_admins = User.objects.filter(is_staff=True)
    if instance.pk:
        existing_admins = existing_admins.exclude(pk=instance.pk)

    if existing_admins.exists():
        raise ValidationError('Only one website admin account is allowed.')
