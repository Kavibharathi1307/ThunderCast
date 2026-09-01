"""Prototype impact-based risk model.

Extends the weather risk system beyond raw probability into human-relevant
impact categories (flooding, roads, agriculture, urban waterlogging, lightning
danger, hail damage, visibility/transport disruption), each scored 0..1.

LABEL: "PROTOTYPE IMPACT MODEL"
These scores are heuristic estimates derived from the baseline risk engine
signals. They are NOT calibrated against real-world impact / damage datasets
and are provided for demonstration and integration purposes only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .features import ModelFeatures
from .predictor import NowcastResult
from .thresholds import IMPACT_THRESHOLDS, IMPACT_MODEL_LABEL, ImpactThresholds

IMPACT_CATEGORIES = (
    "flooding",
    "roads",
    "agriculture",
    "waterlogging",
    "lightning",
    "hail",
    "visibility",
)


@dataclass
class ImpactResult:
    """Structured impact assessment, scores 0..1 each."""

    flooding: float = 0.0
    roads: float = 0.0
    agriculture: float = 0.0
    waterlogging: float = 0.0
    lightning: float = 0.0
    hail: float = 0.0
    visibility: float = 0.0
    label: str = IMPACT_MODEL_LABEL

    def as_dict(self) -> dict[str, float]:
        return {k: round(getattr(self, k), 4) for k in IMPACT_CATEGORIES}


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def assess_impacts(
    features: ModelFeatures,
    nowcast: NowcastResult | None = None,
    thresholds: ImpactThresholds | None = None,
) -> ImpactResult:
    """Compute prototype impact scores from model features (and optional nowcast).

    Hurry-drivers: use the *peak* horizon from the nowcast to weight how
    imminent / severe the hazard is; fall back to raw feature magnitudes.
    """
    t = thresholds or IMPACT_THRESHOLDS
    obs = features.observation
    stab = features.stability
    rad = features.radar
    ltg = features.lightning

    peak = (
        max(
            max(p.thunderstorm_probability, p.hail_probability, p.cloudburst_probability)
            for p in nowcast.points
        )
        if nowcast and nowcast.points
        else 0.0
    )

    # Lightning risk: driven by lightning density + thunderstorm probability.
    lightning = peak * 0.5
    if ltg.lightning_density_km2_hr is not None:
        lightning += _clamp(ltg.lightning_density_km2_hr / t.lightning_danger_density) * 0.5

    # Flooding / urban waterlogging: heavy precipitation on saturated atmosphere.
    flooding = peak * 0.4
    if obs.precipitation_rate_mmh is not None:
        flooding += _clamp(obs.precipitation_rate_mmh / t.flooding_precip_rate_mmh) * 0.6

    waterlogging = peak * 0.3
    if obs.precipitation_rate_mmh is not None:
        waterlogging += _clamp(obs.precipitation_rate_mmh / t.flooding_precip_rate_mmh) * 0.4
    if obs.relative_humidity_percent is not None and obs.relative_humidity_percent >= t.waterlogging_humidity_percent:
        waterlogging += 0.3

    # Hail impact: high reflectivity + thunderstorm probability.
    hail = peak * 0.5
    if rad.max_reflectivity_dbz is not None:
        hail += _clamp(rad.max_reflectivity_dbz / t.hail_reflectivity_dbz) * 0.5

    # Agriculture: a blend of hail, flooding and storm intensity.
    agriculture = _clamp((hail * 0.5) + (flooding * 0.3) + (peak * 0.2))

    # Roads / transport: precipitation + strong shear + heavy rain.
    roads = peak * 0.3
    if obs.precipitation_rate_mmh is not None:
        roads += _clamp(obs.precipitation_rate_mmh / t.flooding_precip_rate_mmh) * 0.4
    if stab.wind_shear_ms is not None:
        roads += _clamp(stab.wind_shear_ms / t.road_shear_ms) * 0.3

    # Visibility: heavy rain / high cloud cover / high precipitation rate.
    visibility = peak * 0.3
    if obs.precipitation_rate_mmh is not None:
        visibility += _clamp(obs.precipitation_rate_mmh / t.flooding_precip_rate_mmh) * 0.5
    if obs.cloud_cover_percent is not None:
        visibility += _clamp(obs.cloud_cover_percent / 100.0) * 0.2

    return ImpactResult(
        flooding=_clamp(flooding),
        roads=_clamp(roads),
        agriculture=_clamp(agriculture),
        waterlogging=_clamp(waterlogging),
        lightning=_clamp(lightning),
        hail=_clamp(hail),
        visibility=_clamp(visibility),
    )
