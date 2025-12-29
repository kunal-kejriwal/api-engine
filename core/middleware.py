from django.http import JsonResponse
import time
from django.utils.timezone import now
from django.contrib.auth.models import AnonymousUser
from core.models import SystemLog
from django.db import models
from django.shortcuts import redirect
from django.urls import reverse

class PlanNamespaceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(("/admin", "/accounts", "/static")):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required"}, status=401)

        profile = getattr(request.user, "profile", None)
        if not profile or not profile.is_active:
            return JsonResponse({"detail": "Inactive account"}, status=403)

        plan = profile.plan
        namespace = request.path.strip("/").split("/")[0]

        if "*" not in plan.allowed_namespaces and namespace not in plan.allowed_namespaces:
            return JsonResponse(
                {"detail": "Upgrade required to access this endpoint"},
                status=403
            )

        if plan.name == "FREE" and request.method != "GET":
            return JsonResponse(
                {"detail": "Read-only access"},
                status=403
            )

        return self.get_response(request)
    

class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)

        if request.path.startswith(("/core/api/", "/core/api/v1/")):
            self.log_request(request, response, start_time)

        return response

    def log_request(self, request, response, start_time):
        user = request.user if request.user.is_authenticated else None
        client_ip = request.META.get("REMOTE_ADDR")
        duration_ms = int((time.time() - start_time) * 1000)
        
        error_message = None

        # Safe extraction for DRF responses
        if response.status_code >= 400 and hasattr(response, "data"):
            if isinstance(response.data, dict):
                error_message = response.data.get("detail")

        message = (
            f"{request.method} {request.path} | "
            f"status={response.status_code}"
            + (f" | error={error_message}" if error_message else "")
        )

        try:
            SystemLog.objects.create(
                created_by=user,  # ✅ THIS is the fix
                service_name="API",
                log_level="INFO" if response.status_code < 400 else "ERROR",
                message=f"{request.method} {request.path}",
                request_path=request.path,
                http_status=response.status_code,
                response_time_ms=duration_ms,
                user_ip_address=client_ip,
            )
        except Exception:
            # logging must never break requests
            pass
        

class EmailVerifiedAccessMiddleware:

    PUBLIC_PREFIXES = (
        "/blogs/",
    )

    AUTH_PREFIXES = (
        "/auth/",
        "/rest/auth/",
    )

    API_PREFIXES = (
    "/api/",
    "/core/api/",
    "/core/v1/",
)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

    # 🚨 CRITICAL: Skip API routes entirely
        if path.startswith(self.API_PREFIXES):
            return self.get_response(request)

        # 1️⃣ Admin
        if path.startswith("/admin/"):
            return self.get_response(request)

        # 2️⃣ Homepage
        if path == "/":
            return self.get_response(request)

        # 3️⃣ Public
        if path.startswith(self.PUBLIC_PREFIXES):
            return self.get_response(request)

        # 4️⃣ Anonymous users (browser only)
        if not request.user.is_authenticated:
            if path.startswith(self.AUTH_PREFIXES):
                return self.get_response(request)

            return redirect(settings.LOGIN_URL)

        # 5️⃣ Logged in but NOT email verified (browser only)
        profile = getattr(request.user, "profile", None)

        if profile and not profile.is_email_verified:
            if path.startswith(self.AUTH_PREFIXES):
                return self.get_response(request)

            return redirect("/auth/confirm-email/")

        return self.get_response(request)
