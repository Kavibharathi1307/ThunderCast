"""Unit tests for baseline storm-motion extrapolation."""

from datetime import datetime, timedelta

import pytest

from app.ml.storm_motion import (
    predict_storm_cell,
    LOOKAHEAD_MINUTES,
    StormPrediction,
    BASELINE_LABEL,
)


def test_lookahead_minutes_are_30_60_90_120():
    assert LOOKAHEAD_MINUTES == (30, 60, 90, 120)


def test_prediction_contains_all_lookahead_times():
    pred = predict_storm_cell(
        cell_id="CB-1",
        latitude=21.25,
        longitude=78.5,
        movement_direction_deg=90.0,
        movement_speed_kmh=30.0,
        current_intensity=0.7,
    )
    assert isinstance(pred, StormPrediction)
    assert pred.label == BASELINE_LABEL
    assert [p.minutes_ahead for p in pred.predicted_positions] == [30, 60, 90, 120]
    assert pred.cell_id == "CB-1"
    assert pred.movement_speed_kmh == 30.0
    assert pred.movement_direction_deg == 90.0


def test_position_moves_toward_direction():
    # Moving due north (0 deg) -> latitude increases, longitude ~ unchanged
    pred = predict_storm_cell(
        cell_id="CB-1",
        latitude=20.0,
        longitude=78.0,
        movement_direction_deg=0.0,
        movement_speed_kmh=60.0,
        current_intensity=0.7,
    )
    positions = pred.predicted_positions
    final = positions[-1]
    assert final.latitude > 20.0
    assert abs(final.longitude - 78.0) < 0.05


def test_further_lookahead_moves_further():
    pred = predict_storm_cell(
        cell_id="CB-1",
        latitude=20.0,
        longitude=78.0,
        movement_direction_deg=0.0,
        movement_speed_kmh=60.0,
        current_intensity=0.7,
    )
    positions = pred.predicted_positions
    assert positions[3].latitude > positions[0].latitude


def test_valid_times_advance_by_minutes():
    base = datetime(2026, 1, 1, 0, 0, 0)
    pred = predict_storm_cell(
        cell_id="CB-1",
        latitude=20.0,
        longitude=78.0,
        movement_direction_deg=90.0,
        movement_speed_kmh=30.0,
        current_intensity=0.7,
        base_time=base,
    )
    for p in pred.predicted_positions:
        assert p.valid_time == base + timedelta(minutes=p.minutes_ahead)


def test_intensity_bounded_and_weakened_over_time():
    pred = predict_storm_cell(
        cell_id="CB-1",
        latitude=20.0,
        longitude=78.0,
        movement_direction_deg=90.0,
        movement_speed_kmh=30.0,
        current_intensity=1.0,
    )
    positions = pred.predicted_positions
    for p in positions:
        assert 0.0 <= p.intensity <= 1.0
    assert positions[-1].intensity <= positions[0].intensity


def test_high_speed_travels_greater_distance():
    slow = predict_storm_cell(cell_id="A", latitude=20.0, longitude=78.0, movement_direction_deg=0.0, movement_speed_kmh=10.0, current_intensity=0.5)
    fast = predict_storm_cell(cell_id="B", latitude=20.0, longitude=78.0, movement_direction_deg=0.0, movement_speed_kmh=90.0, current_intensity=0.5)
    slow_dist = slow.predicted_positions[-1].latitude - 20.0
    fast_dist = fast.predicted_positions[-1].latitude - 20.0
    assert fast_dist > slow_dist


def test_zero_speed_means_no_movement():
    pred = predict_storm_cell(cell_id="A", latitude=20.0, longitude=78.0, movement_direction_deg=90.0, movement_speed_kmh=0.0, current_intensity=0.5)
    for p in pred.predicted_positions:
        assert p.latitude == pytest.approx(20.0)
        assert p.longitude == pytest.approx(78.0)
