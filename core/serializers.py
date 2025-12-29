from rest_framework import serializers
from .models import CustomerProfile, ProductCatalog, OrderTransaction, SystemLog, FeatureUsageAnalytics, CustomObject, CustomField
from django.db.models import Count
from core.validators import enforce_record_quota
from .mixins import RecordQuotaValidationMixin

#-------------------CustomerProfile Serializer Starts---------------
class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = [
            "user_id",
            "full_name",
            "username",
            "email",
            "phone_number",
            "is_email_verified",
            "role",
            "created_at",
            "last_login_ip",
        ]
#-------------------CustomerProfile Serializer Ends---------------

#-------------------ProductCatalogSerializer Serializer Starts---------------
class ProductCatalogSerializer(RecordQuotaValidationMixin, serializers.ModelSerializer):
    
    class Meta:
        model = ProductCatalog
        fields = [
            "product_id",
            "product_name",
            "category",
            "price",
            "currency",
            "in_stock",
            "stock_count",
            "product_rating",
        ]       
    
#-------------------ProductCatalogSerializer Ends---------------

#-------------------OrderTransactionSerializer Starts---------------
class OrderTransactionSerializer(RecordQuotaValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = OrderTransaction
        fields = [
            'order_id',
            'order_amount',
            'payment_method',
            'payment_status',
            'transaction_reference',
            'is_refundable',
            'order_date',
            'discount_applied',
        ]
#-------------------OrderTransactionSerializer Ends---------------

#-------------------SystemLogSerializer Starts---------------     
class SystemLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemLog
        fields = [
            'log_id',
            'service_name',
            'log_level',
            'message',
            'request_path',
            'http_status',
            'response_time_ms',
            'logged_at',
        ]
#-------------------SystemLogSerializer Ends---------------

#-------------------FeatureUsageAnalyticsSerializer  Starts---------------
class FeatureUsageAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureUsageAnalytics
        fields = [
            'event_id',
            'feature_name',
            'api_calls_made',
            'data_volume_mb',
            'success_rate',
            'throttled',
            'client_app',
            'event_timestamp',
        ]
#-------------------FeatureUsageAnalyticsSerializer  Ends---------------


class CustomObjectSerializer(RecordQuotaValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = CustomObject
        fields = ["id", "name", "api_name", "description"]


class CustomFieldSerializer(RecordQuotaValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = CustomField
        fields = [
            "id",
            "name",
            "api_name",
            "data_type",
            "is_required",
            "is_unique",
            "default_value",
            "min_value",
            "max_value",
            "regex",
        ]