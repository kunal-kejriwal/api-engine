from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    #Core Paths for Homepage, Login, Logout, Signup etc. 
    path('', views.core_home, name='core_home'),
    path('dashboard/', views.core_home, name='core_home'),
    # path('core/', views.core_home, name='core_home'),
    # path("login/", auth_views.LoginView.as_view(template_name="core/login-page.html"),name="login"),
    # path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # path("signup/", views.signup_view, name="signup"),
    # path("verify-email/", views.verify_email_view, name="verify_email"),
    # path("forgot-password/", views.forgot_password_view, name="forgot_password"),
#     path(
#     "reset-password/<uuid:token>/",
#     views.reset_password_view,
#     name="reset_password"
# ),
    
    # API and HTML-based API URLs
    #CustomerProfiles Views
    path('api/v1/customer-profiles/', views.CustomerProfileAPIView.as_view(), name="user_profile_view"),
    path('v1/customer-profiles/<uuid:user_id>', views.customer_profile_detail_page, name="customer_profile_detail"),
    path('v1/customer-profiles/', views.customer_profile_list_page, name="all_customer_profile_detail"),
    
    # ProductCatalog Views
    path('v1/product-catalog/', views.product_catalog_get_all_products, name="get_all_products"),
    path('v1/product-catalog/create/', views.create_product_view, name="create_product"),
    path('api/v1/product-catalog/', views.ProductCatalogAPIView.as_view(), name="product_catalog_api_view"),
    path(
    "api/v1/product-catalog/create/",
    views.ProductCatalogCreateAPIView.as_view(),
),
    
    path('api/v1/order-transaction/', views.OrderTransactionAPIView.as_view(), name="order_transaction_api_view"),
    path('v1/order-transaction/', views.order_transaction_list_view, name="order_transaction_list_view"),
    
    path("account/api-tokens/", views.api_tokens_view, name="api_tokens"),
    path("account/details", views.account_detail_view, name="account_detail"),
    
    path("api/v1/objects/", views.CustomObjectCreateAPIView.as_view()),
    path("api/v1/objects/<str:api_name>/", views.CustomObjectDetailAPIView.as_view()),
    path("api/v1/objects/<str:api_name>/fields/", views.CustomFieldCreateAPIView.as_view()),
    
    # Custom Objects
    path("v1/custom-objects/", views.custom_object_list_view, name="custom_object_list"),
    path("v1/custom-objects/create/", views.create_custom_object_view, name="custom_object_create"),
    path("v1/custom-objects/<uuid:object_id>/", views.custom_object_detail_view, name="custom_object_detail"),

    # Custom Fields
    path(
        "v1/custom-objects/<uuid:object_id>/fields/create/",
        views.create_custom_field_view,
        name="custom_field_create",
    ),

    # Custom Records
    path(
        "v1/custom-objects/<uuid:object_id>/records/create/",
        views.create_custom_record_view,
        name="custom_record_create",
    ),
    
    path("api/v1/api-endpoints/details/", views.api_endpoint_list_view, name="api_endpoint_list_view"),
]