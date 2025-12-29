from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework import status
from core.models import SystemLog
from django.db import IntegrityError

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    request = context.get("request")
    
    if isinstance(exc, Throttled):
        # Log safely
        SystemLog.objects.create(
            service_name="API",
            log_level="WARNING",
            message="API rate limit exceeded",
            request_path=request.path,
            http_status=429,
            response_time_ms=0,
            created_by=request.user if request.user.is_authenticated else None,
        )

        return Response(
            {
                "detail": "API limit reached for your plan",
                "current_plan": request.user.profile.plan.name,
                "limit": request.user.profile.plan.monthly_api_limit,
                "reset_at": request.user.profile.api_reset_at,
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
        
    if isinstance(exc, IntegrityError):
        return Response(
            {
                "error_code": "DUPLICATE_RESOURCE",
                "message": "Resource already exists."
            },
            status=400,
        )
    
    if response is not None:
        request = context.get("request")
        user = request.user if request and request.user.is_authenticated else None

        SystemLog.objects.create(
            created_by=user,
            service_name="API",
            log_level="ERROR",
            message=f"API error: {exc.__class__.__name__}",
            request_path=request.path if request else "",
            http_status=response.status_code,
        )

    return response