from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.apps import apps
from .models import CustomerProfile, ProductCatalog, OrderTransaction, SystemLog, FeatureUsageAnalytics, UserProfile, EmailVerificationToken, PasswordResetToken
from .serializers import CustomerProfileSerializer, ProductCatalogSerializer
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
from .permissions import IsSuperUser
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


# Create your views here.

def core_home(request):    
    return render(request, 'core/homepage.html')

def login_view(request):
    return render(request, "core/login-page.html")

def redirect_core(request):
    return redirect('/')

def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        if not username or not email or not password:
            messages.error(request, "All fields are required.")
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect("signup")

        # if User.objects.filter(username=username).exists():
        #     return render(
        #         request,
        #         "core/signup.html",
        #         {"error": "Username already exists"},
        #     )
        
        # if User.objects.filter(email=email).exists():
        #     return Response({"message": "Account Exists"}, status=201)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        # 🔑 EXPLICIT profile creation (NO signals)
        free_plan = Plan.objects.get(name="FREE")
        profile = get_object_or_404(
            UserProfile,
            user=user,
            plan=free_plan,
        )
        
        token = EmailVerificationToken.objects.create(user=user)
        send_verification_email(user, token.token)

        login(request, user)
        return redirect("home")

    return render(request, "core/signup.html")

def verify_email_view(request):
    token = request.GET.get("token")

    if not token:
        messages.error(request, "Invalid verification link.")
        return redirect("login")

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
        return redirect("login")

    user = record.user
    user.profile.is_email_verified = True
    user.is_active = True
    user.save()
    user.profile.save()

    record.is_used = True
    record.save()

    messages.success(request, "Email verified successfully")
    return redirect("login")

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

def reset_password_view(request):
    token = request.GET.get("token")

    record = get_object_or_404(
        PasswordResetToken,
        token=token,
        is_used=False
    )

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

class CustomerProfileList(generics.ListAPIView):
    queryset = CustomerProfile.objects.all()
    serializer_class = CustomerProfileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomerProfileFilter
    permission_classes = [IsAuthenticated]
    
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
    permission_classes = [IsAuthenticated]
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
@plan_required(can_create=True)
def create_product_view(request):
    if request.method == "POST":
        form = ProductCatalogForm(request.POST, user=request.user)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
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
        app_label, model_name = model_path.split(".")
        model = apps.get_model(app_label, model_name)

        total_records += model.objects.filter(
            created_by=user
        ).count()

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