from django.db import models
from django.core.exceptions import PermissionDenied

class Plan(models.Model):
    PLAN_CHOICES = [
        ("FREE", "Free"),
        ("BASE", "Base"),
        ("DEVELOPER", "Developer"),
        ("ENTERPRISE", "Enterprise"),
    ]

    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    
    allowed_namespaces = models.JSONField(default=list)

    # API limits
    monthly_api_limit = models.IntegerField()
    max_records = models.IntegerField()
    max_records_per_query = models.IntegerField()

    # Object & schema capabilities
    can_create_records = models.BooleanField(default=False)
    can_update_records = models.BooleanField(default=False)
    can_delete_records = models.BooleanField(default=False)
    can_create_custom_objects = models.BooleanField(default=False)
    max_custom_objects = models.IntegerField(default=0)

    # Query permissions
    allow_filters = models.BooleanField(default=False)
    allow_sorting = models.BooleanField(default=False)
    allow_bulk_operations = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        if user and not user.is_superuser:
            raise PermissionDenied("Plans can only be modified by admins")
        super().save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        raise PermissionDenied("Plans cannot be deleted")
