# ThunderCast AI — Value for Smart India Hackathon (SIH26084)

ThunderCast AI is architected specifically for **convective-scale nowcasting**
over a **0–6 hour horizon** — the lead time most relevant for community and
authority response to rapid-onset thunderstorm, hail and cloudburst hazards.
This document explains why the architecture is designed the way it is and what
it demonstrates for SIH judges. It makes **no** unsupported claims about
operational meteorological accuracy.

## Why convective nowcasting over 0–6 hours

* Severe convective weather (thunderstorms, hail, cloudbursts) develops and
  dissipates in **minutes to a few hours**. Longer-range numerical forecasts are
  too coarse and too slow to capture the onset that matters for protective
  action.
* A **0–6 hour nowcast horizon** is the practical window in which an alert can
  still be acted on (evacuation, road closure, drainage preparation).
* ThunderCast AI therefore measures **probabilistic** output rather than a single
  deterministic "will it rain" value — giving decision-makers a calibrated
  sense of likelihood.

## Architectural pillars (and the SIH story)

| Pillar | What it does | Why it matters for SIH |
|--------|--------------|------------------------|
| **0–6 hr horizon** | Hour-by-hour probabilities for thunderstorm / hail / cloudburst | Directly actionable nowcasting window |
| **Probabilistic output** | Brier-scored probabilities, not point forecasts | Standard for the nowcasting community; supports risk thresholds |
| **Geospatial predictions** | Per-location (lat/lon) features and risk grids | Coverage for a large, diverse country like India |
| **Storm movement** | Baseline cell extrapolation | Predicts *where* a storm goes, not just that it exists |
| **Impact-based alerts** | Severity + expected impacts + recommended action | Goes beyond "risk level" to "what to do", aligned with IMD impact-based warning practices |
| **Explainability** | Decomposes each prediction into per-feature contributions | Auditability & trust — judges and users can see *why* |
| **Data provenance** | Every response labels DEMO vs REAL DATA and BASELINE vs TRAINED MODEL | Honesty & transparency — a distinguishing, credible trait |
| **Graceful degradation** | REAL → BASELINE → DEMO fallback chain | Resilience when a live provider is unavailable |
| **Modular provider architecture** | Swappable Weather/Radar/Satellite/Lightning providers behind fixed ABCs | Clean path to on-board IMD/NWP/radar data later |
| **Temporal validation** | Chronological train/validation/test splits | Scientifically sound evaluation that avoids look-ahead leakage |

## Data & model honesty (a core SIH strength)

The system explicitly distinguishes three pipeline states and never conflates them:

1. **DEMO** — DEMO DATA → BASELINE MODEL
2. **REAL DATA / UNTRAINED** — REAL DATA → BASELINE MODEL
3. **REAL DATA / TRAINED** — REAL DATA → TRAINED MODEL

This is surfaced in the API and the Methodology page. Judges can see exactly
which pipeline is active at any moment. Crucially, the model refuses to claim
accuracy when no genuine labelled dataset is available (status `UNTRAINED`). A
correct `UNTRAINED` report is more credible than fabricated AI accuracy.

## Real-data realism (honest scope)

* Live REAL observations are fetched from Open-Meteo (a free, no-key ERA5-based
  source) — genuinely real weather data for any location, including India.
* A fully trainable, dependency-free logistic-regression model with
  chronological train/validation/test splitting, Brier/ROC-AUC/precision/
  recall/F1 metrics and calibration inspection is implemented.
* Because **no open, registration-free, India-specific labelled severe-weather
  dataset** is available, the model remains `UNTRAINED` rather than using
  fabricated labels. The ingestion pipeline (documented in `docs/dataset.md`)
  is ready to train the moment a genuine labelled dataset is supplied.

## What this demonstrates to judges

* A production-shaped frontend/backend with **centralised, typed configuration**,
  optional MongoDB persistence, and clean API contracts.
* A **modular ML engine** built on provider abstractions and a fixed feature
  schema — industry-appropriate architecture, not a demo hack.
* **Scientifically honest evaluation**: temporal splits, Brier scoring, baseline
  (climatology) comparison, calibration inspection.
* **Trustworthy transparency**: data provenance + model status everywhere.

This design is a credible foundation for scaling to real India operations by
on-boarding IMD gridded rainfall, IMDAA/ERA5 reanalysis or a future labelled
India thunderstorm dataset through the same provider/adapter seams — without
rewriting the model or UI.
