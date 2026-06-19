export interface Stop {
  id: number;
  stop_type: "fuel" | "break" | "rest" | "restart" | "pickup" | "dropoff";
  location: string;
  coords: [number, number] | null; // [lon, lat]
  duration_hours: number;
  order: number;
  reason: string;
  day_number: number;
  elapsed_hours: number;
}

export interface DailyLog {
  id: number;
  day_number: number;
  date_label: string;
  log_data: Segment[];
  totals: Record<string, number>;
  remarks: string[];
}

export interface Segment {
  status: "OFF_DUTY" | "SLEEPER_BERTH" | "DRIVING" | "ON_DUTY_NOT_DRIVING";
  start: number;
  end: number;
  duration: number;
  location: string;
  coords: [number, number] | null;
  note: string;
}

export interface Trip {
  id: number;
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  current_cycle_used: number;
  distance_miles: number;
  duration_hours: number;
  eta_hours: number;
  days_required: number;
  route_geometry: [number, number][]; // [lon, lat]
  current_coords: [number, number];
  pickup_coords: [number, number];
  dropoff_coords: [number, number];
  created_at: string;
  stops: Stop[];
  daily_logs: DailyLog[];
}

export interface TripFormValues {
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  current_cycle_used: number;
}
