"""
HOS Engine — Property Carrying Driver, 70-hour/8-day cycle.

Rules implemented:
  - 11-hour driving limit per shift
  - 14-hour duty window (no driving after 14th on-duty hour)
  - 30-minute break after 8 cumulative driving hours
  - 10-hour off-duty (sleeper) required before new shift
  - 70-hour/8-day cycle; 34-hour restart when exhausted
  - Fuel stop every 1,000 miles (30 min, ON_DUTY_NOT_DRIVING)
  - Pickup  = 1 hr ON_DUTY_NOT_DRIVING
  - Dropoff = 1 hr ON_DUTY_NOT_DRIVING
  - Day starts at 06:00 (hour 6 of a 24-hour clock)
  - Midnight splitting: no segment crosses 00:00
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

MPH = 55
DAY_START_HOUR = 6          # 06:00 local
FUEL_INTERVAL_MILES = 1000
MAX_DRIVING_HOURS = 11
MAX_DUTY_WINDOW = 14
BREAK_AFTER_HOURS = 8
BREAK_DURATION = 0.5        # hours
FUEL_DURATION = 0.5
PICKUP_DURATION = 1.0
DROPOFF_DURATION = 1.0
OVERNIGHT_REST = 10.0
RESTART_HOURS = 34.0
MAX_CYCLE = 70.0

Status = Literal["OFF_DUTY", "SLEEPER_BERTH", "DRIVING", "ON_DUTY_NOT_DRIVING"]


@dataclass
class Segment:
    status: Status
    start: float        # hours from trip epoch (absolute)
    end: float
    location: str
    coords: list | None = None
    note: str = ""      # remark text

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 6)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "start": round(self.start, 4),
            "end": round(self.end, 4),
            "duration": round(self.duration, 4),
            "location": self.location,
            "coords": self.coords,
            "note": self.note,
        }


@dataclass
class StopEvent:
    stop_type: str
    location: str
    coords: list | None
    elapsed_hours: float    # absolute trip hours when stop occurs
    duration_hours: float
    reason: str
    day_number: int = 1
    order: int = 0


@dataclass
class HosState:
    clock: float = 0.0              # absolute elapsed hours from trip start
    driving_today: float = 0.0      # driving hours in current shift
    duty_window_start: float = 0.0  # when current 14-hr window opened
    cycle_used: float = 0.0         # rolling 70-hr counter
    miles_since_fuel: float = 0.0
    cumulative_driving_for_break: float = 0.0  # driving since last 30-min break
    shift_active: bool = False      # True once driver has started a shift
    day_number: int = 1


def _clock_to_day_hour(clock: float) -> tuple[int, float]:
    """Return (day_number 1-based, hour_within_day 0-24) given trip epoch + DAY_START_HOUR offset."""
    absolute_hour = DAY_START_HOUR + clock
    day = int(absolute_hour // 24) + 1
    hour = absolute_hour % 24
    return day, hour


def _split_across_midnight(segments: list[Segment]) -> list[Segment]:
    """
    Ensure no segment crosses a midnight boundary.
    Splits any segment that would cross 00:00 into two pieces.
    """
    out: list[Segment] = []
    for seg in segments:
        remaining = seg
        while True:
            til_mid = _hours_until_midnight_abs(remaining.start)
            if til_mid < 1e-9:
                til_mid = 24.0
            if remaining.duration <= til_mid + 1e-9:
                out.append(remaining)
                break
            # Split here
            mid_end = remaining.start + til_mid
            out.append(Segment(
                status=remaining.status,
                start=remaining.start,
                end=mid_end,
                location=remaining.location,
                coords=remaining.coords,
                note=remaining.note,
            ))
            remaining = Segment(
                status=remaining.status,
                start=mid_end,
                end=remaining.end,
                location=remaining.location,
                coords=remaining.coords,
                note=remaining.note,
            )
    return out


def _hours_until_midnight_abs(clock: float) -> float:
    absolute = DAY_START_HOUR + clock
    return 24.0 - (absolute % 24)


def build_trip_timeline(
    total_miles: float,
    cycle_used: float,
    geometry: list,           # [lon,lat] list from route service
    pickup_location: str,
    dropoff_location: str,
    current_location: str,
    get_location_fn,          # callable(coords, mile, total) -> str
    interpolate_fn,           # callable(geometry, mile) -> [lon,lat]
) -> tuple[list[Segment], list[StopEvent], float]:
    """
    Build the complete trip timeline and stop events list.
    Returns (all_segments, stop_events, eta_hours).
    """
    segments: list[Segment] = []
    stops: list[StopEvent] = []
    state = HosState(cycle_used=cycle_used)
    stop_order = 0

    def add_seg(status: Status, duration: float, location: str, coords=None, note: str = ""):
        start = state.clock
        end = start + duration
        segments.append(Segment(status, start, end, location, coords, note))
        state.clock = end

    def add_stop(stop_type: str, location: str, coords, duration: float, reason: str):
        nonlocal stop_order
        day, _ = _clock_to_day_hour(state.clock)
        stops.append(StopEvent(
            stop_type=stop_type,
            location=location,
            coords=coords,
            elapsed_hours=state.clock,
            duration_hours=duration,
            reason=reason,
            day_number=day,
            order=stop_order,
        ))
        stop_order += 1

    def maybe_fuel(location: str, coords):
        if state.miles_since_fuel >= FUEL_INTERVAL_MILES:
            reason = f"Fuel stop required every {FUEL_INTERVAL_MILES} miles"
            add_stop("fuel", location, coords, FUEL_DURATION, reason)
            add_seg("ON_DUTY_NOT_DRIVING", FUEL_DURATION, location, coords, f"Fuel stop — {reason}")
            state.miles_since_fuel = 0.0
            state.cycle_used += FUEL_DURATION
            state.duty_window_start = state.duty_window_start  # no change; on-duty counts

    def do_overnight(location: str, coords):
        """Insert 10-hour sleeper berth rest and reset shift counters."""
        add_seg("SLEEPER_BERTH", OVERNIGHT_REST, location, coords, "10-hour mandatory rest")
        state.driving_today = 0.0
        state.cumulative_driving_for_break = 0.0
        state.shift_active = False

    def do_restart(location: str, coords):
        """Insert 34-hour restart when cycle exhausted."""
        reason = "70-hour/8-day cycle exhausted — 34-hour restart required"
        add_stop("restart", location, coords, RESTART_HOURS / 24.0, reason)
        add_seg("OFF_DUTY", RESTART_HOURS, location, coords, reason)
        state.cycle_used = 0.0
        state.driving_today = 0.0
        state.cumulative_driving_for_break = 0.0
        state.shift_active = False

    def start_shift():
        """Begin duty window."""
        state.duty_window_start = state.clock
        state.shift_active = True
        state.driving_today = 0.0
        state.cumulative_driving_for_break = 0.0

    # Pickup 
    pickup_coords = interpolate_fn(geometry, 0) if geometry else None
    # Check cycle before starting
    if state.cycle_used >= MAX_CYCLE:
        do_restart(current_location, pickup_coords)

    start_shift()
    add_stop("pickup", pickup_location, pickup_coords, PICKUP_DURATION,
             "Pickup — loading cargo (1 hour on-duty)")
    add_seg("ON_DUTY_NOT_DRIVING", PICKUP_DURATION, pickup_location, pickup_coords,
            f"Pickup at {pickup_location}")
    state.cycle_used += PICKUP_DURATION

    # Drive segment by segment
    miles_driven = 0.0
    total_segments = max(int(total_miles / 50), 1)
    miles_per_chunk = total_miles / total_segments

    for _ in range(total_segments):
        chunk_miles = min(miles_per_chunk, total_miles - miles_driven)
        if chunk_miles <= 0:
            break

        chunk_hours = chunk_miles / MPH
        mile_mid = miles_driven + chunk_miles / 2
        coords = interpolate_fn(geometry, mile_mid)
        location = get_location_fn(coords, mile_mid, total_miles)

        # Cycle check
        remaining_cycle = MAX_CYCLE - state.cycle_used
        if remaining_cycle <= 0:
            do_restart(location, coords)
            start_shift()
            remaining_cycle = MAX_CYCLE

        # Overnight rest check 
        duty_elapsed = state.clock - state.duty_window_start
        if state.shift_active and duty_elapsed >= MAX_DUTY_WINDOW:
            do_overnight(location, coords)
            start_shift()
            duty_elapsed = 0.0

        if state.shift_active and state.driving_today >= MAX_DRIVING_HOURS:
            do_overnight(location, coords)
            start_shift()
            duty_elapsed = 0.0

        # 30-min break check 
        if state.cumulative_driving_for_break + chunk_hours > BREAK_AFTER_HOURS:
            hours_to_break = BREAK_AFTER_HOURS - state.cumulative_driving_for_break
            if hours_to_break > 0:
                drive_miles_before = hours_to_break * MPH
                coords_b = interpolate_fn(geometry, miles_driven + drive_miles_before)
                loc_b = get_location_fn(coords_b, miles_driven + drive_miles_before, total_miles)
                add_seg("DRIVING", hours_to_break, loc_b, coords_b, f"Driving to {loc_b}")
                state.driving_today += hours_to_break
                state.cycle_used += hours_to_break
                state.cumulative_driving_for_break += hours_to_break
                miles_driven += drive_miles_before
                state.miles_since_fuel += drive_miles_before
                chunk_miles -= drive_miles_before
                chunk_hours -= hours_to_break

            # Insert break
            break_coords = interpolate_fn(geometry, miles_driven)
            break_loc = get_location_fn(break_coords, miles_driven, total_miles)
            reason = f"30-minute break required after {BREAK_AFTER_HOURS} cumulative driving hours"
            add_stop("break", break_loc, break_coords, BREAK_DURATION, reason)
            add_seg("OFF_DUTY", BREAK_DURATION, break_loc, break_coords, reason)
            state.cycle_used += BREAK_DURATION
            state.cumulative_driving_for_break = 0.0

            # Recalc remaining chunk
            coords = interpolate_fn(geometry, miles_driven + chunk_miles / 2)
            location = get_location_fn(coords, miles_driven + chunk_miles / 2, total_miles)
            chunk_hours = chunk_miles / MPH

        # Fuel check mid-chunk
        miles_to_fuel = FUEL_INTERVAL_MILES - state.miles_since_fuel
        if miles_to_fuel < chunk_miles:
            # Drive to fuel point first
            hrs_to_fuel = miles_to_fuel / MPH
            fuel_coords = interpolate_fn(geometry, miles_driven + miles_to_fuel)
            fuel_loc = get_location_fn(fuel_coords, miles_driven + miles_to_fuel, total_miles)
            if hrs_to_fuel > 0:
                add_seg("DRIVING", hrs_to_fuel, fuel_loc, fuel_coords, f"Driving to {fuel_loc}")
                state.driving_today += hrs_to_fuel
                state.cycle_used += hrs_to_fuel
                state.cumulative_driving_for_break += hrs_to_fuel
                miles_driven += miles_to_fuel
                state.miles_since_fuel += miles_to_fuel
                chunk_miles -= miles_to_fuel
                chunk_hours -= hrs_to_fuel
            maybe_fuel(fuel_loc, fuel_coords)
            # Continue with remaining chunk
            coords = interpolate_fn(geometry, miles_driven + chunk_miles / 2)
            location = get_location_fn(coords, miles_driven + chunk_miles / 2, total_miles)
            chunk_hours = chunk_miles / MPH

        if chunk_hours <= 0 or chunk_miles <= 0:
            continue

        # Drive the chunk 
        # Don't exceed remaining duty window
        duty_elapsed = state.clock - state.duty_window_start
        window_remaining = MAX_DUTY_WINDOW - duty_elapsed
        drive_cap = min(
            chunk_hours,
            MAX_DRIVING_HOURS - state.driving_today,
            max(window_remaining, 0),
            (MAX_CYCLE - state.cycle_used),
        )

        if drive_cap <= 0:
            # Need rest before driving more
            if state.driving_today >= MAX_DRIVING_HOURS or duty_elapsed >= MAX_DUTY_WINDOW:
                do_overnight(location, coords)
            else:
                do_restart(location, coords)
            start_shift()
            drive_cap = min(chunk_hours, MAX_DRIVING_HOURS)

        actual_drive = min(drive_cap, chunk_hours)
        actual_miles = actual_drive * MPH

        add_seg("DRIVING", actual_drive, location, coords, f"Driving to {location}")
        state.driving_today += actual_drive
        state.cycle_used += actual_drive
        state.cumulative_driving_for_break += actual_drive
        miles_driven += actual_miles
        state.miles_since_fuel += actual_miles

        # If we couldn't drive the full chunk, rest then continue
        if actual_miles < chunk_miles - 0.01:
            rest_coords = interpolate_fn(geometry, miles_driven)
            rest_loc = get_location_fn(rest_coords, miles_driven, total_miles)
            do_overnight(rest_loc, rest_coords)
            start_shift()
            leftover_miles = chunk_miles - actual_miles
            leftover_hours = leftover_miles / MPH
            leftover_coords = interpolate_fn(geometry, miles_driven + leftover_miles / 2)
            leftover_loc = get_location_fn(leftover_coords, miles_driven + leftover_miles / 2, total_miles)
            add_seg("DRIVING", leftover_hours, leftover_loc, leftover_coords,
                    f"Driving to {leftover_loc}")
            state.driving_today += leftover_hours
            state.cycle_used += leftover_hours
            state.cumulative_driving_for_break += leftover_hours
            miles_driven += leftover_miles
            state.miles_since_fuel += leftover_miles

    # Dropoff  
    dropoff_coords = interpolate_fn(geometry, total_miles) if geometry else None
    add_stop("dropoff", dropoff_location, dropoff_coords, DROPOFF_DURATION,
             "Dropoff — unloading cargo (1 hour on-duty)")
    add_seg("ON_DUTY_NOT_DRIVING", DROPOFF_DURATION, dropoff_location, dropoff_coords,
            f"Dropoff at {dropoff_location}")
    state.cycle_used += DROPOFF_DURATION

    # Final off-duty 
    add_seg("OFF_DUTY", 0.01, dropoff_location, dropoff_coords, "Trip complete")

    # Split across midnight 
    segments = _split_across_midnight(segments)

    eta_hours = state.clock
    return segments, stops, round(eta_hours, 2)


def group_segments_by_day(segments: list[Segment]) -> dict[int, list[Segment]]:
    """Group segments into days based on absolute clock position."""
    days: dict[int, list[Segment]] = {}
    for seg in segments:
        day, _ = _clock_to_day_hour(seg.start)
        days.setdefault(day, []).append(seg)
    return days


def compute_daily_totals(day_segs: list[Segment]) -> dict:
    totals = {"OFF_DUTY": 0.0, "SLEEPER_BERTH": 0.0, "DRIVING": 0.0, "ON_DUTY_NOT_DRIVING": 0.0}
    for seg in day_segs:
        totals[seg.status] = round(totals[seg.status] + seg.duration, 4)
    return totals


def compute_daily_remarks(day_segs: list[Segment]) -> list[str]:
    """Extract unique location remarks for the day."""
    seen = set()
    remarks = []
    for seg in day_segs:
        if seg.location and seg.location not in seen:
            seen.add(seg.location)
            remarks.append(seg.location)
    return remarks
