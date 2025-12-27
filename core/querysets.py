from django.db import models
from django.contrib.auth.models import User

def owned_queryset(queryset, user):
    if user.is_superuser:
        return queryset

    return queryset.filter(
        models.Q(created_by=user) |
        models.Q(is_platform_owned=True),
        is_deleted=False,
    )