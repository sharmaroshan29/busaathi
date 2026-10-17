from django.contrib import admin

# Register your models here.
from .models import Booking, BookingSeat, SeatHold, PaymentTransaction, Ticket

class BookingSeatInline(admin.TabularInline):
    model = BookingSeat
    extra = 0


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("pnr", "user", "trip", "total_fare", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("pnr", "user__email", "user__username")
    readonly_fields = ("pnr", "created_at", "updated_at")
    inlines = [BookingSeatInline]

@admin.register(SeatHold)
class SeatHoldAdmin(admin.ModelAdmin):
    list_display = ("seat", "trip", "user", "expires_at", "is_active")
    list_filter = ("trip", "expires_at")

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("provider_order_id", "booking", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("provider_order_id", "idempotency_key", "booking__pnr")
    readonly_fields = ("idempotency_key", "provider_order_id", "created_at", "updated_at")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("ticket_number", "booking", "issued_at", "is_delivered")
    list_filter = ("is_delivered", "issued_at")
    search_fields = ("ticket_number", "booking__pnr")
    readonly_fields = ("ticket_number", "issued_at")