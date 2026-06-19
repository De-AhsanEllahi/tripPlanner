"""
Unit tests for HOS engine, fuel logic, and route utilities.
Run with: python manage.py test api
"""
from django.test import SimpleTestCase as TestCase
from .services.hos_engine import (
    build_trip_timeline,
    group_segments_by_day,
    compute_daily_totals,
    _clock_to_day_hour,
    _split_across_midnight,
    Segment,
    MPH,
)


def _stub_geometry(miles: float):
    return [[0.0, 0.0], [miles / 69.0, 0.0]]


def _get_loc(coords, mile, total):
    return f"Mile {int(mile)}"


def _interp(geom, mile):
    return geom[0] if geom else [0.0, 0.0]


def _run(miles, cycle_used=0):
    geom = _stub_geometry(miles)
    return build_trip_timeline(
        total_miles=miles,
        cycle_used=cycle_used,
        geometry=geom,
        pickup_location="Pickup City",
        dropoff_location="Dropoff City",
        current_location="Start City",
        get_location_fn=_get_loc,
        interpolate_fn=_interp,
    )


class ClockHelpersTest(TestCase):
    def test_day_one_start(self):
        day, _ = _clock_to_day_hour(0)
        self.assertEqual(day, 1)

    def test_crosses_midnight(self):
        day, hour = _clock_to_day_hour(18)
        self.assertEqual(day, 2)
        self.assertAlmostEqual(hour, 0.0, places=3)


class MidnightSplitTest(TestCase):
    def test_no_split_needed(self):
        seg = Segment("DRIVING", 0, 5, "Loc")
        result = _split_across_midnight([seg])
        self.assertEqual(len(result), 1)

    def test_split_across_midnight(self):
        seg = Segment("DRIVING", 17, 22, "Loc")
        result = _split_across_midnight([seg])
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[0].end, 18.0, places=3)


class ShortTripTest(TestCase):
    def test_short_trip_single_day(self):
        segs, stops, eta = _run(200)
        days = group_segments_by_day(segs)
        self.assertEqual(len(days), 1)

    def test_short_trip_no_fuel(self):
        _, stops, _ = _run(200)
        self.assertEqual(len([s for s in stops if s.stop_type == "fuel"]), 0)

    def test_short_trip_has_pickup_dropoff(self):
        _, stops, _ = _run(200)
        types = [s.stop_type for s in stops]
        self.assertIn("pickup", types)
        self.assertIn("dropoff", types)


class FuelStopTest(TestCase):
    def test_fuel_stop_at_1000(self):
        _, stops, _ = _run(1200)
        self.assertGreaterEqual(len([s for s in stops if s.stop_type == "fuel"]), 1)

    def test_no_fuel_under_1000(self):
        _, stops, _ = _run(999)
        self.assertEqual(len([s for s in stops if s.stop_type == "fuel"]), 0)

    def test_two_fuel_stops_2000_miles(self):
        _, stops, _ = _run(2200)
        self.assertGreaterEqual(len([s for s in stops if s.stop_type == "fuel"]), 2)


class BreakTest(TestCase):
    def test_break_after_8_hours(self):
        _, stops, _ = _run(500)
        self.assertGreaterEqual(len([s for s in stops if s.stop_type == "break"]), 1)

    def test_no_break_under_8_hours(self):
        _, stops, _ = _run(300)
        self.assertEqual(len([s for s in stops if s.stop_type == "break"]), 0)


class CycleRestartTest(TestCase):
    def test_restart_when_cycle_exhausted(self):
        _, stops, _ = _run(miles=3000, cycle_used=69)
        self.assertGreaterEqual(len([s for s in stops if s.stop_type == "restart"]), 1)

    def test_no_restart_when_cycle_ok(self):
        _, stops, _ = _run(miles=300, cycle_used=0)
        self.assertEqual(len([s for s in stops if s.stop_type == "restart"]), 0)


class DailyTotalsTest(TestCase):
    def test_totals_reasonable(self):
        segs, _, _ = _run(800)
        days = group_segments_by_day(segs)
        for day_num, day_segs in days.items():
            totals = compute_daily_totals(day_segs)
            self.assertLessEqual(sum(totals.values()), 24.1)
            self.assertGreater(sum(totals.values()), 0)

    def test_driving_status_present(self):
        segs, _, _ = _run(300)
        self.assertGreater(len([s for s in segs if s.status == "DRIVING"]), 0)

    def test_sleeper_present_long_trip(self):
        segs, _, _ = _run(1000)
        self.assertGreater(len([s for s in segs if s.status == "SLEEPER_BERTH"]), 0)


class MultiDayTripTest(TestCase):
    def test_long_trip_multi_day(self):
        segs, _, _ = _run(2000)
        days = group_segments_by_day(segs)
        self.assertGreater(len(days), 1)

    def test_eta_includes_rest(self):
        miles = 1000
        _, _, eta = _run(miles)
        self.assertGreater(eta, miles / MPH)
