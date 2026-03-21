from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, EmailOTP

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "username", "is_email_verified", "is_staff", "is_active")
    list_filter = ("is_email_verified", "is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "password", "username")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
        ("Status", {"fields": ("is_email_verified",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2", "is_staff", "is_active", "is_email_verified"),
        }),
    )

    search_fields = ("email", "username")
    ordering = ("email",)

admin.site.register(User, CustomUserAdmin)
admin.site.register(EmailOTP)
