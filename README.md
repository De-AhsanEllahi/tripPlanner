# ELD Trip Planner

Full-stack FMCSA-compliant ELD trip planner with HOS enforcement, interactive map, daily log generation, and PDF export.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18 + TypeScript + Vite + MUI v9 + React Leaflet |
| Backend | Django 5 + Django REST Framework |
| Database | PostgreSQL 15 |
| Routing | OpenRouteService API |
| Map | OpenStreetMap (Leaflet) |
| PDF | ReportLab |
| Container | Docker + Docker Compose |

---

## Quick Start (Docker)

### 1. Add your ORS API key

Open `backend/.env` and set:

```
ORS_API_KEY=your_actual_key_here
```

### 2. Start all services

```bash
docker compose up --build
```

- Frontend: http://localhost:5173  
- Backend API: http://localhost:8000/api/  
- Admin: http://localhost:8000/admin/

Migrations run automatically on backend startup.

---

## Local Development (without Docker)

### Backend

```bash
cd backend
uv sync
# Edit .env — set DB_HOST=localhost and your ORS_API_KEY
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/trips/` | Create trip, calculate route + HOS |
| `GET` | `/api/trips/{id}/` | Get trip with stops and daily logs |
| `GET` | `/api/trips/{id}/logs/` | Get daily logs only |
| `GET` | `/api/trips/{id}/pdf/` | Download combined PDF |
| `GET` | `/api/health/` | Health check |

### POST /api/trips/ — Request body

```json
{
  "current_location": "Dallas, TX",
  "pickup_location": "Houston, TX",
  "dropoff_location": "Chicago, IL",
  "current_cycle_used": 20
}
```

---

## HOS Rules Implemented

| Rule | Value |
|------|-------|
| Max driving per shift | 11 hours |
| Duty window | 14 hours |
| Mandatory break | 30 min after 8 cumulative driving hours |
| Overnight rest | 10 hours (Sleeper Berth) |
| Cycle limit | 70 hours / 8 days |
| Restart | 34 hours Off Duty when cycle exhausted |
| Fuel stop | Every 1,000 miles (30 min On Duty) |
| Pickup / Dropoff | 1 hour On Duty each |
| Speed assumption | 55 MPH |

---

## Running Tests

```bash
cd backend
.venv/bin/python manage.py test api --verbosity=2
```

19 unit tests covering: HOS engine, fuel logic, break logic, cycle restart, midnight splitting, multi-day trips, ETA accuracy.

---

## Adding Your ORS API Key

The only environment variable you need to add manually:

**File:** `backend/.env`

```
ORS_API_KEY=your_key_here
```

Get a free key at: https://openrouteservice.org/dev/#/signup

The key is used for:
1. Geocoding addresses → coordinates (ORS `/geocode/search`)
2. Route calculation (ORS `/v2/directions/driving-car`)

Fallback: If ORS geocoding fails, Nominatim (OpenStreetMap) is used automatically.
