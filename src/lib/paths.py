"""
Centralized path constants for the project's data pipeline.

Any script reading or writing data should import the relevant path from
here instead of hardcoding a string. If a folder is ever renamed, this is
the only file that needs to change.

Scope note: these paths are for data meant to be read by other pipeline
stages (data/) or for per-model diagnostics (reports/). One-off artifacts
tied to a single experimental run belong in src.lib.experiment_tracking
instead — see that module's docstring for the distinction.
"""

from pathlib import Path

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"

ETL_DIR = DATA_DIR / "etl"
ETL_PERIMETER_DIR = ETL_DIR / "perimeter"
ETL_FEATURES_DIR = ETL_DIR / "features"
ETL_TARGET_DIR = ETL_DIR / "target"
ETL_TRAIN_TEST_DIR = ETL_DIR / "train_test"

REPORTS_DIR = Path("reports")


def model_data_dir(model_name: str) -> Path:
    """
    Model-specific processed data directory, e.g. data/models/model_M1/.

    Use this for any dataset produced by a model's pipeline that another
    script may need to read later (e.g. predictions, a preprocessed
    training matrix) — not for one-off experiment diagnostics.
    """
    return DATA_DIR / "models" / model_name


def model_reports_dir(model_name: str) -> Path:
    """Diagnostics/reports directory for a given model, e.g. reports/models/model_M1/."""
    return REPORTS_DIR / "models" / model_name
