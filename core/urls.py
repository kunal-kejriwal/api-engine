from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    #Core Paths for Homepage, Login, Logout, Signup etc. 
    path('', views.core_home, name='home'),
    path('core/', views.core_home, name='core_home'),
    path("login/", auth_views.LoginView.as_view(template_name="core/login-page.html"),name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", views.signup_view, name="signup"),
    path("verify-email/", views.verify_email_view, name="verify_email"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("reset-password/", views.reset_password_view, name="reset_password"),
    
    # API and HTML-based API URLs
    #CustomerProfiles Views
    path('api/v1/customer-profiles/', views.CustomerProfileList.as_view(), name="user_profile_view"),
    path('v1/customer-profiles/<uuid:user_id>', views.customer_profile_detail_page, name="customer_profile_detail"),
    path('v1/customer-profiles/', views.customer_profile_list_page, name="all_customer_profile_detail"),
    
    # ProductCatalog Views
    path('v1/product-catalog/', views.product_catalog_get_all_products, name="get_all_products"),
    path('v1/product-catalog/create/', views.create_product_view, name="create_product"),
    path('api/v1/product-catalog/', views.ProductCatalogAPIView.as_view(), name="product_catalog_api_view"),
    
    path("account/api-tokens/", views.api_tokens_view, name="api_tokens"),
    path("account/details", views.account_detail_view, name="account_detail"),
]