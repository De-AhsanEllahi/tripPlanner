"""
FMCSA Daily Log Generator.
Draws one page per day using ReportLab — horizontal lines, vertical transitions,
no filled rectangles — mimicking paper ELD logs.
"""
from __future__ import annotations
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch

from .hos_engine import (
    DAY_START_HOUR,
    Segment,
    compute_daily_totals,
    compute_daily_remarks,
)

# Layout constants (points, 72pt = 1 inch)
PAGE_W, PAGE_H = letter  # 612 x 792

MARGIN_L = 0.5 * inch
MARGIN_R = PAGE_W - 0.5 * inch
MARGIN_TOP = PAGE_H - 0.5 * inch
MARGIN_BOT = 0.5 * inch

GRID_LEFT = MARGIN_L + 1.5 * inch
GRID_RIGHT = MARGIN_R
GRID_TOP = PAGE_H - 2.8 * inch
GRID_BOTTOM = GRID_TOP - 1.6 * inch

GRID_W = GRID_RIGHT - GRID_LEFT
GRID_H = GRID_BOTTOM - GRID_TOP  # negative (grows downward)
GRID_H_ABS = abs(GRID_H)

ROW_H = GRID_H_ABS / 4          # 4 rows: Off Duty, Sleeper, Driving, On Duty
ROW_LABELS = ["Off Duty", "Sleeper\nBerth", "Driving", "On Duty\n(not driving)"]

STATUS_ROW = {
    "OFF_DUTY": 0,
    "SLEEPER_BERTH": 1,
    "DRIVING": 2,
    "ON_DUTY_NOT_DRIVING": 3,
}


def _row_y(row: int) -> float:
    """Y coordinate of the CENTER of a row (measured from bottom of page)."""
    return GRID_TOP - row * ROW_H - ROW_H / 2


def _time_to_x(hour_in_day: float) -> float:
    """Map 0–24 hour within a calendar day to X pixel on the grid."""
    return GRID_LEFT + (hour_in_day / 24.0) * GRID_W


def _seg_day_hours(seg: Segment) -> tuple[float, float]:
    """
    Convert segment's absolute clock times to within-day hours (0–24).
    The segment must already have been midnight-split.
    """
    abs_start = DAY_START_HOUR + seg.start
    abs_end = DAY_START_HOUR + seg.end
    day_start = int(abs_start // 24) * 24
    h_start = abs_start - day_start
    h_end = abs_end - day_start
    # Clamp to 0-24
    h_start = max(0.0, min(24.0, h_start))
    h_end = max(0.0, min(24.0, h_end))
    return h_start, h_end


def draw_log_page(
    c: canvas.Canvas,
    day_number: int,
    day_segs: list[Segment],
    trip_id: int,
    total_miles: float,
    carrier_name: str = "Assessment Carrier",
    carrier_address: str = "N/A",
    truck_number: str = "TRK-001",
    shipping_number: str = "SHIP-001",
):
    """Draw a complete FMCSA log page onto the canvas at the current page position."""
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN_L, MARGIN_TOP - 0.1 * inch, "DRIVER'S DAILY LOG")

    c.setFont("Helvetica", 9)
    c.drawString(MARGIN_L, MARGIN_TOP - 0.35 * inch, f"Day {day_number}  |  Trip #{trip_id}")

    # Header fields
    y_hdr = MARGIN_TOP - 0.65 * inch
    fields_left = [
        ("Carrier Name:", carrier_name),
        ("Carrier Address:", carrier_address),
        ("Truck/Tractor #:", truck_number),
    ]
    fields_right = [
        ("Shipping Doc #:", shipping_number),
        ("Total Miles:", f"{total_miles:.0f} mi (total trip)"),
    ]
    c.setFont("Helvetica", 8)
    for label, value in fields_left:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(MARGIN_L, y_hdr, label)
        c.setFont("Helvetica", 8)
        c.drawString(MARGIN_L + 1.1 * inch, y_hdr, value)
        y_hdr -= 0.2 * inch

    y_hdr = MARGIN_TOP - 0.65 * inch
    for label, value in fields_right:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(MARGIN_L + 4 * inch, y_hdr, label)
        c.setFont("Helvetica", 8)
        c.drawString(MARGIN_L + 5.4 * inch, y_hdr, value)
        y_hdr -= 0.2 * inch

    # Hour ruler 
    c.setFont("Helvetica", 6)
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    for h in range(25):
        x = _time_to_x(h)
        tick_len = 6 if h % 6 == 0 else 3
        # Top tick
        c.line(x, GRID_TOP, x, GRID_TOP + tick_len)
        if h % 2 == 0:
            tick_label = f"{h:02d}"
            c.drawCentredString(x, GRID_TOP + 8, tick_label)

    # Grid lines 
    c.setLineWidth(0.3)
    c.setStrokeColor(colors.lightgrey)
    # Vertical hour lines
    for h in range(1, 24):
        x = _time_to_x(h)
        c.line(x, GRID_TOP, x, GRID_TOP - GRID_H_ABS)

    # Horizontal row dividers
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    for row in range(5):
        y = GRID_TOP - row * ROW_H
        c.line(GRID_LEFT, y, GRID_RIGHT, y)

    # Row labels
    c.setFont("Helvetica-Bold", 7)
    label_x = MARGIN_L + 0.05 * inch
    for row, row_label in enumerate(ROW_LABELS):
        cy = GRID_TOP - row * ROW_H - ROW_H / 2
        for i, part in enumerate(row_label.split("\n")):
            c.drawString(label_x, cy + (0.07 * inch if "\n" in row_label else 0) - i * 0.1 * inch, part)

    # Outer border
    c.setLineWidth(1)
    c.rect(GRID_LEFT, GRID_TOP - GRID_H_ABS, GRID_W, GRID_H_ABS)

    #  Plot duty status lines 
    c.setLineWidth(2)

    # Sort segments within the day by start time
    sorted_segs = sorted(day_segs, key=lambda s: s.start)

    prev_row = None
    prev_x = None

    for seg in sorted_segs:
        h_start, h_end = _seg_day_hours(seg)
        if h_end <= h_start:
            continue

        row = STATUS_ROW.get(seg.status, 0)
        x1 = _time_to_x(h_start)
        x2 = _time_to_x(h_end)
        cy = _row_y(row)

        # Vertical transition from previous row
        if prev_row is not None and prev_row != row and prev_x is not None:
            prev_cy = _row_y(prev_row)
            c.setStrokeColor(colors.black)
            c.line(prev_x, prev_cy, prev_x, cy)  # vertical drop/rise

        # Horizontal line for this status
        c.setStrokeColor(colors.HexColor("#0047AB"))
        c.line(x1, cy, x2, cy)

        prev_row = row
        prev_x = x2

    #  Totals section 
    totals = compute_daily_totals(day_segs)
    total_y = GRID_TOP - GRID_H_ABS - 0.35 * inch
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN_L, total_y, "Daily Totals (hours):")
    c.setFont("Helvetica", 8)
    col_x = MARGIN_L
    for status, label in [
        ("OFF_DUTY", "Off Duty"),
        ("SLEEPER_BERTH", "Sleeper"),
        ("DRIVING", "Driving"),
        ("ON_DUTY_NOT_DRIVING", "On Duty"),
    ]:
        val = totals.get(status, 0.0)
        c.drawString(col_x, total_y - 0.2 * inch, f"{label}: {val:.2f} h")
        col_x += 1.7 * inch

    grand_total = sum(totals.values())
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN_L, total_y - 0.4 * inch, f"Total: {grand_total:.2f} h (should equal 24.00 h)")

    # Remarks 
    remarks = compute_daily_remarks(day_segs)
    remarks_y = total_y - 0.65 * inch
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN_L, remarks_y, "Remarks / Locations:")
    c.setFont("Helvetica", 7)
    col1, col2 = [], []
    for i, r in enumerate(remarks[:20]):
        if i % 2 == 0:
            col1.append(r)
        else:
            col2.append(r)
    for i, r in enumerate(col1):
        c.drawString(MARGIN_L, remarks_y - 0.18 * inch - i * 0.14 * inch, f"• {r}")
    for i, r in enumerate(col2):
        c.drawString(MARGIN_L + 3.5 * inch, remarks_y - 0.18 * inch - i * 0.14 * inch, f"• {r}")

    # Footer
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.grey)
    c.drawString(MARGIN_L, MARGIN_BOT, "Form FMCSA-391.2 | ELD Assessment Log | For review purposes only")
    c.setFillColor(colors.black)


def generate_pdf_bytes(
    days: dict[int, list[Segment]],
    trip_id: int,
    total_miles: float,
    carrier_name: str = "Assessment Carrier",
    carrier_address: str = "N/A",
    truck_number: str = "TRK-001",
    shipping_number: str = "SHIP-001",
) -> bytes:
    """Generate a combined PDF with one page per day. Returns raw bytes."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)

    for day_number in sorted(days.keys()):
        day_segs = days[day_number]
        draw_log_page(
            c,
            day_number,
            day_segs,
            trip_id,
            total_miles,
            carrier_name,
            carrier_address,
            truck_number,
            shipping_number,
        )
        c.showPage()

    c.save()
    buf.seek(0)
    return buf.read()


def generate_log_image_bytes(
    day_number: int,
    day_segs: list[Segment],
    trip_id: int,
    total_miles: float,
) -> bytes:
    """Render a single day log as PDF bytes (one page)."""
    return generate_pdf_bytes(
        {day_number: day_segs},
        trip_id,
        total_miles,
    )
