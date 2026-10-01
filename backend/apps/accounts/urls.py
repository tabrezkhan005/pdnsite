from django.urls import path

from .views import (
    CSRFView,
    LoginView,
    LogoutView,
    MeView,
    RequestOTPView,
    VerifyOTPView,
)

urlpatterns = [
    path("auth/request-otp/", RequestOTPView.as_view(), name="request-otp"),
    path("auth/verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/csrf/", CSRFView.as_view(), name="csrf"),
]
