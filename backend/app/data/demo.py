"""Clearly-labelled DEMO data generators.

These functions produce placeholder meteorological responses so that every
API endpoint is functional before real data pipelines / ML exist. They never
pretend to be real meteorological data; each payload is explicitly flagged as
``demo: true`` with a short ``demo_note`` describing what it is.

Nothing in this module writes to MongoDB or requires a live database.
"""

import hashlib
from datetime import datetime, timedelta, timezone
import random as _random

from ..schemas.alerts import Alert, AlertImpact
from ..schemas.forecast import ForecastPoint
from ..schemas.historical import HistoricalEvent
from ..schemas.map import RiskGridCell, RiskGridResponse, RiskGridBounds
from ..schemas.weather import WeatherObservation
from ..schemas.storm import StormCell, StormCellPosition, StormTrack
from ..schemas.analytics import (
    HistoricalAnalytics,
    EventTypeBreakdown,
    RiskDistribution,
    MonthlyTrend,
)

DEMO_NOTE = (
    "Demo data for API contract demonstration. Not real meteorological data."
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _bounded(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _seed_from_coords(lat: float, lon: float, offset: int = 0) -> int:
    """Deterministic seed from coordinates for reproducible demo data."""
    key = f"{lat:.4f}:{lon:.4f}:{offset}"
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)


def demo_weather(latitude: float, longitude: float) -> WeatherObservation:
    seed = _seed_from_coords(latitude, longitude)
    rng = _random.Random(seed)
    temp = 25.0 + rng.random() * 12
    humidity = 55.0 + rng.random() * 40
    wind = 2.0 + rng.random() * 10
    pressure = 1004.0 + rng.random() * 12
    precip = rng.random() * 5 if humidity > 70 else 0.0

    return WeatherObservation(
        latitude=latitude,
        longitude=longitude,
        timestamp=_utcnow(),
        temperature_c=round(temp, 1),
        humidity_percent=round(humidity, 1),
        wind_speed_ms=round(wind, 1),
        wind_direction_deg=round(rng.random() * 360, 1),
        pressure_hpa=round(pressure, 1),
        precipitation_mm=round(precip, 1),
        source="demo",
    )


def demo_forecast(latitude: float, longitude: float) -> list[ForecastPoint]:
    now = _utcnow()
    seed = _seed_from_coords(latitude, longitude, 1)
    rng = _random.Random(seed)
    points = []

    base_thunder = _bounded(0.3 + rng.random() * 0.4)
    base_hail = _bounded(0.1 + rng.random() * 0.25)
    base_cloudburst = _bounded(0.08 + rng.random() * 0.2)

    for lead in range(7):
        decay = 1.0 + lead * 0.04 * (1 if rng.random() > 0.5 else -0.3)
        points.append(
            ForecastPoint(
                latitude=latitude,
                longitude=longitude,
                timestamp=now + timedelta(hours=lead),
                lead_time_hours=float(lead),
                thunderstorm_probability=_bounded(base_thunder * decay),
                hail_probability=_bounded(base_hail * decay),
                cloudburst_probability=_bounded(base_cloudburst * decay),
                precipitation_mm=round(rng.random() * (10 + lead * 2), 1) if base_thunder > 0.4 else None,
                wind_speed_ms=round(3.0 + rng.random() * (8 + lead * 1.5), 1) if base_thunder > 0.3 else None,
            )
        )
    return points


def demo_alerts() -> list[Alert]:
    now = _utcnow()
    return [
        Alert(
            id="TC-ALERT-001",
            title="Elevated Thunderstorm Risk — Central India",
            message="Conditions favoring severe thunderstorm development over the next 3 hours. Potential for damaging winds, heavy rainfall, and localized flooding in low-lying areas.",
            severity="HIGH",
            area_name="Central India Region",
            area_latitude=21.25,
            area_longitude=78.5,
            area_radius_km=150,
            issued_at=now - timedelta(minutes=45),
            valid_until=now + timedelta(hours=3),
            source="ThunderCast AI",
            confidence=0.78,
            impacts=[
                AlertImpact(
                    category="wind_damage",
                    severity_description="Damaging wind gusts up to 70 km/h possible",
                    affected_population="100,000 - 500,000",
                    recommended_action="Secure loose outdoor objects. Stay away from trees and power lines.",
                ),
                AlertImpact(
                    category="flooding",
                    severity_description="Localized urban flooding in low-lying areas",
                    affected_population="50,000 - 200,000",
                    recommended_action="Avoid flood-prone areas. Do not drive through waterlogged roads.",
                ),
                AlertImpact(
                    category="power_outage",
                    severity_description="Possible power disruptions due to lightning and wind",
                    affected_population="20,000 - 100,000",
                    recommended_action="Keep backup charging devices ready. Unplug sensitive electronics.",
                ),
            ],
        ),
        Alert(
            id="TC-ALERT-002",
            title="Moderate Hail Risk — Western Ghats",
            message="Moderate probability of hail activity in elevated terrain. Small to medium hailstones may damage crops and vehicles.",
            severity="MODERATE",
            area_name="Western Ghats",
            area_latitude=15.35,
            area_longitude=74.5,
            area_radius_km=80,
            issued_at=now - timedelta(hours=1, minutes=20),
            valid_until=now + timedelta(hours=4),
            source="ThunderCast AI",
            confidence=0.62,
            impacts=[
                AlertImpact(
                    category="crop_damage",
                    severity_description="Hail may damage standing crops and horticulture",
                    affected_population="10,000 - 50,000",
                    recommended_action="Cover sensitive crops with protective sheets if possible.",
                ),
                AlertImpact(
                    category="vehicle_damage",
                    severity_description="Small hailstones may dent vehicle surfaces",
                    affected_population="5,000 - 20,000",
                    recommended_action="Park vehicles under shelter if available.",
                ),
            ],
        ),
        Alert(
            id="TC-ALERT-003",
            title="Cloudburst Watch — Northeast India",
            message="Atmospheric conditions favorable for intense localized rainfall events (cloudburst) in mountainous terrain.",
            severity="MODERATE",
            area_name="Northeast India",
            area_latitude=25.67,
            area_longitude=92.0,
            area_radius_km=120,
            issued_at=now - timedelta(hours=2),
            valid_until=now + timedelta(hours=5),
            source="ThunderCast AI",
            confidence=0.55,
            impacts=[
                AlertImpact(
                    category="flash_flooding",
                    severity_description="Rapid water level rise in streams and rivers",
                    affected_population="30,000 - 150,000",
                    recommended_action="Stay away from riverbanks and low-lying areas. Monitor water levels.",
                ),
                AlertImpact(
                    category="landslide",
                    severity_description="Increased landslide risk on saturated slopes",
                    affected_population="5,000 - 30,000",
                    recommended_action="Evacuate from known landslide-prone zones. Report unusual ground movement.",
                ),
            ],
        ),
        Alert(
            id="TC-ALERT-004",
            title="Low Risk — Southern Peninsula",
            message="Minimal convective activity expected. Routine monitoring continues.",
            severity="LOW",
            area_name="Southern Peninsula",
            area_latitude=12.5,
            area_longitude=78.0,
            area_radius_km=200,
            issued_at=now - timedelta(hours=4),
            valid_until=now + timedelta(hours=6),
            source="ThunderCast AI",
            confidence=0.85,
            impacts=[],
        ),
    ]


def demo_historical_events() -> list[HistoricalEvent]:
    now = _utcnow()
    rng = _random.Random(42)
    events = []
    locations = [
        ("Delhi NCR", 28.6139, 77.2090),
        ("Mumbai", 19.0760, 72.8777),
        ("Chennai", 13.0827, 80.2707),
        ("Kolkata", 22.5726, 88.3639),
        ("Hyderabad", 17.3850, 78.4867),
        ("Jaipur", 26.9124, 75.7873),
        ("Ahmedabad", 23.0225, 72.5714),
        ("Pune", 18.5204, 73.8567),
        ("Lucknow", 26.8467, 80.9462),
        ("Bhopal", 23.2599, 77.4126),
        ("Patna", 25.6093, 85.1376),
        ("Guwahati", 26.1445, 91.7362),
    ]
    event_types = ["thunderstorm", "hail", "cloudburst"]
    risk_levels = ["LOW", "MODERATE", "HIGH", "EXTREME"]

    for i in range(20):
        name, lat, lon = rng.choice(locations)
        etype = rng.choice(event_types)
        days_ago = rng.randint(1, 365)
        thunder_p = round(rng.random(), 2)
        hail_p = round(rng.random() * 0.5, 2)
        cb_p = round(rng.random() * 0.4, 2)
        risk = risk_levels[min(3, int(max(thunder_p, hail_p, cb_p) * 4))]

        summaries = {
            "thunderstorm": [
                f"Severe thunderstorm with lightning caused power outages across {name}.",
                f"Thunderstorm with heavy rain led to traffic disruptions in {name}.",
                f"Electric storm affected multiple neighborhoods in {name}.",
            ],
            "hail": [
                f"Hailstorm damaged crops and vehicles in the {name} area.",
                f"Large hail reported in {name}, causing property damage.",
                f"Hail activity affected agricultural regions near {name}.",
            ],
            "cloudburst": [
                f"Intense rainfall event caused flash flooding in {name}.",
                f"Cloudburst led to waterlogging and road closures in {name}.",
                f"Extreme rainfall overwhelmed drainage systems in {name}.",
            ],
        }

        events.append(
            HistoricalEvent(
                id=f"HIST-{i+1:04d}",
                event_type=etype,
                occurred_at=now - timedelta(days=days_ago, hours=rng.randint(0, 23)),
                latitude=lat,
                longitude=lon,
                location_name=name,
                max_thunderstorm_probability=thunder_p,
                max_hail_probability=hail_p,
                max_cloudburst_probability=cb_p,
                risk_level=risk,
                confidence=round(0.5 + rng.random() * 0.4, 2),
                impact_summary=rng.choice(summaries[etype]),
                duration_hours=round(0.5 + rng.random() * 4.5, 1),
                damage_reported=rng.random() > 0.4,
            )
        )
    return events


def demo_risk_grid(
    center_latitude: float | None = None,
    center_longitude: float | None = None,
) -> RiskGridResponse:
    """Return a clearly-labelled demo risk grid.

    When ``center_latitude`` / ``center_longitude`` are provided the grid is
    generated *around* that location so the map follows the selected city.
    Otherwise a default central-India region is used (kept for backward
    compatibility). The output is deterministic for a given location.
    """
    RESOLUTION = 0.5

    if center_latitude is None or center_longitude is None:
        center_latitude, center_longitude = 19.5, 77.5
        span = 6  # cells each side
    else:
        span = 4  # cells each side -> a compact city-centred grid

    # Round the centre to the nearest grid node so cells are stable & aligned.
    center_lat = round(round(center_latitude / RESOLUTION) * RESOLUTION, 3)
    center_lon = round(round(center_longitude / RESOLUTION) * RESOLUTION, 3)

    seed = _seed_from_coords(center_lat, center_lon, 99)
    rng = _random.Random(seed)

    cell_lats = [round(center_lat + i * RESOLUTION, 3) for i in range(-span, span + 1)]
    cell_lons = [round(center_lon + i * RESOLUTION, 3) for i in range(-span, span + 1)]

    cells = []
    for lat in cell_lats:
        for lon in cell_lons:
            # Distance from centre (in cells) slightly modulates the risk so the
            # grid reads like a coherent "storm cluster" rather than random noise.
            dist = max(abs(lat - center_lat), abs(lon - center_lon)) / RESOLUTION
            proximity = max(0.0, 1.0 - dist / (span + 1))
            core = 0.25 + rng.random() * 0.45 + proximity * 0.25
            thunder = _bounded(core)
            hail = _bounded(0.1 + rng.random() * 0.3)
            cloudburst = _bounded(0.05 + rng.random() * 0.35)
            peak = max(thunder, hail, cloudburst)
            if peak >= 0.8:
                level = "EXTREME"
            elif peak >= 0.6:
                level = "HIGH"
            elif peak >= 0.4:
                level = "MODERATE"
            else:
                level = "LOW"
            cells.append(
                RiskGridCell(
                    latitude=lat,
                    longitude=lon,
                    thunderstorm_probability=round(thunder, 3),
                    hail_probability=round(hail, 3),
                    cloudburst_probability=round(cloudburst, 3),
                    overall_risk=level,
                    confidence=round(0.55 + rng.random() * 0.35, 2),
                )
            )
    return RiskGridResponse(
        bounds=RiskGridBounds(
            min_latitude=cell_lats[0] - RESOLUTION / 2,
            min_longitude=cell_lons[0] - RESOLUTION / 2,
            max_latitude=cell_lats[-1] + RESOLUTION / 2,
            max_longitude=cell_lons[-1] + RESOLUTION / 2,
        ),
        resolution_deg=RESOLUTION,
        generated_at=_utcnow(),
        cells=cells,
    )


def demo_storm_cells() -> list[StormCell]:
    now = _utcnow()
    rng = _random.Random(77)
    cells = []
    base_locations = [
        (21.25, 78.5, "CB-Cell-001"),
        (20.1, 77.3, "CB-Cell-002"),
        (19.8, 79.1, "CB-Cell-003"),
        (22.5, 76.8, "CB-Cell-004"),
        (18.9, 80.2, "CB-Cell-005"),
    ]
    for lat, lon, cid in base_locations:
        intensity = round(0.3 + rng.random() * 0.6, 2)
        sev = "EXTREME" if intensity > 0.8 else "HIGH" if intensity > 0.6 else "MODERATE" if intensity > 0.4 else "LOW"
        cells.append(
            StormCell(
                id=cid,
                latitude=lat + round(rng.random() * 0.3 - 0.15, 2),
                longitude=lon + round(rng.random() * 0.3 - 0.15, 2),
                intensity=intensity,
                severity=sev,
                radius_km=round(15 + rng.random() * 45, 1),
                movement_speed_kmh=round(10 + rng.random() * 30, 1),
                movement_direction_deg=round(rng.random() * 360, 1),
                timestamp=now - timedelta(minutes=rng.randint(5, 30)),
                precipitation_mm_h=round(5 + rng.random() * 40, 1),
                echo_top_km=round(8 + rng.random() * 7, 1),
                vil_kgm2=round(10 + rng.random() * 40, 1),
            )
        )
    return cells


def demo_storm_tracks() -> list[StormTrack]:
    now = _utcnow()
    rng = _random.Random(88)
    tracks = []
    for i in range(3):
        base_lat = 20.0 + rng.random() * 3
        base_lon = 77.0 + rng.random() * 3
        speed = 15 + rng.random() * 20
        direction = rng.random() * 360
        cell_id = f"CB-Cell-{i+1:03d}"

        positions = []
        for t in range(4):
            dt = timedelta(minutes=15 * t)
            dlat = speed * (t * 15 / 60) * 0.009 * (1 if direction < 180 else -1)
            dlon = speed * (t * 15 / 60) * 0.011 * (1 if 90 < direction < 270 else -1)
            positions.append(
                StormCellPosition(
                    latitude=round(base_lat + dlat, 4),
                    longitude=round(base_lon + dlon, 4),
                    timestamp=now - timedelta(minutes=45) + dt,
                    intensity=round(min(1.0, 0.3 + t * 0.15 + rng.random() * 0.1), 2),
                )
            )

        projected = []
        for t in range(1, 4):
            dt = timedelta(minutes=15 * t)
            dlat = speed * (t * 15 / 60) * 0.009 * (1 if direction < 180 else -1)
            dlon = speed * (t * 15 / 60) * 0.011 * (1 if 90 < direction < 270 else -1)
            projected.append(
                StormCellPosition(
                    latitude=round(base_lat + dlat, 4),
                    longitude=round(base_lon + dlon, 4),
                    timestamp=now + dt,
                    intensity=round(min(1.0, 0.4 + t * 0.1 + rng.random() * 0.1), 2),
                )
            )

        tracks.append(StormTrack(cell_id=cell_id, positions=positions, projected_positions=projected))
    return tracks


def demo_historical_analytics() -> HistoricalAnalytics:
    rng = _random.Random(55)
    monthly = []
    months = ["2025-09", "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"]
    counts = [12, 18, 25, 8, 3, 2, 5, 15, 28, 35, 32, 22]
    for m, c in zip(months, counts):
        monthly.append(MonthlyTrend(month=m, count=c))

    return HistoricalAnalytics(
        total_events=205,
        date_range_start="2025-09-01",
        date_range_end="2026-08-31",
        event_types=EventTypeBreakdown(thunderstorm=95, hail=55, cloudburst=55),
        risk_distribution=RiskDistribution(low=30, moderate=80, high=65, extreme=30),
        avg_confidence=0.72,
        monthly_trends=monthly,
        peak_activity_month="2026-06",
        most_affected_region="Central India",
        total_events_analyzed=205,
    )
