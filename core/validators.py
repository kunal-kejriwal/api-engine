from django.apps import apps
from rest_framework import serializers
from core.plan_limits import PLAN_RECORD_LIMITS, QUOTA_MODELS, QUOTA_MODEL_OWNERSHIP


def enforce_record_quota(user, incoming_count=1):
    """
    Enforces record creation limit based on user's plan.
    Respects soft deletes automatically via SoftDeleteManager.
    """

    profile = user.profile
    plan = profile.plan

    if not plan:
        raise serializers.ValidationError("No plan assigned to user.")

    plan_name = plan.name.upper()
    max_records = PLAN_RECORD_LIMITS.get(plan_name)

    if max_records is None:
        raise serializers.ValidationError("Invalid plan configuration.")

    total_existing = 0

    for model_path in QUOTA_MODELS:
        try:
            app_label, model_name = model_path.rsplit(".", 1)
            model = apps.get_model(app_label, model_name)

            owner_field = QUOTA_MODEL_OWNERSHIP.get(model_path)

            if not owner_field:
                continue  # Skip models without ownership definition

            if not hasattr(model, owner_field):
                continue  # Safety check

            total_records += model.objects.filter(
                **{owner_field: user}
            ).count()
        except Exception as e:
            print(f"[Quota Error] {model_path}: {e}")
            continue

    if total_existing + incoming_count > max_records:
        raise serializers.ValidationError(
            {
                "error_code": "RECORD_LIMIT_EXCEEDED",
                "message": (
                    f"{plan_name} plan allows a maximum of "
                    f"{max_records} active records. "
                    f"You currently have {total_existing}."
                )
            }
        )
