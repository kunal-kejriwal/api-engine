from rest_framework.throttling import BaseThrottle
from django.utils import timezone
from dateutil.relativedelta import relativedelta

class PlanBasedUserThrottle(BaseThrottle):
    """
    Monthly API quota based on user's subscription plan
    """

    def allow_request(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        profile = getattr(user, "profile", None)
        if not profile or not profile.plan:
            return False

        now = timezone.now()

        # 🔁 Reset monthly quota window
        if not profile.api_reset_at or now >= profile.api_reset_at:
            profile.api_calls_used = 0
            profile.api_reset_at = now + relativedelta(months=1)
            profile.save(update_fields=["api_calls_used", "api_reset_at"])

        # ❌ Do NOT increment here
        if profile.api_calls_used >= profile.plan.monthly_api_limit:
            return False

        return True

    def wait(self):
        return None
