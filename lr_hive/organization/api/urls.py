from django.urls import path
from organization.api.api import (
    InviteUserAPIView,
    OrganizationCreateAPIView,
    OrganizationListAPIView,
    OrganizationSwitchAPIView,
)

app_name = "organization"

urlpatterns = [
    path("create/", OrganizationCreateAPIView.as_view(), name="create_org"),
    path("list/", OrganizationListAPIView.as_view(), name="list_orgs"),
    path("switch/", OrganizationSwitchAPIView.as_view(), name="switch_org"),
    path("invite/", InviteUserAPIView.as_view(), name="invite_user"),
]
