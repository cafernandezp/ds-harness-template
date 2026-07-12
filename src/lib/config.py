"""
Typed configuration loader for model-specific settings.

Merges project-wide defaults (`configs/global.yaml`) with model-specific
overrides (`configs/models/<model_name>.yaml`) into a typed `ModelConfig`
object, so the rest of the codebase never touches a raw dictionary.

Requires: pyyaml (pip install pyyaml)

Example
-------
    from src.lib.config import load_config

    config = load_config("model_M1")
    threshold = config.feature_selection.spearman_threshold
"""

from dataclasses import dataclass, field
from typing import Any
import yaml

from src.lib.paths import CONFIGS_DIR


@dataclass
class ModelConfig:
    """
    Fully merged configuration for a single model (global defaults + model-specific overrides).

    `feature_selection` is intentionally a plain dict, not a typed dataclass:
    the exact feature-selection technique and its parameters have not been
    decided yet. Once that choice is final, promote it into its own typed
    dataclass here and update `load_config` accordingly. Every other field
    below reflects something already confirmed (fixed `random_state` in
    Standards; primary/secondary metric and `use_mlflow` in CONVENTIONS.md).

    `use_mlflow` is a project-wide switch, defined only in `global.yaml`.
    Model-specific YAML files are not expected to override it — it is the
    same for every model in the project.
    """
    random_state: int
    primary_metric: str
    secondary_metric: str
    use_mlflow: bool
    feature_selection: dict[str, Any] = field(default_factory=dict)


def load_config(model_name: str) -> ModelConfig:
    """
    Load and merge configuration for a given model.

    Reads `configs/global.yaml` first, then `configs/models/<model_name>.yaml`.
    Any top-level key defined in the model-specific file overrides the same
    key in the global file; keys not overridden are inherited from global.

    Note: the merge is shallow (top-level keys only). If a nested key like
    `feature_selection` exists in both files, the model's version fully
    replaces the global one rather than merging field by field. Today only
    model configs define `feature_selection`, so this is not an issue yet —
    but keep it in mind if global-level nested defaults are added later.

    Args:
        model_name: Identifier of the model, matching the filename under
            configs/models/ without the .yaml extension (e.g. "model_M1").

    Returns:
        A typed ModelConfig with the merged values.

    Raises:
        FileNotFoundError: if either the global or the model config file
            is missing.
    """
    global_path = CONFIGS_DIR / "global.yaml"
    model_path = CONFIGS_DIR / "models" / f"{model_name}.yaml"

    with open(global_path, "r") as f:
        global_cfg = yaml.safe_load(f)

    with open(model_path, "r") as f:
        model_cfg = yaml.safe_load(f)

    merged = {**global_cfg, **model_cfg}

    return ModelConfig(
        random_state=merged["random_state"],
        primary_metric=merged["primary_metric"],
        secondary_metric=merged["secondary_metric"],
        use_mlflow=merged["use_mlflow"],
        feature_selection=merged.get("feature_selection", {}),
    )


if __name__ == "__main__":
    # Minimal usage example.
    # Requires configs/global.yaml and configs/models/model_M1.yaml to exist.
    config = load_config("model_M1")
    print(config)
