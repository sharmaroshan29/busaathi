from django.contrib import admin

# Register your models here.
from .models import Booking, BookingSeat, SeatHold

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