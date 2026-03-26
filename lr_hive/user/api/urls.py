from django.urls import path
from rest_framework.routers import DefaultRouter
from user.api.api import UserViewSet, login_api_view, token_refresh_view

app_name = "user"

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    path(r"login/", login_api_view, name="login"),
    path(r"token/refresh/", token_refresh_view, name="token_refresh"),
] + router.urls
