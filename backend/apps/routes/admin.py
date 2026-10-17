from django.contrib import admin
from .models import City, Stop, Route, RouteStop

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "code", "is_active")
    search_fields = ("name", "code", "state")

@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "is_active")
    list_filter = ("is_active", "city")
    search_fields = ("name", "city__name")

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("name", "origin", "destination", "distance_km", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "origin__name", "destination__name")

@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ("route", "stop", "stop_order", "arrival_offset_minutes")
    list_filter = ("route",)