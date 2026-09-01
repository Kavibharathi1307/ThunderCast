"""Labelled dataset loading for the trainable nowcasting model.

Supplies real, chronologically-ordered labelled samples. The MVP ships with
**no** bundled labelled dataset, so the loader returns an empty/``None`` result
until a labelled source is provided (e.g. a Mongo ``historical_events``
collection with feature rows + labels, or a CSV file).

Honesty
-------
This module never fabricates labels or samples. If no labelled data exists it
honestly reports that a dataset is required, which keeps the model from being
presented as trained.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator

from ..features import ModelFeatures, WeatherObservationFeatures, StabilityFeatures


class LabelledRow:
    """One labelled sample: feature row + binary label + timestamp + target."""

    __slots__ = ("features", "label", "timestamp", "target")

    def __init__(self, features: ModelFeatures, label: int, timestamp: datetime, target: str = "thunderstorm"):
        self.features = features
        self.label = int(label)
        self.timestamp = timestamp
        self.target = target


@dataclass
class LabelledDataset:
    """A chronologically-ordered set of labelled samples for one target."""

    rows: list[LabelledRow] = None  # type: ignore[assignment]
    target: str = "thunderstorm"

    def __post_init__(self) -> None:
        if self.rows is None:
            self.rows = []
        self.rows.sort(key=lambda r: r.timestamp)
        if self.rows:
            self.target = self.rows[0].target

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self) -> Iterator[LabelledRow]:
        return iter(self.rows)

    @property
    def n_positive(self) -> int:
        return sum(1 for r in self.rows if r.label == 1)

    @property
    def n_negative(self) -> int:
        return sum(1 for r in self.rows if r.label == 0)


def empty_dataset() -> LabelledDataset:
    """Return an empty dataset (the honest default when no data is supplied)."""
    return LabelledDataset([])


def load_csv(path: str | Path, target: str = "thunderstorm") -> LabelledDataset:
    """Load a labelled dataset from a CSV file.

    Expected columns: the tabular feature names, plus ``label`` (0/1) and an
    optional ``timestamp`` (ISO) used for chronological splitting. If no
    ``timestamp`` column is present, rows are ordered by file order.
    """
    rows: list[LabelledRow] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if "label" not in (reader.fieldnames or []):
            raise ValueError("CSV dataset must contain a 'label' column")
        for index, record in enumerate(reader):
            features = _features_from_row(record)
            label = int(record["label"])
            ts = _parse_timestamp(record.get("timestamp"), index)
            rows.append(LabelledRow(features, label, ts, target=target))
    return LabelledDataset(rows, target=target)


def _features_from_row(record: dict) -> ModelFeatures:
    def num(key: str) -> float | None:
        raw = (record.get(key) or "").strip()
        if raw == "":
            return None
        return float(raw)

    obs = WeatherObservationFeatures(
        temperature_c=num("temperature_c"),
        dew_point_c=num("dew_point_c"),
        relative_humidity_percent=num("relative_humidity_percent"),
        pressure_hpa=num("pressure_hpa"),
        wind_speed_ms=num("wind_speed_ms"),
        precipitation_rate_mmh=num("precipitation_rate_mmh"),
        cloud_cover_percent=num("cloud_cover_percent"),
    )
    stab = StabilityFeatures(
        cape_jkg=num("cape_jkg"),
        cin_jkg=num("cin_jkg"),
        lifted_index_c=num("lifted_index_c"),
        wind_shear_ms=num("wind_shear_ms"),
        dewpoint_depression_c=num("dewpoint_depression_c"),
    )
    return ModelFeatures(
        latitude=num("latitude") or 0.0,
        longitude=num("longitude") or 0.0,
        observation=obs,
        stability=stab,
    )


def _parse_timestamp(raw: str | None, index: int) -> datetime:
    if raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    # No timestamp -> synthetic monotonically increasing time to preserve order.
    return datetime.fromtimestamp(1_700_000_000 + index)
