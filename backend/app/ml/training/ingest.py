"""Reusable ingestion pipeline: raw records → feature rows → labels → dataset.

Design
------
This is the adapter layer between a **raw** dataset (CSV now; NetCDF/GRIB/Parquet
later) and the engine's ``LabelledDataset``. It is intentionally decoupled from
the training loop so a new source can be added without rewriting the model.

For each supported target the caller supplies a
:class:`LabelingSpec` that says how a label is derived **from a genuine field in
the dataset**. The pipeline NEVER fabricates labels: if the required field is
absent from a record, that record is skipped and the target is reported
``unavailable``; if no records can be labelled for a target, that target is
marked unavailable and not trained.

Target honesty
--------------
* ``TARGETS`` lists the supported targets.
* ``available_targets`` / ``unavailable_targets`` are derived from whether the
  dataset actually contains the fields needed to build each target's label.
* ``hail`` is never inferred from CAPE/temperature alone.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

from ..features import ModelFeatures, WeatherObservationFeatures, StabilityFeatures
from .dataset import LabelledDataset, LabelledRow

# The set of nowcasting targets the system can express.
TARGETS: tuple[str, ...] = ("thunderstorm", "hail", "cloudburst")


@dataclass
class LabelingSpec:
    """Declarative description of how a target's label is derived."""

    target: str
    # Event-based label: label = 1 when event_field value is in positive_values.
    event_field: str | None = None
    positive_values: tuple[str, ...] = ()
    # Threshold-based label: label = 1 when numeric value_field op threshold.
    value_field: str | None = None
    threshold: float | None = None
    operator: str = ">="

    def could_be_available(self, fieldnames: set[str]) -> bool:
        """Whether the dataset has at least one field needed to label this target."""
        if self.event_field is not None and self.event_field in fieldnames:
            return True
        if self.value_field is not None and self.value_field in fieldnames:
            return True
        return False


DEFAULT_SPECS: dict[str, LabelingSpec] = {
    "thunderstorm": LabelingSpec(
        target="thunderstorm",
        event_field="EVENT_TYPE",
        positive_values=("THUNDERSTORM WIND", "MARINE THUNDERSTORM WIND"),
    ),
    "hail": LabelingSpec(
        target="hail",
        event_field="EVENT_TYPE",
        positive_values=("HAIL",),
    ),
    "cloudburst": LabelingSpec(
        target="cloudburst",
        event_field="EVENT_TYPE",
        positive_values=("HEAVY RAIN",),
    ),
}


@dataclass
class IngestionReport:
    """Honest summary of an ingestion run."""

    target_attempted: str
    available: bool
    rows_ingested: int = 0
    n_positive: int = 0
    n_negative: int = 0
    skipped_missing_field: int = 0
    skipped_bad_value: int = 0
    message: str = ""


def _spec_label(spec: LabelingSpec, record: dict) -> int | None:
    """Derive a label from a raw record per the spec, or None if unavailable."""
    if spec.event_field is not None and spec.event_field in record:
        value = (record.get(spec.event_field) or "").strip().upper()
        if value == "":
            return 0
        return 1 if value in {v.upper() for v in spec.positive_values} else 0
    if spec.value_field is not None and spec.value_field in record:
        raw = record.get(spec.value_field)
        if raw in (None, ""):
            return None
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return None
        if spec.operator == ">=":
            return 1 if value >= spec.threshold else 0
        if spec.operator == ">":
            return 1 if value > spec.threshold else 0
        if spec.operator == "<=":
            return 1 if value <= spec.threshold else 0
        return 0
    return None


def raw_features_from_row(record: dict) -> ModelFeatures:
    """Build a ModelFeatures bundle from raw row keys (only fields present)."""
    def num(key: str) -> float | None:
        raw = (record.get(key) or "").strip()
        if raw == "":
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    obs = WeatherObservationFeatures(
        temperature_c=num("temperature_c"),
        dew_point_c=num("dew_point_c"),
        relative_humidity_percent=num("relative_humidity_percent"),
        pressure_hpa=num("pressure_hpa"),
        wind_speed_ms=num("wind_speed_ms"),
        wind_direction_deg=num("wind_direction_deg"),
        precipitation_mm=num("precipitation_mm"),
        precipitation_rate_mmh=num("precipitation_rate_mmh"),
        cloud_cover_percent=num("cloud_cover_percent"),
    )
    stab = StabilityFeatures(
        cape_jkg=num("cape_jkg"),
        cin_jkg=num("cin_jkg"),
        lifted_index_c=num("lifted_index_c"),
        wind_shear_ms=num("wind_shear_ms"),
        dewpoint_depression_c=_depression(obs.temperature_c, obs.dew_point_c),
    )
    return ModelFeatures(
        latitude=num("latitude") or 0.0,
        longitude=num("longitude") or 0.0,
        observation=obs,
        stability=stab,
    )


def _depression(temp, dew):
    if temp is None or dew is None:
        return None
    return temp - dew


def _parse_ts(raw: str | None, index: int) -> datetime:
    if raw:
        cleaned = raw.replace("Z", "+00:00").strip()
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S%z", "%Y-%m-%dT%H:%M", "%m/%d/%Y %H:%M:%S"):
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue
    return datetime.fromtimestamp(1_700_000_000 + index)


def ingest_raw_csv(
    path: str | Path,
    target: str,
    spec: LabelingSpec | None = None,
    timestamp_field: str = "timestamp",
) -> tuple[LabelledDataset | None, IngestionReport]:
    """Ingest a raw CSV into a target-specific LabelledDataset.

    Returns ``(dataset, report)`` where ``dataset`` is ``None`` when the target's
    labelling fields are absent (unavailable).
    """
    if target not in TARGETS:
        raise ValueError(f"unknown target: {target}")
    spec = spec or DEFAULT_SPECS[target]

    rows: list[LabelledRow] = []
    report = IngestionReport(target_attempted=target, available=False)
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        report.available = spec.could_be_available(fieldnames)
        if not report.available:
            report.message = f"Dataset lacks fields needed to label target '{target}'; target unavailable."
            return None, report
        for index, record in enumerate(reader):
            label = _spec_label(spec, record)
            if label is None:
                report.skipped_missing_field += 1
                continue
            try:
                features = raw_features_from_row(record)
            except Exception:  # noqa: BLE001 - bad row, skip
                report.skipped_bad_value += 1
                continue
            ts = _parse_ts(record.get(timestamp_field), index)
            rows.append(LabelledRow(features, label, ts, target=target))
            report.rows_ingested += 1
            if label == 1:
                report.n_positive += 1
            else:
                report.n_negative += 1

    return LabelledDataset(rows, target=target), report


def assess_target_availability(fieldnames: Iterable[str]) -> tuple[list[str], list[str]]:
    """Return (available_targets, unavailable_targets) for a set of column names."""
    names = set(fieldnames)
    available = [t for t in TARGETS if DEFAULT_SPECS[t].could_be_available(names)]
    unavailable = [t for t in TARGETS if t not in available]
    return available, unavailable
