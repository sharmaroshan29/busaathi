from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PassengerProfile


# @admin.register(User) is a clean Python decorator equivalent to calling
# admin.site.register(User, UserAdmin) at the bottom of the file.
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom Admin configuration for BuSaathi's User model.
    
    Inherits from Django's built-in UserAdmin so that password hashing,
    staff/superuser toggles, and group permissions work securely out of the box.
    """
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "phone_number")
    ordering = ("username",)
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "BuSaathi Verification & Contact",
            {"fields": ("phone_number", "is_email_verified")},
        ),
    )

@admin.register(PassengerProfile)
class PassengerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "emergency_contact_phone", "created_at")
    search_fields = ("user__username", "user__email", "full_name")



