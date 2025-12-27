# core/billing.py (or models.py)

from django.db import models
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta
from django.conf import settings
from .plans import Plan

class Subscription(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("PAST_DUE", "Past Due"),
        ("CANCELLED", "Cancelled"),
        ("EXPIRED", "Expired"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription"
    )

    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    valid_from = models.DateTimeField(default=now)
    valid_till = models.DateTimeField()

    last_payment_id = models.CharField(max_length=255, blank=True, null=True)

    def is_active(self):
        return self.status == "ACTIVE" and now() <= self.valid_till
