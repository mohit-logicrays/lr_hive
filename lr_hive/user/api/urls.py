from django.urls import path
from rest_framework.routers import DefaultRouter
from user.api.api import (
    ProfileUpdateAPIView,
    ResendOTPAPIView,
    UserViewSet,
    VerifyOTPAPIView,
    login_api_view,
    token_refresh_view,
)

app_name = "user"

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    path(r"register/", UserViewSet.as_view({"post": "create"}), name="register"),
    path(r"login/", login_api_view, name="login"),
    path(r"token/refresh/", token_refresh_view, name="token_refresh"),
    path(r"verify-otp/", VerifyOTPAPIView.as_view(), name="verify_otp"),
    path(r"resend-otp/", ResendOTPAPIView.as_view(), name="resend_otp"),
    path(r"profile/", ProfileUpdateAPIView.as_view(), name="profile"),
] + router.urls
