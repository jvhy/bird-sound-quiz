from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    ordering = ["id"]
    list_display = ["username", "is_contributor", "is_staff"]
    fieldsets = (
        (None, {"fields": ("username", "password", "security_answer")}),
        ("Permissions", {"fields": ("is_active", "is_contributor", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2"),
        }),
    )

admin.site.register(User, UserAdmin)
