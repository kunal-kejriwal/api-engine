from django.db.models import F

def increment_api_usage(user):
    user.profile.__class__.objects.filter(
        pk=user.profile.pk
    ).update(api_calls_used=F("api_calls_used") + 1)