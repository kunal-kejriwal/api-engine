from rest_framework.throttling import BaseThrottle
from django.utils import timezone
from django.db.models import F
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

        # 🔁 Reset monthly quota
        if not profile.api_reset_at or now >= profile.api_reset_at:
            profile.api_calls_used = 0
            profile.api_reset_at = now + relativedelta(months=1)
            profile.save(update_fields=["api_calls_used", "api_reset_at"])

        if profile.api_calls_used >= profile.plan.monthly_api_limit:
            return False

        # ✅ Atomic increment
        profile.__class__.objects.filter(
            pk=profile.pk
        ).update(api_calls_used=F("api_calls_used") + 1)

        return True

    def wait(self):
        return None
