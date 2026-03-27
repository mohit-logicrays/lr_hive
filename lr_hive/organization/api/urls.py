from django.urls import path
from organization.api.api import InviteUserAPIView, OrganizationCreateAPIView

app_name = "organization"

urlpatterns = [
    path("create/", OrganizationCreateAPIView.as_view(), name="create_org"),
    path("invite/", InviteUserAPIView.as_view(), name="invite_user"),
]
