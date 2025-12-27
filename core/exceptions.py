from rest_framework.views import exception_handler
from core.models import SystemLog

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

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