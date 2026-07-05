"""
Thin wrapper around experiment logging so that scripts never need to know
whether mlflow or manual `reports/` files are the active backend. The
choice is read once from `use_mlflow` in `configs/global.yaml` (see
src.lib.config) and passed in by the caller — no branching logic is
duplicated across experiment scripts.

Artifact values are saved using the format that matches their type:
- pandas.DataFrame -> .csv (easy to open and inspect as a table)
- dict             -> .json
- XGBoost model    -> mlflow's native flavor (mlflow.xgboost.log_model)
                      when use_mlflow=True, since that captures the model
                      signature/environment and plugs into the Model
                      Registry — using src.lib.model_io here instead would
                      throw that metadata away for no benefit
- any other object  -> assumed to be a model, handled by src.lib.model_io
                      (used for XGBoost too, but only in manual mode,
                      where no mlflow flavor is available)

Scope: this module is only for small, disposable artifacts tied to a
single experimental run (e.g. a boruta-shap summary for one trial). Any
dataset meant to be read later by another script — predictions, a
preprocessed training matrix, anything reusable — does not belong here.
Save it as parquet under `src.lib.paths.model_data_dir(model_name)` instead.

Requires: mlflow, pandas, xgboost (pip install mlflow pandas xgboost)
"""

from pathlib import Path
from typing import Any
import json

import mlflow
import mlflow.xgboost
import pandas as pd
import xgboost as xgb

from src.lib.model_io import save_model


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
            if isinstance(obj, pd.DataFrame):
                tmp_path = Path(f"{name}.csv")
                obj.to_csv(tmp_path, index=False)
                mlflow.log_artifact(str(tmp_path))
            elif isinstance(obj, dict):
                tmp_path = Path(f"{name}.json")
                tmp_path.write_text(json.dumps(obj, indent=2))
                mlflow.log_artifact(str(tmp_path))
            elif isinstance(obj, (xgb.XGBModel, xgb.Booster)):
                # Use mlflow's own XGBoost flavor rather than a generic
                # artifact: it captures the model signature and
                # environment, and plugs into the MLflow Model Registry
                # if that's ever needed. Duplicating this via model_io
                # would throw that metadata away for no benefit.
                mlflow.xgboost.log_model(obj, artifact_path=name)
            else:
                # No dedicated mlflow flavor assumed for this type —
                # fall back to src.lib.model_io, same as manual mode.
                tmp_path = save_model(obj, Path(name))
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
        if isinstance(obj, pd.DataFrame):
            obj.to_csv(run_dir / f"{name}.csv", index=False)
        elif isinstance(obj, dict):
            (run_dir / f"{name}.json").write_text(json.dumps(obj, indent=2))
        else:
            save_model(obj, run_dir / name)
