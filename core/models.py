from django.db import models
import uuid
from django.conf import settings
from . import plans
from .mixins import PublicIDMixin, SoftDeleteModel, OwnedModel
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta
from django.core.exceptions import PermissionDenied
# from .permissions import can_add_field_to_object, can_create_custom_object
# Create your models here.

#------------------------------------------ User Profile Model Starts ------------------------------------------

class UserProfile(models.Model):
    first_name = models.CharField(max_length=25, blank=True, null=True)
    last_name = models.CharField(max_length=25, default = "LastName")
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    plan = models.ForeignKey(plans.Plan, on_delete=models.PROTECT, null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # api_calls_today = models.PositiveIntegerField(default=0)
    # api_calls_limit = models.PositiveIntegerField(default=25)
    api_reset_at = models.DateTimeField(default=now)
    
    api_calls_used = models.IntegerField(default=0)
    records_used = models.IntegerField(default=0)

    organization_name = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def has_api_quota(self):
        return self.plan and self.api_calls_used < self.plan.monthly_api_limit

    def has_record_quota(self):
        return self.plan and self.records_used < self.plan.max_records
    
    def save(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        if user and not user.is_superuser:
            raise PermissionDenied("User profile changes restricted")
        super().save(*args, **kwargs)

    def __str__(self):
        plan_name = self.plan.name if self.plan else "No Plan"
        return f"{self.user} → {plan_name}"
    
User = settings.AUTH_USER_MODEL

class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(default=now)
    is_used = models.BooleanField(default=False)


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(default=now)
    is_used = models.BooleanField(default=False)
    
#------------------------------------------ User Profile Model Starts ------------------------------------------

#------------------------------------------ Customer Profile Model Starts ------------------------------------------
#User Roles enum
class UserRole(models.TextChoices):
    QA = "QA", "Qa"
    USER = "USER", "User"
    DEVELOPER = "DEVELOPER", "Developer"
    PRODUCTMANAGER = "PRODUCT MANAGER", "Product Manager"
    TEAMLEAD = "TEAM LEAD", "Team Lead"

#CustomerProfile Model
class CustomerProfile(PublicIDMixin, SoftDeleteModel, OwnedModel):
    user_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    full_name = models.CharField(max_length = 50, db_index=True)
    username = models.CharField(max_length=50, unique=True, db_index=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    is_email_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=UserRole.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_ip = models.GenericIPAddressField()

    def __str__(self):
        return self.username
#------------------------------------------ User Profile Model Ends ------------------------------------------    


#------------------------------------------ Product Catalog Model Starts ------------------------------------------
# Defining Currency Enum
class Currency(models.TextChoices):
    INR = "INR", "Indian Rupee"
    USD = "USD", "US Dollar"
    EUR = "EUR", "Euro"
    
# Creating the product catalog model
class ProductCatalog(PublicIDMixin, SoftDeleteModel, OwnedModel):
#     user = models.ForeignKey(
#     settings.AUTH_USER_MODEL,
#     on_delete=models.CASCADE,
#     null=False,
#     blank=False,
#     related_name="products",
# )
    product_id = models.CharField(max_length=30)
    product_name = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, choices=Currency.choices)
    in_stock = models.BooleanField(default=True)
    stock_count = models.PositiveIntegerField()
    product_rating = models.FloatField()
    # is_platform_owned = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["created_by", "product_id"],
                condition=models.Q(is_deleted=False),
                name="unique_product_per_user"
            )
        ]
        
    def __str__(self):
        return self.product_name


#------------------------------------------ Product Catalog Model Ends ------------------------------------------


#------------------------------------------ Order Transaction Model Starts ------------------------------------------
#Defining Payment Methods and Payment Status enum
class PaymentMethod(models.TextChoices):
    CARD = "CARD", "Card"
    UPI = "UPI", "UPI"
    NET_BANKING = "NET_BANKING", "Net Banking"
    
class PaymentStatus(models.TextChoices):
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    PENDING = "PENDING", "Pending"
    
# Creating the order transaction model
class OrderTransaction(PublicIDMixin, SoftDeleteModel, OwnedModel):
    order_id = models.CharField(max_length=30, unique=True, db_index=True)
    order_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices)
    transaction_reference = models.CharField(max_length=50)
    is_refundable = models.BooleanField(default=False)
    order_date = models.DateField()
    discount_applied = models.FloatField(help_text="Percentage value")

    def __str__(self):
        return self.order_id
    
#------------------------------------------ Order Transaction Model Ends ------------------------------------------


#------------------------------------------ System Log Model Starts ------------------------------------------
# Creating the log-level-enum
class LogLevel(models.TextChoices):
    INFO = "INFO", "Info"
    WARNING = "WARNING", "Warning"
    ERROR = "ERROR", "Error"
    CRITICAL = "CRITICAL", "Critical"
    
#Creating the System Log class
class SystemLog(PublicIDMixin, SoftDeleteModel, OwnedModel):
    log_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    service_name = models.CharField(max_length=50)
    log_level = models.CharField(max_length=20, choices=LogLevel.choices)
    message = models.TextField()
    request_path = models.CharField(max_length=255)
    http_status = models.PositiveSmallIntegerField()
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)
    user_ip_address = models.GenericIPAddressField(null=True)

    def __str__(self):
        return f"{self.service_name} - {self.log_level}"
    
#------------------------------------------ System Log Model Ends ------------------------------------------    


#------------------------------------------ FeatureUsageAnalytics Model Starts -----------------------------
class FeatureUsageAnalytics(PublicIDMixin, SoftDeleteModel, OwnedModel):
    event_id = models.CharField(max_length=30, unique=True)
    feature_name = models.CharField(max_length=100)
    api_calls_made = models.PositiveIntegerField()
    data_volume_mb = models.FloatField()
    success_rate = models.FloatField(help_text="Percentage value")
    throttled = models.BooleanField(default=False)
    client_app = models.CharField(max_length=50)
    event_timestamp = models.DateTimeField()

    def __str__(self):
        return self.feature_name
    
#------------------------------------------ FeatureUsageAnalytics Model Ends ------------------------------------------


# Create your models here.
class CustomObject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="custom_objects",
    )

    name = models.CharField(max_length=100)
    api_name = models.SlugField(max_length=50)

    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)

    max_records = models.PositiveIntegerField(default=1000)
    allow_api_access = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("tenant", "api_name")

    def __str__(self):
        return f"{self.api_name}"
    
    # def clean(self):
    #     if not can_create_custom_object(self.tenant):
    #         raise ValidationError("Custom Object limit exceeded.")
    

class CustomField(models.Model):
    DATA_TYPES = [
        ("STRING", "String"),
        ("NUMBER", "Number"),
        ("DECIMAL", "Decimal"),
        ("BOOLEAN", "Boolean"),
        ("DATE", "Date"),
        ("DATETIME", "Datetime"),
        ("EMAIL", "Email"),
        ("JSON", "JSON"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    custom_object = models.ForeignKey(
        CustomObject,
        on_delete=models.CASCADE,
        related_name="fields",
    )

    name = models.CharField(max_length=100)
    api_name = models.SlugField(max_length=50)

    data_type = models.CharField(max_length=20, choices=DATA_TYPES)

    is_required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    is_indexed = models.BooleanField(default=False)

    default_value = models.TextField(blank=True, null=True)
    min_value = models.DecimalField(
        max_digits=18, decimal_places=6, null=True, blank=True
    )
    max_value = models.DecimalField(
        max_digits=18, decimal_places=6, null=True, blank=True
    )
    regex = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("custom_object", "api_name")

    def __str__(self):
        return f"{self.custom_object.api_name}.{self.api_name}"


class CustomObjectRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="custom_records",
    )

    object_api_name = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CustomFieldValue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    record = models.ForeignKey(
        CustomObjectRecord,
        on_delete=models.CASCADE,
        related_name="field_values",
    )

    field_api_name = models.CharField(max_length=50)

    value_string = models.TextField(null=True, blank=True)
    value_number = models.BigIntegerField(null=True, blank=True)
    value_decimal = models.DecimalField(
        max_digits=18, decimal_places=6, null=True, blank=True
    )
    value_boolean = models.BooleanField(null=True, blank=True)
    value_date = models.DateField(null=True, blank=True)
    value_datetime = models.DateTimeField(null=True, blank=True)
    value_json = models.JSONField(null=True, blank=True)
    
    
    

