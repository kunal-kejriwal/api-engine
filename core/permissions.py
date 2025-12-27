# core/permissions.py

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

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

        if profile and not profile.email_verified:
            raise PermissionDenied("EMAIL_NOT_VERIFIED")

        return True
