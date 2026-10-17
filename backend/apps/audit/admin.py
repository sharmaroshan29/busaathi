from django.contrib import admin
from .models import AuditLog


# Register your models here.
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("actor", "action", "ip_address", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("actor__username", "action", "ip_address")
    # Audit logs should be read-only in production admin!
    readonly_fields = ("actor", "action", "ip_address", "details", "created_at")
