from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from core.models import UserProfile
from core.plans import Plan

@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    if not hasattr(instance, "profile"):
        free_plan = Plan.objects.get(name="FREE")
        UserProfile.objects.create(
            user=instance,
            plan=free_plan
        )
