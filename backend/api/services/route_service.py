"""
Route service: geocoding + directions via OpenRouteService.
Falls back to Nominatim geocoding if ORS geocoding fails.
"""
import math
import os
import time
import requests

ORS_BASE = "https://api.openrouteservice.org"
NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
HEADERS = {"User-Agent": "ELD-TripPlanner/1.0 assessment@example.com"}


def _ors_key() -> str:
    key = os.getenv("ORS_API_KEY", "")
    if not key:
        raise ValueError("ORS_API_KEY is not set in environment.")
    return key


def geocode_address(address: str) -> list[float]:
    """Return [lon, lat] for the given address string."""
    # Try ORS geocoding first
    try:
        return _geocode_ors(address)
    except Exception:
        pass
    # Fallback: Nominatim
    return _geocode_nominatim(address)


def _geocode_ors(address: str) -> list[float]:
    url = f"{ORS_BASE}/geocode/search"
    params = {
        "api_key": _ors_key(),
        "text": address,
        "size": 1,
    }
    resp = requests.get(url, params=params, timeout=10, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    features = data.get("features", [])
    if not features:
        raise ValueError(f"No geocoding result for: {address}")
    coords = features[0]["geometry"]["coordinates"]  # [lon, lat]
    return coords


def _geocode_nominatim(address: str) -> list[float]:
    time.sleep(1)  # Nominatim rate limit
    url = f"{NOMINATIM_BASE}/search"
    params = {"q": address, "format": "json", "limit": 1}
    resp = requests.get(url, params=params, timeout=10, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError(f"Nominatim could not geocode: {address}")
    return [float(data[0]["lon"]), float(data[0]["lat"])]


def get_route(coords: list[list[float]]) -> dict:
    """
    Get driving route through a list of [lon, lat] waypoints.
    Returns dict with keys: distance_miles, duration_hours, geometry (list of [lon,lat]).
    """
    # /geojson suffix returns GeoJSON FeatureCollection (features[0].properties.summary)
    url = f"{ORS_BASE}/v2/directions/driving-car/geojson"
    headers = {
        "Authorization": _ors_key(),
        "Content-Type": "application/json",
        **HEADERS,
    }
    body = {
        "coordinates": coords,
        "units": "mi",
    }
    resp = requests.post(url, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "features" not in data or not data["features"]:
        raise ValueError(f"ORS returned unexpected response: {list(data.keys())}")

    feature = data["features"][0]
    props = feature["properties"]
    summary = props["summary"]

    distance_miles = summary["distance"]  # already in miles (units=mi)
    duration_hours = summary["duration"] / 3600.0

    geometry = feature["geometry"]["coordinates"]  # list of [lon, lat]

    return {
        "distance_miles": round(distance_miles, 2),
        "duration_hours": round(duration_hours, 2),
        "geometry": geometry,
    }


def get_location_name_from_coords(coords: list[float], segment_miles: float, total_miles: float) -> str:
    """
    Reverse geocode [lon, lat] to get a city/state string.
    Uses Nominatim. Returns a best-effort string.
    """
    try:
        time.sleep(0.5)
        url = f"{NOMINATIM_BASE}/reverse"
        params = {
            "lat": coords[1],
            "lon": coords[0],
            "format": "json",
            "zoom": 10,
        }
        resp = requests.get(url, params=params, timeout=8, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        addr = data.get("address", {})
        city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county", "")
        state = addr.get("state", "")
        if city and state:
            return f"{city}, {state}"
        return data.get("display_name", "En Route")[:60]
    except Exception:
        pct = int((segment_miles / total_miles) * 100) if total_miles else 0
        return f"Mile {int(segment_miles)} ({pct}% of route)"


def interpolate_point_at_mile(geometry: list[list[float]], target_mile: float) -> list[float]:
    """
    Walk the route geometry and return the [lon, lat] at approximately target_mile.
    """
    def haversine(a, b):
        R = 3958.8
        lat1, lon1 = math.radians(a[1]), math.radians(a[0])
        lat2, lon2 = math.radians(b[1]), math.radians(b[0])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 2 * R * math.asin(math.sqrt(h))

    accumulated = 0.0
    for i in range(len(geometry) - 1):
        seg = haversine(geometry[i], geometry[i + 1])
        if accumulated + seg >= target_mile:
            frac = (target_mile - accumulated) / seg if seg > 0 else 0
            lon = geometry[i][0] + frac * (geometry[i + 1][0] - geometry[i][0])
            lat = geometry[i][1] + frac * (geometry[i + 1][1] - geometry[i][1])
            return [lon, lat]
        accumulated += seg
    return geometry[-1]
