from django.contrib import admin
from .models import Trip, Stop, DailyLog


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ["id", "current_location", "pickup_location", "dropoff_location", "distance_miles", "days_required", "created_at"]
    readonly_fields = ["created_at", "route_geometry", "current_coords", "pickup_coords", "dropoff_coords"]


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ["id", "trip", "stop_type", "location", "duration_hours", "order"]
    list_filter = ["stop_type"]


@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ["id", "trip", "day_number", "date_label"]
