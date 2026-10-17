from django.contrib import admin
from .models import Trip, TripStop, FareRule

class FareRuleInline(admin.TabularInline):
    model = FareRule
    extra = 1

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("id", "operator", "route", "bus", "departure_time", "status")
    list_filter = ("status", "operator", "departure_time")
    search_fields = ("route__name", "bus__registration_number")
    inlines = [FareRuleInline]

@admin.register(TripStop)
class TripStopAdmin(admin.ModelAdmin):
    list_display = ("trip", "route_stop", "expected_arrival")
    list_filter = ("trip__status",)