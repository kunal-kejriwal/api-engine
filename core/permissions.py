# core/permissions.py

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from core.plan_limits import PLAN_CUSTOM_OBJECT_LIMITS 
from .models import CustomObject, CustomField

class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)
    

class IsEmailVerified(BasePermission):
    """
    Allows access only to users with verified email and active account.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if not user.is_active:
            raise PermissionDenied("ACCOUNT_INACTIVE")

        profile = getattr(user, "profile", None)

        if profile and not profile.is_email_verified:
            raise PermissionDenied("EMAIL_NOT_VERIFIED")

        return True
    

def get_plan_limits(user):
    plan_name = user.profile.plan.name.upper()
    return PLAN_CUSTOM_OBJECT_LIMITS.get(plan_name, {})

def can_create_custom_object(user):
    limits = get_plan_limits(user)
    max_objects = limits.get("max_objects", 0)

    current_count = CustomObject.objects.filter(
        tenant=user,
        is_active=True,
    ).count()

    return current_count < max_objects

def can_add_field_to_object(user, custom_object):
    limits = get_plan_limits(user)
    max_fields = limits.get("max_fields_per_object", 0)

    current_fields = CustomField.objects.filter(
        custom_object=custom_object
    ).count()

    return current_fields < max_fields
