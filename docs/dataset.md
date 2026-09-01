# ThunderCast AI — Dataset & Training Documentation

> **Honesty statement (mandatory).** This document describes the dataset sources
> selected for the nowcasting training pipeline and exactly how labels are (or
> would be) produced. **As of this phase, no labelled India-specific dataset is
> openly bulk-downloadable without registration, and ThunderCast AI does NOT
> fabricate labels or accuracy. The shipped model therefore remains UNTRAINED.**
> See § A "Current status" below.

---

## A. Current status (must be read first)

| Item | Value |
|------|-------|
| Model status | `UNTRAINED` |
| Bundled labelled dataset | **None** |
| Why | No open, registration-free, India-specific *labelled* thunderstorm/hail dataset exists (see § Researched sources). We do not fabricate labels. |
| Behaviour | App runs on the BASELINE engine; `environment_mode` and `model_status` are surfaced honestly in every response. |

The full *reusable* ingestion → feature → label → temporal split → training →
evaluation pipeline is implemented so that the moment a genuine labelled
dataset is supplied, a real model can be trained without rewriting the engine.

---

## B. Dataset selected (reference pipeline)

Because no open India-specific labelled event dataset exists, the reference
ingestion pipeline targets the **only openly bulk-downloadable labelled
severe-weather source (NOAA NCEI Storm Events, US)**, with **real features from
Open-Meteo / ERA5 (global, incl. India)**. This gives a *genuinely labelled,
trainable* reference, but its geographic coverage is the **United States**, not
India.

> **If a future labelled India dataset becomes available, the same adapter
> interface is reused unchanged** — only the source changes.

### B.1 Labelled source: NOAA NCEI Storm Events Database

| Field | Value |
|-------|-------|
| Name | NCEI Storm Events Database (bulk CSV export) |
| Provider | NOAA National Centers for Environmental Information (NCEI) |
| URL | `https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/` |
| Access landing | `https://www.ncei.noaa.gov/stormevents/` |
| License / access | US Government public-domain data. Free bulk download, **no registration / no API key**. |
| Geographic coverage | **United States only** (NWS severe-weather reporting; bounding box West 172, East −65, South 18, North 72). **India is NOT included.** |
| Temporal coverage | 1950–present (event types vary by start year; thunderstorm wind/hail ~1955+, modern detail from ~1996). |
| Variables (event fields) | `EVENT_TYPE`, `BEGIN_DATE_TIME`, `END_DATE_TIME`, `BEGIN_LAT`, `BEGIN_LON`, `MAGNITUDE`/`MAGNITUDE_TYPE`, `STATE`, plus injury/damage narratives. |
| Real labels available | **Yes** — `EVENT_TYPE` = `THUNDERSTORM WIND`, `HAIL`, `HEAVY RAIN`, `FLASH FLOOD`, `TORNADO`, etc. |
| Timestamp format | `BEGIN_DATE_TIME` / `END_DATE_TIME` = `MM/DD/YYYY hh:mm:ss` (local standard time; `CZ_TIMEZONE` gives offset). Pre-2012 records may use `DD-MON-YYHHMM`. |
| Resolution | Event polygon/location lat-lon with begin/end times; ~county-level precision. |
| Format | Gzipped CSV (`.csv.gz`), one file per year (`StormEvents_details-ftp_v1.0_d{YYYY}_c{CREATEDATE}.csv.gz`). |
| Missing-value handling | Narrative/location fields blank where absent; some years lack MAGNITUDE. |

### B.2 Feature source: Open-Meteo Historical (ERA5) API

| Field | Value |
|-------|-------|
| Name | Open-Meteo Historical Weather API |
| Provider | Open-Meteo (ERA5 reanalysis mirror) |
| URL | `https://archive-api.open-meteo.com/v1/archive` |
| License / access | Free, no API key for non-commercial use. Data CC BY 4.0 (attribution required). Rate limits ~10,000 requests/day. |
| Geographic coverage | **Global 0.25° (~25 km), incl. India.** |
| Temporal coverage | 1940–present (ERA5); updated daily, ~5-day delay. |
| Variables | `temperature_2m`, `dew_point_2m`, `relative_humidity_2m`, `surface_pressure`, `precipitation` (mm per preceding hour), `cloud_cover`, `wind_speed_10m`, `wind_direction_10m`, `wind_gusts_10m`, `weather_code`. |
| Timestamp format | Hourly, ISO8601 `YYYY-MM-DDTHH:MM` (GMT). |
| Caveat | The **archive API does NOT expose historical CAPE / CIN / lifted_index** (those exist only on the forecast API / ERA5-CDS-with-login). Therefore the reference historical feature stack uses T, DP, RH, pressure, precip, cloud, wind — **not** CAPE. Features are limited to those actually present. |

> **Feature honesty:** the pipeline records exactly which features are present
> in a given dataset and never fabricates missing ones (e.g. CAPE is not imputed
> as if it were measured when the archive does not provide it).

---

## C. Sources researched (and why they were not selected)

| Source | Geog. | Labels? | Open bulk DL? | Outcome |
|--------|-------|---------|----------------|---------|
| NOAA NCEI Storm Events | US | **Yes** (storm/hail) | Yes (no key) | Selected as reference labelled source |
| Open-Meteo archive (ERA5) | Global incl. India | No (precip/weather_code only) | Yes (no key) | Selected as feature source |
| IMD 0.25° gridded rainfall | India | No (precip only) | Yes (gridded) | precipitation-only; daily (no sub-daily event timing) |
| IMD DSP station data | India | No | **No** (registration + charges) | Not used |
| IMDAA reanalysis | India | No | **No** (registration/login) | Not used |
| IMD lightning (INSAT-3D) | India | No | **No** (explicitly copyrighted) | Not used |
| ERA5 via Copernicus CDS | Global | No | **No** (login + licence acceptance) | Not used (Open-Meteo mirror used instead) |
| CHIRPS | Global | No (precip only) | Yes (public domain) | Possible precip-only feature alternative |

---

## D. Target-label methodology

Labels are produced **only** from a genuine event/precipitation field present in
the dataset — never from a fabricated inference.

| Target | Label definition (reference NCEI pipeline) | India availability |
|--------|---------------------------------------------|--------------------|
| `thunderstorm` | `EVENT_TYPE` ∈ {`THUNDERSTORM WIND`, `MARINE THUNDERSTORM WIND`} within a temporal/geo bin → 1, else 0 | Unavailable (no open India labels) |
| `hail` | `EVENT_TYPE == "HAIL"` within a temporal/geo bin → 1, else 0 | Unavailable |
| `cloudburst` (heavy rain) | `EVENT_TYPE == "HEAVY RAIN"` or hourly `precipitation >= HIGH_RAIN_THRESHOLD` (documented per-dataset threshold) → 1, else 0 | Precipitation threshold derivable from IMD/ERA5 |

**Rules enforced by the pipeline:**
1. Each target is trained **independently** (`targets` / `unavailable_targets` in metadata).
2. A target is marked **unavailable** (not trained) whenever its label field is absent — never silently dropped or hallucinated.
3. `hail` is **never** inferred from CAPE/temperature alone.

---

## E. Feature engineering

Uses the existing `ModelFeatures` schema (`app/ml/features.py`) and its
deterministic `tabular.extract_features` transformation.

- Only features **actually present** in the dataset are populated; the rest stay `None` (unknown) → imputed at model level, never fabricated as observed.
- Derived features computed when their inputs exist: relative humidity (Magnus), dew-point depression, precipitation intensity, wind-speed components.
- Feature availability is tracked in the training metadata (`features` list).

---

## F. Temporal (leakage-prevention) split

Chronological 3-way split — **no random shuffle before splitting**:

```
EARLIEST ────────────► TRAIN ──► VALIDATION ──► TEST ──► LATEST
```

- Validation = most-recent block; test = latest block; everything earlier = train.
- Documented in `app/ml/training/pipeline.py::temporal_split`.

---

## G. Limitations

1. No open, registration-free, **labelled India** severe-weather dataset — the reference trainable pipeline is US-coverage (NCEI).
2. Open-Meteo archive lacks historical CAPE/CIN/lifted-index, so the reference feature stack omits instability indices unless ERA5-CDS (login) is used.
3. IMD gridded rainfall is daily-resolution — insufficient alone for sub-daily (hourly) nowcast timing.
4. Event labels are county/location-precision; co-locating them to a 0.25° grid may create spatial/temporal mislabelling that must be reported, not hidden.
5. Because no genuine labelled dataset is bundled, **no accuracy metrics are reported.** The model is honestly `UNTRAINED`.

---

## H. Repro / ingestion

A reusable ingestion script (`backend/scripts/ingest_ncei_openmeteo.py`) documents
the exact steps to download NCEI CSVs and Open-Meteo features, co-locate them,
build `LabelledDataset` rows (CSV), and run the temporal train/validation/test
pipeline — for when a genuine labelled source is supplied. It is **not invoked
automatically** and does **not** fabricate data.
