from rest_framework import serializers
from .models import Trip, Stop, DailyLog


class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stop
        fields = [
            "id", "stop_type", "location", "coords",
            "duration_hours", "order", "reason", "day_number", "elapsed_hours",
        ]


class DailyLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyLog
        fields = ["id", "day_number", "date_label", "log_data", "totals", "remarks"]


class TripSerializer(serializers.ModelSerializer):
    stops = StopSerializer(many=True, read_only=True)
    daily_logs = DailyLogSerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = [
            "id",
            "current_location", "pickup_location", "dropoff_location",
            "current_cycle_used",
            "distance_miles", "duration_hours", "eta_hours", "days_required",
            "route_geometry",
            "current_coords", "pickup_coords", "dropoff_coords",
            "created_at",
            "stops",
            "daily_logs",
        ]


class TripCreateSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=500)
    pickup_location = serializers.CharField(max_length=500)
    dropoff_location = serializers.CharField(max_length=500)
    current_cycle_used = serializers.FloatField(min_value=0, max_value=70)
