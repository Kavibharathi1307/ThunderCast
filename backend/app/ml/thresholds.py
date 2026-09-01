"""Configurable thresholds and constants for the intelligence layer.

Centralises the rule thresholds used by the nowcasting / risk / impact engines
so that no magic numbers are scattered through the code. These are *prototype
heuristic* thresholds, NOT scientifically validated operational values. They
are grouped and overridable so a real model / calibration can replace them.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConvectiveThresholds:
    """Thresholds for the baseline rules engine."""

    # Thermodynamic / moisture
    high_humidity_percent: float = 70.0
    extreme_humidity_percent: float = 85.0
    warm_temperature_c: float = 28.0
    hot_temperature_c: float = 34.0
    low_pressure_hpa: float = 1008.0

    # Instability
    high_cape_jkg: float = 1500.0
    unstable_lifted_index_c: float = -3.0
    strong_shear_ms: float = 15.0

    # Precipitation / radar
    heavy_precipitation_mmh: float = 15.0
    extreme_precipitation_mmh: float = 30.0
    high_reflectivity_dbz: float = 45.0
    high_echo_top_km: float = 10.0

    # Engine input weights (baseline, explainable)
    weight_humidity: float = 0.25
    weight_temperature: float = 0.20
    weight_pressure: float = 0.15
    weight_cape: float = 0.22
    weight_lifted_index: float = 0.15
    weight_shear: float = 0.10
    weight_precip_rate: float = 0.18
    weight_reflectivity: float = 0.15
    weight_echo_top: float = 0.10
    weight_lightning: float = 0.12

    # Risk classification
    extreme_peak: float = 0.80
    high_peak: float = 0.60
    moderate_peak: float = 0.40

    # Confidence
    confidence_base: float = 0.60
    confidence_feature_bonus: float = 0.05


@dataclass
class ImpactThresholds:
    """Thresholds for the prototype impact model."""

    lightning_danger_density: float = 2.0  # flashes / km^2 / hr
    flooding_precip_rate_mmh: float = 25.0
    waterlogging_humidity_percent: float = 80.0
    hail_reflectivity_dbz: float = 55.0
    road_shear_ms: float = 20.0


# Recommended thresholds for the baseline engine.
BASELINE_THRESHOLDS: ConvectiveThresholds = ConvectiveThresholds()

# Impact thresholds.
IMPACT_THRESHOLDS: ImpactThresholds = ImpactThresholds()

# Label used on all baseline-engine outputs (never claim a trained model).
BASELINE_MODEL_LABEL = "BASELINE MODEL"
BASELINE_MODEL_VERSION = "thundercast-baseline-0.1"
IMPACT_MODEL_LABEL = "PROTOTYPE IMPACT MODEL"
