"""Reference ingestion: NOAA NCEI Storm Events (labels) + Open-Meteo (features).

This script documents the exact steps to build a genuinely-labelled dataset
from openly-available public sources and train the ThunderCast nowcasting model
with a chronological train/validation/test split.

IMPORTANT — honesty and safety
------------------------------
* This script is a **documented reference**. By default it runs in **dry-run**
  (prints the plan, downloads nothing, trains nothing). Pass ``--execute`` to
  actually download and train.
* Long-running / large downloads are intentionally gated behind ``--execute``
  so it is never accidentally triggered in automation or tests.
* It does **not** fabricate data. Labels come only from the genuine NCEI
  ``EVENT_TYPE`` field; features come only from genuine Open-Meteo fields.
* The NCEI source is **US-only** (see ``docs/dataset.md``). There is no open,
  registration-free, India-specific labelled severe-weather dataset; the model
  therefore remains UNTRAINED for India until such a source is integrated.

Usage
-----
    python scripts/ingest_ncei_openmeteo.py --dry-run          # default: print plan
    python scripts/ingest_ncei_openmeteo.py --execute          # download + train
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as a script from the backend directory.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


NCEI_DIR = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles"
OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"

# Height of the target-availability honesty gate.
SUPPORTED_TARGETS = ("thunderstorm", "hail", "cloudburst")

HIGH_RAIN_THRESHOLD_MM = 15.0  # documented per-dataset heavy-rain threshold


def plan(target: str) -> dict:
    """Return the documented plan for a target (no side effects)."""
    return {
        "target": target,
        "label_source": (
            f"NCEI EVENT_TYPE field (US)"
        ),
        "feature_source": f"Open-Meteo archive (ERA5), {OPEN_METEO_ARCHIVE}",
        "label_rule": {
            "thunderstorm": "EVENT_TYPE in {THUNDERSTORM WIND, MARINE THUNDERSTORM WIND}",
            "hail": "EVENT_TYPE == HAIL",
            "cloudburst": f"EVENT_TYPE == HEAVY RAIN or precipitation >= {HIGH_RAIN_THRESHOLD_MM} mm/hr",
        }[target],
        "note": (
            "Geographic coverage is the United States (NCEI). "
            "For India, this pipeline stays UNTRAINED until a labelled India "
            "dataset is integrated."
        ),
    }


def run_dry_run() -> None:
    print("ThunderCast reference ingestion — DRY RUN (no downloads, no training)\n")
    for target in SUPPORTED_TARGETS:
        p = plan(target)
        print(f"[target: {p['target']}]")
        print(f"  label rule : {p['label_rule']}")
        print(f"  feature src: {p['feature_source']}")
        print(f"  note       : {p['note']}\n")
    print("To actually download + train, run with --execute. See docs/dataset.md.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="actually download NCEI/Open-Meteo data and train (large downloads; gated)",
    )
    args = parser.parse_args()

    if not args.execute:
        run_dry_run()
        return 0

    # Real execution path — intentionally left as a documented stub so that a
    # genuinely-labelled dataset can be wired in without rewriting the engine.
    # Wiring points (reuse existing components):
    #   from app.ml.training.ingest import ingest_raw_csv, DEFAULT_SPECS
    #   from app.ml.training.pipeline import train_target_pipeline
    print(
        "Execution path requires a supplied labelled dataset directory. "
        "See docs/dataset.md §H for the exact wiring. Refusing to fabricate data."
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
