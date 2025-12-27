from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

def get_user_plan(user):
    if not hasattr(user, "profile"):
        return None
    return user.profile.plan


def can_create(user):
    plan = get_user_plan(user)
    return bool(plan and plan.can_create_records)


def can_update(user):
    plan = get_user_plan(user)
    return bool(plan and plan.can_update_records)


def can_delete(user):
    plan = get_user_plan(user)
    return bool(plan and plan.can_delete_records)


def can_bulk(user):
    plan = get_user_plan(user)
    return bool(plan and plan.allow_bulk_operations)

def check_and_consume_api_call(profile):
    """
    Raises exception if limit exceeded.
    Otherwise increments usage.
    """

    # Reset monthly quota
    if now() >= profile.api_reset_at:
        profile.api_calls_used = 0
        profile.api_reset_at = now() + relativedelta(months=1)

    if profile.api_calls_used >= profile.plan.monthly_api_limit:
        return False

    profile.api_calls_used += 1
    profile.save(update_fields=["api_calls_used", "api_reset_at"])
    return True

def send_verification_email(user, token):
    verify_url = (
        settings.SITE_URL +
        reverse("verify_email") +
        f"?token={token}"
    )

    subject = "Verify your email address"
    message = f"""
Hello {user.email},

Your account has been created.

Please verify your email by clicking the link below:

{verify_url}

If you did not request this, you can ignore this email.
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
