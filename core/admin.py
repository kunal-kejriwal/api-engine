from django.contrib import admin
from .models import CustomerProfile, ProductCatalog, OrderTransaction, SystemLog, FeatureUsageAnalytics, UserProfile
from .plans import Plan

# Register your models here.
admin.site.register(CustomerProfile)
admin.site.register(OrderTransaction)
admin.site.register(FeatureUsageAnalytics)

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = (
        "log_id",
        "service_name",
        "log_level",
        "http_status",
        "created_by",
        "logged_at",
    )
    search_fields = ("log_id", "request_path", "message")

@admin.register(ProductCatalog)
class ProductCatalogAdmin(admin.ModelAdmin):
    list_display = (
        "product_name",
        "product_id",
        "public_id",      # 👈 show in list view
        "created_by",
        "is_deleted",
    )

    readonly_fields = (
        "public_id",      # 👈 visible but not editable
        "created_at",
        "deleted_at",
    )

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "monthly_api_limit", "max_records")

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "api_calls_used", "api_reset_at")
    readonly_fields = ("created_at",)

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
