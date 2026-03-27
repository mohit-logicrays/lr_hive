from django.contrib import admin
from user.models import EmailTemplate, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    pass
