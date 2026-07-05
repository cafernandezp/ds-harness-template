"""
Model persistence helpers.

Picks the serialization method that best fits each model type, instead of
defaulting to pickle everywhere. Pickle is fragile across library/Python
version changes — exactly the "can't load it later" problem this module
exists to avoid.

- XGBoost models: native save_model()/load_model() with a `.json` file,
  which XGBoost guarantees to load correctly across its own version
  upgrades (unlike a pickled object).
- Any other model type: joblib, the standard choice in the sklearn
  ecosystem for arbitrary Python model objects.

Requires: xgboost, joblib (pip install xgboost joblib)
"""

from pathlib import Path
from typing import Any

import joblib
import xgboost as xgb


def save_model(model: Any, path: Path) -> Path:
    """
    Save a model, choosing the format based on its type.

    Args:
        model: A fitted model object (XGBoost or any other type).
        path: Destination path. The extension is set automatically based
            on the model type, so pass a path without extension
            (e.g. `reports/models/model_M1/manual_runs/run_1/model`).

    Returns:
        The actual path written, including the extension that was chosen.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(model, (xgb.XGBModel, xgb.Booster)):
        final_path = path.with_suffix(".json")
        model.save_model(str(final_path))
    else:
        final_path = path.with_suffix(".joblib")
        joblib.dump(model, final_path)

    return final_path


def load_model(path: Path, model_class: type | None = None) -> Any:
    """
    Load a model saved with `save_model`.

    Args:
        path: Path to the saved model file (`.json` or `.joblib`).
        model_class: Required only for `.json` (XGBoost) files — the
            sklearn-style wrapper class used originally, e.g.
            `xgboost.XGBRegressor`, so the object can be reconstructed
            before calling `load_model` on it.

    Returns:
        The reconstructed model object, ready to call `.predict()` on.

    Raises:
        ValueError: if loading a `.json` file without providing `model_class`.
    """
    path = Path(path)

    if path.suffix == ".json":
        if model_class is None:
            raise ValueError(
                "model_class is required to load an XGBoost .json model "
                "(e.g. model_class=xgboost.XGBRegressor)"
            )
        model = model_class()
        model.load_model(str(path))
        return model

    return joblib.load(path)
