from django.contrib import admin
from .models import Operator, OperatorInvitation, OperatorMembership, OperatorDocument, OperatorPaymentProfile
# Register your models here.

@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "contact_email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "contact_email", "slug")
    # Automatically fills the slug field as you type the operator name!
    prepopulated_fields = {"slug": ("name",)}


@admin.register(OperatorMembership)
class OperatorMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "operator", "role", "status")
    list_filter = ("role", "status")
    search_fields = ("user__username", "user__email", "operator__name")


@admin.register(OperatorInvitation)
class OperatorInvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "operator", "role", "status", "expires_at", "created_at")
    list_filter = ("status", "role")
    search_fields = ("email", "operator__name")

@admin.register(OperatorDocument)
class OperatorDocumentAdmin(admin.ModelAdmin):
    list_display = ("operator", "doc_type", "status", "created_at")
    list_filter = ("status", "doc_type")
    search_fields = ("operator__name", "doc_type")


@admin.register(OperatorPaymentProfile)
class OperatorPaymentProfileAdmin(admin.ModelAdmin):
    list_display = ("operator", "payout_status", "bank_details_verified", "created_at")
    list_filter = ("payout_status", "bank_details_verified")
    search_fields = ("operator__name", "gateway_account_id")