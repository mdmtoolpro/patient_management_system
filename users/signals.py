from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import StaffProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a StaffProfile automatically when a new User is created"""
    if created:
        StaffProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the profile when the user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # If profile doesn't exist, create it
        StaffProfile.objects.get_or_create(user=instance)