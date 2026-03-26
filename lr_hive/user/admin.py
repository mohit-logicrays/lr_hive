from django.contrib.admin import site
from django.contrib.auth.admin import UserAdmin
from user.models import User


class UserAdmin(UserAdmin):
    pass


site.register(User)
