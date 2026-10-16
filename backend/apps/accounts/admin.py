from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


# @admin.register(User) is a clean Python decorator equivalent to calling
# admin.site.register(User, UserAdmin) at the bottom of the file.
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom Admin configuration for BuSaathi's User model.
    
    Inherits from Django's built-in UserAdmin so that password hashing,
    staff/superuser toggles, and group permissions work securely out of the box.
    """

    # Columns displayed in the main table list view inside Django Admin
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")

    # Adds a sidebar filter on the right side of the admin page
    list_filter = ("is_staff", "is_superuser", "is_active")

    # Enables the search bar at the top of the User list page
    search_fields = ("username", "email", "first_name", "last_name")

    # Default sorting order in the admin table
    ordering = ("username",)