import logging
from django.http import HttpResponse, Http404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Trip, Stop, DailyLog
from .serializers import TripSerializer, TripCreateSerializer, DailyLogSerializer
from .services.route_service import geocode_address, get_route, get_location_name_from_coords, interpolate_point_at_mile
from .services.hos_engine import (
    build_trip_timeline,
    group_segments_by_day,
    compute_daily_totals,
    compute_daily_remarks,
    DAY_START_HOUR,
)
from .services.log_generator import generate_pdf_bytes

logger = logging.getLogger(__name__)


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


@api_view(["POST"])
def create_trip(request):
    serializer = TripCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    # 1. Geocode all three locations
    try:
        current_coords = geocode_address(data["current_location"])
        pickup_coords = geocode_address(data["pickup_location"])
        dropoff_coords = geocode_address(data["dropoff_location"])
    except ValueError as e:
        return Response({"error": f"Geocoding failed: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Geocoding error")
        return Response({"error": "Location lookup service unavailable. Please try again."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # 2. Get route
    try:
        route = get_route([current_coords, pickup_coords, dropoff_coords])
    except Exception as e:
        logger.exception("Route service error")
        return Response({"error": "Route calculation failed. Check that locations are driveable."}, status=status.HTTP_502_BAD_GATEWAY)

    distance_miles = route["distance_miles"]
    duration_hours = route["duration_hours"]
    geometry = route["geometry"]

    # 3. HOS engine
    def get_loc(coords, mile, total):
        return get_location_name_from_coords(coords, mile, total)

    def interp(geom, mile):
        return interpolate_point_at_mile(geom, mile)

    try:
        segments, stop_events, eta_hours = build_trip_timeline(
            total_miles=distance_miles,
            cycle_used=data["current_cycle_used"],
            geometry=geometry,
            pickup_location=data["pickup_location"],
            dropoff_location=data["dropoff_location"],
            current_location=data["current_location"],
            get_location_fn=get_loc,
            interpolate_fn=interp,
        )
    except Exception as e:
        logger.exception("HOS engine error")
        return Response({"error": "HOS calculation failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    days = group_segments_by_day(segments)
    days_required = len(days)

    # 4. Persist trip
    trip = Trip.objects.create(
        current_location=data["current_location"],
        pickup_location=data["pickup_location"],
        dropoff_location=data["dropoff_location"],
        current_cycle_used=data["current_cycle_used"],
        distance_miles=distance_miles,
        duration_hours=duration_hours,
        eta_hours=eta_hours,
        days_required=days_required,
        route_geometry=geometry,
        current_coords=current_coords,
        pickup_coords=pickup_coords,
        dropoff_coords=dropoff_coords,
    )

    # 5. Persist stops
    stop_objs = []
    for ev in stop_events:
        stop_objs.append(Stop(
            trip=trip,
            stop_type=ev.stop_type,
            location=ev.location,
            coords=ev.coords,
            duration_hours=ev.duration_hours,
            order=ev.order,
            reason=ev.reason,
            day_number=ev.day_number,
            elapsed_hours=ev.elapsed_hours,
        ))
    Stop.objects.bulk_create(stop_objs)

    # 6. Persist daily logs
    log_objs = []
    for day_num, day_segs in sorted(days.items()):
        totals = compute_daily_totals(day_segs)
        remarks = compute_daily_remarks(day_segs)
        log_data = [s.to_dict() for s in day_segs]
        log_objs.append(DailyLog(
            trip=trip,
            day_number=day_num,
            date_label=f"Day {day_num}",
            log_data=log_data,
            totals=totals,
            remarks=remarks,
        ))
    DailyLog.objects.bulk_create(log_objs)

    return Response(TripSerializer(trip).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def get_trip(request, trip_id):
    try:
        trip = Trip.objects.prefetch_related("stops", "daily_logs").get(pk=trip_id)
    except Trip.DoesNotExist:
        raise Http404
    return Response(TripSerializer(trip).data)


@api_view(["GET"])
def get_trip_logs(request, trip_id):
    try:
        trip = Trip.objects.get(pk=trip_id)
    except Trip.DoesNotExist:
        raise Http404
    logs = DailyLog.objects.filter(trip=trip).order_by("day_number")
    return Response(DailyLogSerializer(logs, many=True).data)


@api_view(["GET"])
def download_trip_pdf(request, trip_id):
    try:
        trip = Trip.objects.prefetch_related("daily_logs").get(pk=trip_id)
    except Trip.DoesNotExist:
        raise Http404

    logs = trip.daily_logs.all().order_by("day_number")
    if not logs.exists():
        return Response({"error": "No logs generated for this trip."}, status=status.HTTP_404_NOT_FOUND)

    from .services.hos_engine import Segment

    days: dict[int, list[Segment]] = {}
    for log in logs:
        segs = []
        for s in (log.log_data or []):
            segs.append(Segment(
                status=s["status"],
                start=s["start"],
                end=s["end"],
                location=s["location"],
                coords=s.get("coords"),
                note=s.get("note", ""),
            ))
        days[log.day_number] = segs

    try:
        pdf_bytes = generate_pdf_bytes(
            days=days,
            trip_id=trip.id,
            total_miles=trip.distance_miles or 0,
        )
    except Exception as e:
        logger.exception("PDF generation error")
        return Response({"error": "PDF generation failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="trip_{trip_id}_logs.pdf"'
    return response
