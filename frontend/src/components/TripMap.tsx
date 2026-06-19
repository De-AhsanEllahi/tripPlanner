import { useEffect } from "react";
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Trip, Stop } from "../types";

// Fix default leaflet icon paths broken by Vite bundling
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const ICON_COLOR: Record<string, string> = {
  fuel: "#ef4444",
  break: "#f97316",
  rest: "#6366f1",
  restart: "#dc2626",
  pickup: "#22c55e",
  dropoff: "#3b82f6",
  current: "#64748b",
};

function makeIcon(color: string, label: string) {
  return L.divIcon({
    className: "",
    html: `
      <div style="
        background:${color};
        border:2px solid white;
        border-radius:50%;
        width:22px;height:22px;
        display:flex;align-items:center;justify-content:center;
        box-shadow:0 2px 6px rgba(0,0,0,0.4);
        font-size:9px;color:white;font-weight:bold;
      ">${label}</div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  });
}

const STOP_LABEL: Record<string, string> = {
  fuel: "F",
  break: "B",
  rest: "R",
  restart: "34",
  pickup: "P",
  dropoff: "D",
  current: "★",
};

function FitBounds({ coords }: { coords: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (coords.length > 1) {
      map.fitBounds(L.latLngBounds(coords), { padding: [40, 40] });
    }
  }, [map, coords]);
  return null;
}

interface Props {
  trip: Trip;
}

export default function TripMap({ trip }: Props) {
  // ORS returns [lon, lat]; Leaflet needs [lat, lon]
  const routeLatLng: [number, number][] = (trip.route_geometry ?? []).map(
    ([lon, lat]) => [lat, lon]
  );

  const allCoords: [number, number][] = [
    ...(trip.current_coords ? [[trip.current_coords[1], trip.current_coords[0]] as [number, number]] : []),
    ...(trip.pickup_coords ? [[trip.pickup_coords[1], trip.pickup_coords[0]] as [number, number]] : []),
    ...(trip.dropoff_coords ? [[trip.dropoff_coords[1], trip.dropoff_coords[0]] as [number, number]] : []),
  ];

  function stopLatLng(stop: Stop): [number, number] | null {
    if (!stop.coords) return null;
    return [stop.coords[1], stop.coords[0]];
  }

  const center: [number, number] = allCoords[0] ?? [37.0902, -95.7129];

  return (
    <MapContainer
      center={center}
      zoom={5}
      style={{ height: 480, width: "100%", borderRadius: 8 }}
      aria-label="Trip route map"
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />

      {routeLatLng.length > 1 && (
        <Polyline positions={routeLatLng} color="#1d4ed8" weight={4} opacity={0.8} />
      )}

      {/* Current location */}
      {trip.current_coords && (
        <Marker
          position={[trip.current_coords[1], trip.current_coords[0]]}
          icon={makeIcon(ICON_COLOR.current, STOP_LABEL.current)}
        >
          <Popup>
            <strong>Current Location</strong>
            <br />
            {trip.current_location}
          </Popup>
        </Marker>
      )}

      {/* Pickup */}
      {trip.pickup_coords && (
        <Marker
          position={[trip.pickup_coords[1], trip.pickup_coords[0]]}
          icon={makeIcon(ICON_COLOR.pickup, STOP_LABEL.pickup)}
        >
          <Popup>
            <strong>Pickup</strong>
            <br />
            {trip.pickup_location}
          </Popup>
        </Marker>
      )}

      {/* Dropoff */}
      {trip.dropoff_coords && (
        <Marker
          position={[trip.dropoff_coords[1], trip.dropoff_coords[0]]}
          icon={makeIcon(ICON_COLOR.dropoff, STOP_LABEL.dropoff)}
        >
          <Popup>
            <strong>Dropoff</strong>
            <br />
            {trip.dropoff_location}
          </Popup>
        </Marker>
      )}

      {/* Intermediate stops */}
      {trip.stops.map((stop) => {
        const pos = stopLatLng(stop);
        if (!pos) return null;
        return (
          <Marker
            key={stop.id}
            position={pos}
            icon={makeIcon(
              ICON_COLOR[stop.stop_type] ?? "#64748b",
              STOP_LABEL[stop.stop_type] ?? "?"
            )}
          >
            <Popup>
              <strong>
                {stop.stop_type === "fuel" && "Fuel Stop"}
                {stop.stop_type === "break" && "Break Stop"}
                {stop.stop_type === "rest" && "Overnight Rest"}
                {stop.stop_type === "restart" && "34-Hour Restart"}
                {stop.stop_type === "pickup" && "Pickup"}
                {stop.stop_type === "dropoff" && "Dropoff"}
              </strong>
              <br />
              <em>{stop.location}</em>
              <br />
              <span style={{ fontSize: 11, color: "#555" }}>{stop.reason}</span>
              <br />
              <span style={{ fontSize: 11 }}>
                Duration: {(stop.duration_hours * 60).toFixed(0)} min | Day {stop.day_number}
              </span>
            </Popup>
          </Marker>
        );
      })}

      <FitBounds coords={[...routeLatLng, ...allCoords]} />
    </MapContainer>
  );
}
