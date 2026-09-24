from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Every User gets a Profile, however it was created.

    Without this, accounts made by createsuperuser or by the signup form
    have no role and every admin_panel page raises Profile.DoesNotExist.
    """
    if created:
        role = (
            Profile.ROLE_ADMIN if instance.is_superuser
            else Profile.ROLE_SEEKER
        )
        Profile.objects.create(user=instance, role=role)
