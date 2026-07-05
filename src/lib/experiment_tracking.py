"""
Thin wrapper around experiment logging so that scripts never need to know
whether mlflow or manual `reports/` files are the active backend. The
choice is read once from `use_mlflow` in `configs/global.yaml` (see
src.lib.config) and passed in by the caller — no branching logic is
duplicated across experiment scripts.

Artifact values are saved using the format that matches their type:
- pandas.DataFrame -> .csv (easy to open and inspect as a table)
- dict             -> .json
- anything else    -> assumed to be a trained model; uses its own
                      `.save_model()` method when available (XGBoost,
                      LightGBM, and others expose this), falling back to
                      joblib otherwise. No ML library is hardcoded or
                      required as a dependency here — this trades away
                      mlflow's model-specific flavors (which capture a
                      signature and integrate with the Model Registry)
                      in favor of staying generic and simple.

Scope: this module is only for small, disposable artifacts tied to a
single experimental run (e.g. a boruta-shap summary for one trial). Any
dataset meant to be read later by another script — predictions, a
preprocessed training matrix, anything reusable — does not belong here.
Save it as parquet under `src.lib.paths.model_data_dir(model_name)` instead.

Requires: mlflow, pandas, joblib (pip install mlflow pandas joblib)
"""

import json
from pathlib import Path
from typing import Any

import joblib
import mlflow
import pandas as pd


def log_run(
    model_name: str,
    run_name: str,
    params: dict[str, Any],
    metrics: dict[str, float],
    artifacts: dict[str, Any] | None = None,
    use_mlflow: bool = True,
) -> None:
    """
    Log one experiment run, backend chosen by `use_mlflow`.

    Args:
        model_name: e.g. "model_M1" — used to locate the tracking store
            or the manual output folder.
        run_name: Descriptive identifier for this run
            (e.g. "boruta_shap_phase2", "xgboost_trial_1").
        params: Hyperparameters / settings used in this run.
        metrics: Evaluation metrics produced by this run.
        artifacts: Named objects to persist alongside the run. Format is
            inferred from each object's type (see module docstring).
        use_mlflow: Typically `config.use_mlflow` from src.lib.config.
    """
    artifacts = artifacts or {}

    if use_mlflow:
        _log_with_mlflow(model_name, run_name, params, metrics, artifacts)
    else:
        _log_manually(model_name, run_name, params, metrics, artifacts)


def _save_artifact(directory: Path, name: str, obj: Any) -> Path:
    """Save one artifact to `directory`, format chosen by its type."""
    if isinstance(obj, pd.DataFrame):
        path = directory / f"{name}.csv"
        obj.to_csv(path, index=False)
    elif isinstance(obj, dict):
        path = directory / f"{name}.json"
        path.write_text(json.dumps(obj, indent=2))
    elif hasattr(obj, "save_model"):
        path = directory / f"{name}.json"
        obj.save_model(str(path))
    else:
        path = directory / f"{name}.joblib"
        joblib.dump(obj, path)
    return path


def _log_with_mlflow(
    model_name: str,
    run_name: str,
    params: dict[str, Any],
    metrics: dict[str, float],
    artifacts: dict[str, Any],
) -> None:
    mlflow.set_tracking_uri(f"file:./reports/models/{model_name}/mlruns")
    mlflow.set_experiment(model_name)

    with mlflow.start_run(run_name=run_name):
        for key, value in params.items():
            mlflow.log_param(key, value)
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
        for name, obj in artifacts.items():
            tmp_path = _save_artifact(Path("."), name, obj)
            mlflow.log_artifact(str(tmp_path))


def _log_manually(
    model_name: str,
    run_name: str,
    params: dict[str, Any],
    metrics: dict[str, float],
    artifacts: dict[str, Any],
) -> None:
    run_dir = Path(f"reports/models/{model_name}/manual_runs/{run_name}")
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "params.json").write_text(json.dumps(params, indent=2))
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    for name, obj in artifacts.items():
        _save_artifact(run_dir, name, obj)
