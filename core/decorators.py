from functools import wraps
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.shortcuts import redirect

def plan_required(*, can_create=False, can_update=False, can_delete=False):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            profile = request.user.profile
            plan = profile.plan
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # 🔑 SAFE profile access
            if not profile:
                return HttpResponseForbidden(
                    "User profile missing. Contact support."
                )
            
            if can_create and not plan.can_create_records:
                return HttpResponseForbidden(
                    "Upgrade your plan to perform this action."
                )

            if can_update and not plan.can_update_records:
                return HttpResponseForbidden(
                    "Upgrade your plan to update records."
                )

            if can_delete and not plan.can_delete_records:
                return HttpResponseForbidden(
                    "Upgrade your plan to delete records."
                )

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def api_quota_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        profile = request.user.profile

        from core.utils import check_and_consume_api_call

        if not check_and_consume_api_call(profile):
            return JsonResponse(
                {"detail": "API quota exceeded for your plan"},
                status=429,
            )

        return view_func(request, *args, **kwargs)

    return _wrapped_view

def verified_user_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.profile.is_email_verified:
            return redirect("verify_email_notice")
        return view_func(request, *args, **kwargs)
    return wrapper
