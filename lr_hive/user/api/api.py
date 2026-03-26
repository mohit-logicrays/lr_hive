from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from user.api.serializers import UserSerailizer
from user.models import User


class UserViewSet(ModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerailizer
    filterset_fields = ["is_active"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["email"]
    lookup_field = "id"
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Override get_permissions to return the permission class based on action.
        The permissions are as follows:
        - list and create: AllowAny()
        - others: IsAuthenticated()
        """

        if self.action in ["create"]:
            return [AllowAny()]
        return super().get_permissions()

    def get_object(self):
        """
        Override get_object to return the current user object.
        """
        return self.queryset.get(id=self.request.user.id)


class LoginAPiView(TokenObtainPairView):
    """
    Custom login view that uses the TokenObtainPairView from Simple JWT.
    It allows users to obtain a token pair (access and refresh tokens).
    """

    _serializer_class = "user.api.serializers.JWTTokenSerializer"


login_api_view = LoginAPiView.as_view()


class RefreshTokenView(TokenRefreshView):
    """
    Custom token refresh view that uses the TokenRefreshView from Simple JWT.
    It allows users to refresh their access token using a valid refresh token.
    """

    _serializer_class = "user.api.serializers.JWTTokenRefreshSerializer"


token_refresh_view = RefreshTokenView.as_view()
