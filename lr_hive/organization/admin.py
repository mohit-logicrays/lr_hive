from django.contrib import admin
from organization.models import Organization, OrganizationDetail, OrganizationUser

admin.site.register(Organization)
admin.site.register(OrganizationDetail)
admin.site.register(OrganizationUser)
