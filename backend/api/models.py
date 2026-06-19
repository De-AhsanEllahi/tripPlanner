from django.db import models


class Trip(models.Model):
    current_location = models.CharField(max_length=500)
    pickup_location = models.CharField(max_length=500)
    dropoff_location = models.CharField(max_length=500)
    current_cycle_used = models.FloatField(default=0)

    # Computed route data
    distance_miles = models.FloatField(null=True, blank=True)
    duration_hours = models.FloatField(null=True, blank=True)
    eta_hours = models.FloatField(null=True, blank=True)
    days_required = models.IntegerField(null=True, blank=True)

    # Geometry stored as JSON list of [lon, lat] pairs
    route_geometry = models.JSONField(null=True, blank=True)

    # Coordinates
    current_coords = models.JSONField(null=True, blank=True)  # [lon, lat]
    pickup_coords = models.JSONField(null=True, blank=True)
    dropoff_coords = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Trip {self.id}: {self.current_location} → {self.dropoff_location}"


class Stop(models.Model):
    STOP_TYPES = [
        ("fuel", "Fuel Stop"),
        ("break", "Break"),
        ("rest", "Overnight Rest"),
        ("restart", "34-Hour Restart"),
        ("pickup", "Pickup"),
        ("dropoff", "Dropoff"),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="stops")
    stop_type = models.CharField(max_length=20, choices=STOP_TYPES)
    location = models.CharField(max_length=500)
    coords = models.JSONField(null=True, blank=True)  # [lon, lat]
    duration_hours = models.FloatField(default=0)
    order = models.IntegerField(default=0)
    reason = models.TextField(blank=True)
    day_number = models.IntegerField(default=1)
    elapsed_hours = models.FloatField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.stop_type} at {self.location}"


class DailyLog(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="daily_logs")
    day_number = models.IntegerField()
    date_label = models.CharField(max_length=50, blank=True)
    log_data = models.JSONField(null=True, blank=True)  # Timeline segments
    totals = models.JSONField(null=True, blank=True)    # Hours per status
    remarks = models.JSONField(null=True, blank=True)   # List of remark strings
    image_path = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["day_number"]

    def __str__(self):
        return f"Trip {self.trip_id} Day {self.day_number}"
