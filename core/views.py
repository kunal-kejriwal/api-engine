from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.apps import apps
from .models import CustomerProfile, ProductCatalog, OrderTransaction, SystemLog, FeatureUsageAnalytics, UserProfile, EmailVerificationToken, PasswordResetToken, CustomObject, CustomField, CustomFieldValue, CustomObjectRecord
from .serializers import CustomerProfileSerializer, ProductCatalogSerializer, OrderTransactionSerializer, CustomObjectSerializer, CustomFieldSerializer
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from .filters import CustomerProfileFilter, ProductCatalogFilter
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from .forms import ProductCatalogForm
from .plans import Plan
from core.decorators import plan_required, api_quota_required
from core.querysets import owned_queryset
from core.throttles import PlanBasedUserThrottle
from .permissions import IsSuperUser, get_plan_limits, can_add_field_to_object, can_create_custom_object, IsEmailVerified
from .paginations import PlanBasedPagination
from django.core.paginator import Paginator
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import NotAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from django.contrib import messages
from core.utils import send_verification_email
from core.plan_limits import PLAN_RECORD_LIMITS, QUOTA_MODELS
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from .usage import increment_api_usage


# Create your views here.

def core_home(request):    
    return render(request, 'core/homepage.html')

def login_view(request):
    return render(request, "core/login-page.html")

def redirect_core(request):
    return redirect('/')

def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        errors = []

        if not username:
            errors.append("Username is required.")

        if not email:
            errors.append("Email is required.")

        if not password:
            errors.append("Password is required.")

        if User.objects.filter(username=username).exists():
            errors.append("Username already exists. Please opt for a different username.")

        if User.objects.filter(email=email).exists():
            errors.append("An account with this email already exists. Please opt for a different email.")

        # ⛔ STOP execution if errors exist
        if errors:
            return render(
                request,
                "core/signup.html",
                {
                    "errors": errors,
                    "username": username,
                    "email": email,
                },
            )

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
        except IntegrityError:
            return render(
                request,
                "core/signup.html",
                {
                    "errors": ["Something went wrong. Please try again."],
                },
            )

        # Profile creation (FIXED)
        free_plan = Plan.objects.get(name="FREE")
        UserProfile.objects.create(
            user=user,
            plan=free_plan,
        )

        token = EmailVerificationToken.objects.create(user=user)
        send_verification_email(user, token.token)

        login(request, user)
        return redirect("home")

    return render(request, "core/signup.html")

@login_required
def verify_email_page(request):
    profile = request.user.profile

    if profile.is_email_verified:
        return redirect("/core/account/details")

    return render(request, "core/confirm-email.html")

@login_required
def verify_email_view(request):
    token = request.GET.get("token")

    if not token:
        messages.error(request, "Invalid verification link.")
        return redirect("/auth/confirm-email/")

    try:
        record = EmailVerificationToken.objects.get(
            token=token,
            is_used=False
        )
    except EmailVerificationToken.DoesNotExist:
        messages.error(
            request,
            "This verification link is invalid or has already been used."
        )
        return redirect("/auth/confirm-email/")

    user = record.user

    # ✅ Mark verified
    user.profile.is_email_verified = True
    user.is_active = True
    user.profile.save()

    record.is_used = True
    record.save()

    messages.success(request, "Email verified successfully")

    # ✅ Redirect to protected post-login page
    return redirect("/core/dashboard/")

@login_required
def resend_verification_email(request):
    profile = request.user.profile

    if profile.is_email_verified:
        messages.info(request, "Your email is already verified.")
        return redirect("/core/dashboard/")

    token = EmailVerificationToken.objects.create(user=request.user)

    send_verification_email(request.user, token.token)

    messages.success(
        request,
        "A new verification email has been sent."
    )

    return redirect("/auth/confirm-email/")

def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
            token = PasswordResetToken.objects.create(user=user)
            print(f"/reset-password/?token={token.token}")
        except User.DoesNotExist:
            pass

        messages.success(
            request,
            "If an account exists, a reset link has been sent."
        )
        return redirect("login")

    return render(request, "core/forgot_password.html")

def reset_password_view(request, token):
    # token = request.GET.get("token")
    
    # 🚫 No token in URL
    if not token:
        messages.error(request, "Invalid password reset link.")
        return redirect("login")

    try:
        record = get_object_or_404(
            PasswordResetToken,
            token=token,
            is_used=False
        )
    except PasswordResetToken.DoesNotExist:
        messages.error(
            request,
            "This password reset link is invalid or has expired."
        )
        return redirect("login")

    if request.method == "POST":
        new_password = request.POST.get("password")

        user = record.user
        user.set_password(new_password)
        user.save()

        record.is_used = True
        record.save()

        messages.success(request, "Password updated successfully")
        return redirect("login")

    return render(request, "core/reset_password.html")

class VerifyEmailAPIView(APIView):
    permission_classes = []

    def post(self, request):
        token = request.data.get("token")

        try:
            record = EmailVerificationToken.objects.get(
                token=token, is_used=False
            )
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"error": "INVALID_OR_EXPIRED_TOKEN"},
                status=400
            )

        user = record.user
        user.is_active = True
        user.profile.is_email_verified = True
        user.save()
        user.profile.save()

        record.is_used = True
        record.save()

        return Response({"message": "EMAIL_VERIFIED"})
    
@login_required
def api_tokens_view(request):
    access_token = None
    refresh_token = None

    if request.method == "POST":
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

    return render(
        request,
        "core/api_tokens.html",
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    )

# ----------------------------------- CustomerProfile Views Start --------------------------------------

#@api_view(["GET"])
def user_profile_get_list(request):
    user_profiles = CustomerProfile.objects.all()
    serializer = CustomerProfileSerializer(user_profiles, many=True)
    return Response(serializer.data)

class CustomerProfileAPIView(generics.ListAPIView):
    # queryset = ProductCatalog.objects.filter()
    serializer_class = CustomerProfileSerializer
    filter_backends = [DjangoFilterBackend]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsEmailVerified]
    throttle_classes = [PlanBasedUserThrottle]
    pagination_class = PlanBasedPagination
    
    def get(self, request, *args, **kwargs):
        if request.headers.get("X-Force-401") == "true":
            raise NotAuthenticated("Forced 401 via header")

        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return ProductCatalog.all_objects.all()

        return ProductCatalog.objects.filter(
            created_by=user,
            is_deleted=False,
        )
    
@login_required
def customer_profile_detail_page(request, user_id):
    profile = get_object_or_404(CustomerProfile, user_id=user_id)
    return render(
        request,
        "core/customer-profile-detail.html",
        {"profile": profile}
    )
    
@login_required
def customer_profile_list_page(request):
    profiles = CustomerProfile.objects.all()
    return render(
        request,
        "core/customer_profile_list.html",
        {"profiles": profiles}
    )

# ----------------------------------- CustomerProfile Views Ends --------------------------------------


# ----------------------------------- ProductCatalog Views Start --------------------------------------

@login_required
def product_catalog_get_all_products(request):
    sort = request.GET.get("sort")          # price | stock | rating
    order = request.GET.get("order", "asc") # asc | desc
    page_number = request.GET.get("page", 1)

    product_catalog = owned_queryset(ProductCatalog.objects.all(), request.user)

    SORT_MAP = {
        "price": "price",
        "stock": "stock_count",
        "rating": "product_rating",
    }

    if sort in SORT_MAP:
        field = SORT_MAP[sort]
        if order == "desc":
            field = f"-{field}"
        product_catalog = product_catalog.order_by(field)

    
    paginator = Paginator(product_catalog, 10)  # page size
    page_obj = paginator.get_page(page_number)
    
    context = {
        "product_catalog": page_obj,   # 👈 paginated object
        "page_obj": page_obj,
        "current_sort": sort,
        "current_order": order,
    }

    return render(
        request,
        "core/product_catalog_list.html",
        context
    )


class ProductCatalogAPIView(generics.ListAPIView):
    # queryset = ProductCatalog.objects.filter()
    serializer_class = ProductCatalogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductCatalogFilter
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsEmailVerified]
    throttle_classes = [PlanBasedUserThrottle]
    pagination_class = PlanBasedPagination
    
    def get(self, request, *args, **kwargs):
        if request.headers.get("X-Force-401") == "true":
            raise NotAuthenticated("Forced 401 via header")

        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return ProductCatalog.all_objects.all()

        return ProductCatalog.objects.filter(
            created_by=user,
            is_deleted=False,
        )
        
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        if response.status_code == 200:
            increment_api_usage(request.user)

        return response
    
class ProductCatalogCreateAPIView(generics.CreateAPIView):
    serializer_class = ProductCatalogSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsEmailVerified]
    throttle_classes = [PlanBasedUserThrottle]
    
    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return ProductCatalog.all_objects.all()

        return ProductCatalog.objects.filter(
            created_by=user,
            is_deleted=False,
        )

    def perform_create(self, serializer):
        try:
            obj = serializer.save(created_by=self.request.user)
            increment_api_usage(self.request.user)
            return obj
        except IntegrityError:
            raise ValidationError(
                {"product_id": ["A product with this product_id already exists."]}
            )
    
@login_required
@plan_required(can_create=True)
def create_product_view(request):
    if request.method == "POST":
        form = ProductCatalogForm(request.POST, user=request.user)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
            
            profile = request.user.profile
            profile.api_calls_used = F("api_calls_used") + 1
            profile.save(update_fields=["api_calls_used"])

            return redirect("get_all_products")
    else:
        form = ProductCatalogForm()

    return render(
        request,
        "core/create-product.html",
        {"form": form}
    )

# ----------------------------------- ProductCatalog Views Ends --------------------------------------

@login_required
def account_detail_view(request):
    user = request.user
    profile = user.profile
    plan = profile.plan

    plan_name = plan.name.upper() if plan else "FREE"
    max_records = PLAN_RECORD_LIMITS.get(plan_name, 0)

    # 🔑 Global record count (respects soft delete)
    total_records = 0

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

    records_remaining = max(max_records - total_records, 0)

    context = {
        "user": user,
        "profile": profile,
        "plan": plan,
        "plan_name": plan_name,

        # API usage
        "api_used": profile.api_calls_used,
        "api_limit": plan.monthly_api_limit if plan else 0,
        "api_remaining": (
            plan.monthly_api_limit - profile.api_calls_used
            if plan else 0
        ),
        "api_reset_at": profile.api_reset_at,

        # Record quota
        "max_records": max_records,
        "current_records_created": total_records,
        "records_remaining": records_remaining,
    }

    return render(
        request,
        "core/account-details-page.html",
        context
    )
    


class OrderTransactionAPIView(generics.ListAPIView):
    # queryset = ProductCatalog.objects.filter()
    serializer_class = OrderTransactionSerializer
    filter_backends = [DjangoFilterBackend]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsEmailVerified]
    throttle_classes = [PlanBasedUserThrottle]
    pagination_class = PlanBasedPagination
    
    def get(self, request, *args, **kwargs):
        if request.headers.get("X-Force-401") == "true":
            raise NotAuthenticated("Forced 401 via header")

        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return ProductCatalog.all_objects.all()

        return ProductCatalog.objects.filter(
            created_by=user,
            is_deleted=False,
        )
        

@login_required
def order_transaction_list_view(request):
    sort = request.GET.get("sort")          # price | stock | rating
    order = request.GET.get("order", "asc") # asc | desc
    page_number = request.GET.get("page", 1)

    order_transactions = owned_queryset(OrderTransaction.objects.all(), request.user)

    # SORT_MAP = {
    #     "price": "price",
    #     "stock": "stock_count",
    #     "rating": "product_rating",
    # }

    # if sort in SORT_MAP:
    #     field = SORT_MAP[sort]
    #     if order == "desc":
    #         field = f"-{field}"
    #     product_catalog = product_catalog.order_by(field)

    
    paginator = Paginator(order_transactions, 10)  # page size
    order_obj = paginator.get_page(page_number)
    
    context = {
        "order_transaction": order_obj,   # 👈 paginated object
        "page_obj": order_obj,
        "current_sort": sort,
        "current_order": order,
    }

    return render(
        request,
        "core/product_catalog_list.html",
        context
    )
    
    
    
    

class CustomObjectCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def post(self, request):
        serializer = CustomObjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        obj = serializer.save(tenant=request.user)

        return Response(
            {"message": "Custom object created", "object": serializer.data},
            status=status.HTTP_201_CREATED,
        )
        

class CustomFieldCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def post(self, request, api_name):
        try:
            custom_object = CustomObject.objects.get(
                tenant=request.user,
                api_name=api_name,
                is_active=True,
            )
        except CustomObject.DoesNotExist:
            return Response({"error": "Object not found"}, status=404)

        serializer = CustomFieldSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(custom_object=custom_object)

        return Response(
            {"message": "Field added", "field": serializer.data},
            status=status.HTTP_201_CREATED,
        )
        

class CustomObjectDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request, api_name):
        try:
            obj = CustomObject.objects.get(
                tenant=request.user,
                api_name=api_name,
                is_active=True,
            )
        except CustomObject.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        fields = CustomFieldSerializer(obj.fields.all(), many=True).data

        return Response(
            {
                "object": obj.api_name,
                "fields": fields,
            }
        )
        

@login_required
def create_custom_object_view(request):
    if request.method == "POST":
        if not can_create_custom_object(request.user):
            messages.error(
                request,
                "You have reached your Custom Object limit for your plan."
            )
            return redirect("custom_object_list")

        name = request.POST.get("name")
        api_name = request.POST.get("api_name")

        CustomObject.objects.create(
            tenant=request.user,
            name=name,
            api_name=api_name,
        )

        messages.success(request, "Custom Object created successfully.")
        return redirect("custom_object_list")

    return render(request, "core/custom_object_create.html")

@login_required
def create_custom_field_view(request, object_id):
    custom_object = get_object_or_404(
        CustomObject,
        id=object_id,
        tenant=request.user,
    )

    if request.method == "POST":
        if not can_add_field_to_object(request.user, custom_object):
            messages.error(
                request,
                "You have reached the maximum number of fields allowed for this object."
            )
            return redirect("custom_object_detail", object_id=object_id)

        CustomField.objects.create(
            custom_object=custom_object,
            name=request.POST["name"],
            api_name=request.POST["api_name"],
            data_type=request.POST["data_type"],
            is_required="is_required" in request.POST,
            is_unique="is_unique" in request.POST,
        )

        messages.success(request, "Field added successfully.")
        return redirect("custom_object_detail", object_id=object_id)

    return render(
        request,
        "core/custom_field_create.html",
        {"custom_object": custom_object}
    )

@login_required
def create_custom_field_view(request, object_id):
    custom_object = get_object_or_404(
        CustomObject,
        id=object_id,
        tenant=request.user,
    )

    if request.method == "POST":
        if not can_add_field_to_object(request.user, custom_object):
            messages.error(
                request,
                "You have reached the maximum number of fields allowed for this object."
            )
            return redirect("custom_object_detail", object_id=object_id)

        CustomField.objects.create(
            custom_object=custom_object,
            name=request.POST["name"],
            api_name=request.POST["api_name"],
            data_type=request.POST["data_type"],
            is_required="is_required" in request.POST,
            is_unique="is_unique" in request.POST,
        )

        messages.success(request, "Field added successfully.")
        return redirect("custom_object_detail", object_id=object_id)

    return render(
        request,
        "core/custom_field_create.html",
        {"custom_object": custom_object}
    )

@login_required
def custom_object_list_view(request):
    objects = CustomObject.objects.filter(
        tenant=request.user,
        is_active=True,
    )

    limits = get_plan_limits(request.user)

    return render(
        request,
        "core/custom_object_list.html",
        {
            "objects": objects,
            "max_objects": limits["max_objects"],
            "current_count": objects.count(),
        }
    )
    

@login_required
def custom_object_detail_view(request, object_id):
    obj = get_object_or_404(
        CustomObject,
        id=object_id,
        tenant=request.user,
    )

    fields = obj.fields.all()
    records = CustomObjectRecord.objects.filter(
        tenant=request.user,
        object_api_name=obj.api_name,
    )

    limits = get_plan_limits(request.user)

    return render(
        request,
        "core/custom_object_detail.html",
        {
            "object": obj,
            "fields": fields,
            "records": records,
            "max_fields": limits["max_fields_per_object"],
        }
    )
    

@login_required
def create_custom_record_view(request, object_id):
    obj = get_object_or_404(
        CustomObject,
        id=object_id,
        tenant=request.user,
    )

    fields = obj.fields.all()

    if request.method == "POST":
        record = CustomObjectRecord.objects.create(
            tenant=request.user,
            object_api_name=obj.api_name,
        )

        for field in fields:
            raw_value = request.POST.get(field.api_name)

            if raw_value in ("", None):
                continue

            kwargs = {
                "record": record,
                "field_api_name": field.api_name,
            }

            if field.data_type == "STRING":
                kwargs["value_string"] = raw_value
            elif field.data_type == "NUMBER":
                kwargs["value_number"] = int(raw_value)
            elif field.data_type == "DECIMAL":
                kwargs["value_decimal"] = raw_value
            elif field.data_type == "BOOLEAN":
                kwargs["value_boolean"] = raw_value == "on"
            elif field.data_type == "DATE":
                kwargs["value_date"] = raw_value
            elif field.data_type == "DATETIME":
                kwargs["value_datetime"] = raw_value
            elif field.data_type == "JSON":
                kwargs["value_json"] = raw_value

            CustomFieldValue.objects.create(**kwargs)

        messages.success(request, "Record created successfully.")
        return redirect("custom_object_detail", object_id=obj.id)

    return render(
        request,
        "core/custom_record_create.html",
        {
            "object": obj,
            "fields": fields,
        }
    )
    
    
@login_required
def api_endpoint_list_view(request):
    return
