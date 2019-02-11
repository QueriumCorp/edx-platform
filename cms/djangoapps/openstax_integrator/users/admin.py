from __future__ import absolute_import
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class UserAdmin(UserAdmin):
    pass
UserAdmin = admin.register(User)(UserAdmin)
