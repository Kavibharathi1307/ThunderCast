"""Intelligence service layer.

Orchestrates the ML modules: provider -> features -> nowcast engine ->
explainability -> impact model -> storm motion. Also handles optional MongoDB
persistence of generated records via the existing database abstraction.

All responses are clearly labelled DEMO / BASELINE because this MVP has no
trained model or real data. MongoDB is strictly optional; when unavailable the
service degrades gracefully to in-memory demo responses.
"""

from __future__ import annotations

import logging

from datetime import datetime, timezone

from ..database import get_collection, ping_database
from ..ml.features import ModelFeatures
from ..ml.predictor import NowcastResult, NowcastPoint, generate_nowcast
from ..ml.risk_engine import WeatherFeatures, assess_risk_structured, StructuredRisk
from ..ml.explainability import (
    explain_structured_risk,
    explain_nowcast,
    PredictionExplanation,
)
from ..ml.impacts import ImpactResult, assess_impacts
from ..ml.providers import DemoDataProvider, DATA_PROVENANCE_LABEL, WeatherDataProvider
from ..ml.real_providers import (
    ProviderUnavailable,
    RealWeatherProvider,
    resolve_feature_provider,
    REAL_PROVENANCE_LABEL,
)
from ..ml.storm_motion import predict_storm_cell, StormPrediction
from ..ml.evaluation import dataset_status, DatasetStatus
from ..ml.training.registry import registry_status, DEFAULT_TARGETS, STATUS_TRAINED, STATUS_UNTRAINED
from ..ml.training.model import STATUS_STALE, STATUS_FAILED
from ..ml.training.tabular import feature_names
from ..config import get_settings
from ..data.demo import (
    DEMO_NOTE,
    demo_storm_cells,
    demo_forecast,
    demo_weather,
)
from ..utils.coordinates import parse_latitude, parse_longitude

logger = logging.getLogger(__name__)

# Resolve the active provider up-front from config. REAL mode uses the live
# Open-Meteo provider; DEMO uses the deterministic demo provider. Both are
# labelled so outputs are never silently mixed.
_provider: WeatherDataProvider = resolve_feature_provider()
_mode = get_settings().ENVIRONMENT_MODE.upper()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def environment_mode() -> str:
    """Return the resolved data mode ('DEMO' or 'REAL')."""
    if _mode == "REAL" and isinstance(_active_provider(), RealWeatherProvider):
        return "REAL"
    return "DEMO"


def current_provenance() -> str:
    """Return the provenance label for the active provider."""
    if _mode == "REAL" and isinstance(_active_provider(), RealWeatherProvider):
        return REAL_PROVENANCE_LABEL
    return DATA_PROVENANCE_LABEL


def _active_provider() -> WeatherDataProvider:
    """Return the configured REAL provider, falling back to DEMO on network error."""
    if _mode == "REAL" and isinstance(_provider, RealWeatherProvider):
        try:
            return _provider
        except Exception:  # pragma: no cover - defensive
            pass
        logger.warning("REAL provider unavailable; falling back to DEMO provider")
        return DemoDataProvider()
    return _provider


def build_features(latitude: float, longitude: float) -> ModelFeatures:
    """Build ModelFeatures for a coordinate via the active data provider."""
    provider = _active_provider()
    try:
        return provider.build_features(latitude, longitude)
    except ProviderUnavailable:
        logger.warning("REAL provider unavailable for (%s, %s); falling back to DEMO", latitude, longitude)
        return DemoDataProvider().build_features(latitude, longitude)


def build_legacy_weather_features(latitude: float, longitude: float) -> WeatherFeatures:
    """Bridge ModelFeatures into the existing risk engine's feature type."""
    mf = build_features(latitude, longitude)
    obs = mf.observation
    return WeatherFeatures(
        latitude=latitude,
        longitude=longitude,
        temperature_c=obs.temperature_c if obs.temperature_c is not None else 29.0,
        humidity_percent=obs.relative_humidity_percent or 70.0,
        wind_speed_ms=obs.wind_speed_ms or 5.0,
        wind_direction_deg=obs.wind_direction_deg or 180.0,
        pressure_hpa=obs.pressure_hpa or 1010.0,
        precipitation_mm=obs.precipitation_mm or 0.0,
        cape_jkg=mf.stability.cape_jkg,
        lifted_index=mf.stability.lifted_index_c,
        wind_shear_ms=mf.stability.wind_shear_ms,
    )


def generate_nowcast_response(
    latitude: float, longitude: float, request_id: str | None = None
) -> tuple[NowcastResult, ImpactResult]:
    """Generate a nowcast + impact assessment for a coordinate."""
    features = build_features(latitude, longitude)
    nowcast = generate_nowcast(features)
    impacts = assess_impacts(features, nowcast)
    if request_id:
        _persist_nowcast(nowcast, impacts, features, request_id)
    return nowcast, impacts


def explain_nowcast_payload(nowcast: NowcastResult) -> PredictionExplanation:
    return explain_nowcast(nowcast)


def structured_risk(latitude: float, longitude: float) -> StructuredRisk:
    wf = build_legacy_weather_features(latitude, longitude)
    return assess_risk_structured(wf)


def explain_risk_payload(latitude: float, longitude: float) -> PredictionExplanation:
    return explain_structured_risk(structured_risk(latitude, longitude))


def storm_predictions() -> list[StormPrediction]:
    """Compute baseline motion predictions for the demo storm cells."""
    cells = demo_storm_cells()
    predictions: list[StormPrediction] = []
    for cell in cells:
        predictions.append(
            predict_storm_cell(
                cell_id=cell.id,
                latitude=cell.latitude,
                longitude=cell.longitude,
                movement_direction_deg=cell.movement_direction_deg,
                movement_speed_kmh=cell.movement_speed_kmh,
                current_intensity=cell.intensity,
            )
        )
    return predictions


def _model_state() -> dict:
    """Return the resolved data/model state (honest, never optimistic)."""
    reg = registry_status(DEFAULT_TARGETS)
    artifacts = reg["artifacts"]
    trained = {t: a for t, a in artifacts.items() if a.get("status") == STATUS_TRAINED}
    any_trained = bool(trained)
    # Status precedence: any trained -> TRAINED; else UNTRAINED (or FAILED/STALE if present).
    if any_trained:
        status = STATUS_TRAINED
    elif any(a.get("status") == STATUS_FAILED for a in artifacts.values()):
        status = STATUS_FAILED
    elif any(a.get("status") == STATUS_STALE for a in artifacts.values()):
        status = STATUS_STALE
    else:
        status = STATUS_UNTRAINED
    # Describe supported vs trained targets.
    trained_targets = sorted(trained.keys())
    return {
        "registry": reg,
        "status": status,
        "trained_targets": trained_targets,
        "untrained_targets": sorted(
            t for t in DEFAULT_TARGETS if t not in trained_targets
        ),
    }


def model_analytics() -> dict:
    """Return honest model analytics (data/model state, registry, metrics)."""
    module_state = _model_state()
    status = module_state["status"]
    registry = module_state["registry"]
    any_trained = module_state["trained_targets"]
    is_trained = status == STATUS_TRAINED

    # Only expose metrics for targets that are genuinely TRAINED.
    metrics_by_target = {
        t: a.get("metrics") for t, a in registry["artifacts"].items()
        if a.get("status") == STATUS_TRAINED and a.get("metrics")
    }
    datasets = sorted({
        a.get("dataset_name") for a in registry["artifacts"].values()
        if a.get("dataset_name") and a.get("status") == STATUS_TRAINED
    })
    versions = sorted({
        a.get("model_version") for a in registry["artifacts"].values()
        if a.get("model_version") and a.get("status") == STATUS_TRAINED
    })
    ds = dataset_status()

    return {
        "model_name": "thundercast-glm",
        "model_label": (
            "GLM (TRAINED)"
            if is_trained
            else "BASELINE MODEL"
        ),
        "model_version": ", ".join(versions) if versions else "thundercast-baseline-0.1",
        "model_status": status,
        "environment_mode": environment_mode(),
        "data_provenance": current_provenance(),
        "dataset": datasets[0] if datasets else None,
        "targets": module_state["trained_targets"],
        "unavailable_targets": module_state["untrained_targets"],
        "feature_count": len(feature_names()),
        "features": feature_names(),
        "training_samples": sum(
            a.get("n_train") or 0 for a in registry["artifacts"].values()
            if a.get("status") == STATUS_TRAINED
        ),
        "validation_samples": sum(
            a.get("n_validation") or 0 for a in registry["artifacts"].values()
            if a.get("status") == STATUS_TRAINED
        ),
        "test_samples": sum(
            a.get("n_test") or 0 for a in registry["artifacts"].values()
            if a.get("status") == STATUS_TRAINED
        ),
        "metrics": metrics_by_target,
        "architecture": (
            "Trained logistic-regression nowcasting models with chronological "
            "train/validation/test splitting and honest out-of-sample evaluation."
            if is_trained
            else (
                "Rule-based heuristic nowcasting engine with explainable feature "
                "contributions, a prototype impact model and baseline storm-motion "
                "extrapolation. No trained model is active."
            )
        ),
        "evaluation": (
            {
                "status": ds.status,
                "message": ds.message,
                "n_samples": ds.n_samples,
                "available_metrics": ds.available_metrics,
            }
            if not is_trained
            else {
                "status": "ready",
                "message": "Evaluation computed from a real labelled dataset on held-out test splits.",
                "n_samples": sum(
                    a.get("n_test") or 0 for a in registry["artifacts"].values()
                    if a.get("status") == STATUS_TRAINED
                ),
                "available_metrics": ["brier_score", "accuracy", "precision", "recall", "f1", "roc_auc"],
            }
        ),
        "limitations": (
            (
                "No labelled India-specific severe-weather dataset is bundled; "
                "any trained model reflects its documented training-coverage "
                "(reference source is US NCEI). Thunderstorm/hail targets remain "
                "BASELINE unless a genuine labelled dataset is integrated."
                if not is_trained
                else (
                    "Metrics reflect only genuinely-labelled held-out test data. "
                    "Coverage/limitations of the source dataset apply."
                )
            )
        ),
        "feature_surface": _feature_surface(),
    }


def _feature_surface() -> list[dict]:
    return [
        {"name": "temperature_c", "group": "weather", "description": "Surface temperature (C)"},
        {"name": "dew_point_c", "group": "weather", "description": "Surface dew point (C)"},
        {"name": "relative_humidity_percent", "group": "weather", "description": "Relative humidity (%)"},
        {"name": "pressure_hpa", "group": "weather", "description": "Surface pressure (hPa)"},
        {"name": "wind_speed_ms", "group": "weather", "description": "Wind speed (m/s)"},
        {"name": "wind_direction_deg", "group": "weather", "description": "Wind direction (deg)"},
        {"name": "precipitation_mm", "group": "weather", "description": "Accumulated precipitation (mm)"},
        {"name": "precipitation_rate_mmh", "group": "weather", "description": "Precipitation rate (mm/h)"},
        {"name": "cloud_cover_percent", "group": "weather", "description": "Cloud cover (%)"},
        {"name": "cape_jkg", "group": "stability", "description": "Convective available potential energy (J/kg)"},
        {"name": "cin_jkg", "group": "stability", "description": "Convective inhibition (J/kg)"},
        {"name": "lifted_index_c", "group": "stability", "description": "Lifted index (C)"},
        {"name": "wind_shear_ms", "group": "stability", "description": "Vertical wind shear (m/s)"},
        {"name": "dewpoint_depression_c", "group": "stability", "description": "Dewpoint depression (C)"},
        {"name": "max_reflectivity_dbz", "group": "radar", "description": "Max radar reflectivity (dBZ)"},
        {"name": "echo_top_km", "group": "radar", "description": "Radar echo-top height (km)"},
        {"name": "vil_kgm2", "group": "radar", "description": "Vertically integrated liquid (kg/m2)"},
        {"name": "cell_movement_speed_kmh", "group": "radar", "description": "Storm cell speed (km/h)"},
        {"name": "cell_movement_direction_deg", "group": "radar", "description": "Storm cell direction (deg)"},
        {"name": "cloud_top_temperature_k", "group": "satellite", "description": "Satellite cloud-top temp (K)"},
        {"name": "cloud_top_pressure_hpa", "group": "satellite", "description": "Satellite cloud-top pressure (hPa)"},
        {"name": "lightning_density_km2_hr", "group": "lightning", "description": "Lightning density (flashes/km2/hr)"},
    ]


# --- MongoDB persistence (Phase 11) -----------------------------------------

def _persist_nowcast(nowcast: NowcastResult, impacts: ImpactResult, features: ModelFeatures, request_id: str) -> None:
    """Persist a generated nowcast to MongoDB when available.

    Never raises: if the database is unavailable (or the write fails), we log
    and continue serving the in-memory demo response.
    """
    try:
        if not ping_database():
            return
        collection = get_collection("nowcasts")
        if collection is None:
            return
        collection.insert_one(
            {
                "request_id": request_id,
                "latitude": nowcast.latitude,
                "longitude": nowcast.longitude,
                "forecast_time": nowcast.forecast_time.isoformat(),
                "peak_risk": nowcast.peak_risk,
                "peak_hour": nowcast.peak_hour,
                "risk_start_hour": nowcast.risk_start_hour,
                "risk_end_hour": nowcast.risk_end_hour,
                "model_label": nowcast.model_label,
                "model_version": nowcast.model_version,
                "provenance": DATA_PROVENANCE_LABEL,
                "impacts": impacts.as_dict(),
                "points": [
                    {
                        "horizon_hours": p.horizon_hours,
                        "thunderstorm_probability": p.thunderstorm_probability,
                        "hail_probability": p.hail_probability,
                        "cloudburst_probability": p.cloudburst_probability,
                        "overall_risk": p.overall_risk,
                        "confidence": p.confidence,
                    }
                    for p in nowcast.points
                ],
                "created_at": _now().isoformat(),
            }
        )
    except Exception as exc:  # pragma: no cover - defensive persistence
        logger.warning("Failed to persist nowcast to MongoDB: %s", exc)


def persist_storm_tracks() -> None:
    """Persist generated storm-motion predictions when MongoDB is available."""
    try:
        if not ping_database():
            return
        collection = get_collection("storm_tracks")
        if collection is None:
            return
        for prediction in storm_predictions():
            collection.replace_one(
                {"cell_id": prediction.cell_id},
                {
                    "cell_id": prediction.cell_id,
                    "current_latitude": prediction.current_latitude,
                    "current_longitude": prediction.current_longitude,
                    "movement_direction_deg": prediction.movement_direction_deg,
                    "movement_speed_kmh": prediction.movement_speed_kmh,
                    "current_intensity": prediction.current_intensity,
                    "label": prediction.label,
                    "predicted_positions": [
                        {
                            "latitude": p.latitude,
                            "longitude": p.longitude,
                            "valid_time": p.valid_time.isoformat(),
                            "minutes_ahead": p.minutes_ahead,
                            "intensity": p.intensity,
                        }
                        for p in prediction.predicted_positions
                    ],
                    "created_at": _now().isoformat(),
                },
                upsert=True,
            )
    except Exception as exc:  # pragma: no cover - defensive persistence
        logger.warning("Failed to persist storm tracks to MongoDB: %s", exc)
