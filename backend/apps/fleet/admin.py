from django.contrib import admin
from .models import Bus, SeatLayout, Seat

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ("registration_number", "operator", "bus_type", "is_active")
    list_filter = ("bus_type", "is_active", "operator")
    search_fields = ("registration_number", "make_and_model")

@admin.register(SeatLayout)
class SeatLayoutAdmin(admin.ModelAdmin):
    list_display = ("bus", "version", "total_capacity", "is_active", "effective_from")
    list_filter = ("is_active",)
    search_fields = ("bus__registration_number",)

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("id", "seat_number", "layout", "seat_type", "deck", "is_window", "is_women_only")
    list_filter = ("seat_type", "deck", "is_window", "is_women_only")
    search_fields = ("seat_number", "layout__bus__registration_number")