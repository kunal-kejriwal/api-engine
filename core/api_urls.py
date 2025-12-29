from django.urls import path
from . import views
from django.contrib.auth import views as auth_views    
    
urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="core/login-page.html"),name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", views.signup_view, name="signup"),
    path("confirm-email/", views.verify_email_page, name="confirm_email"),
    path("verify-email/", views.verify_email_view, name="verify_email"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path(
    "reset-password/<uuid:token>/",
    views.reset_password_view,
    name="reset_password"
),
    path(
    "resend-verification/",
    views.resend_verification_email,
    name="resend_verification_email",
),
]