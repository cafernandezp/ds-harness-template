# configs/models/

Per-model configuration overrides. One YAML file per model, named
`<model_name>.yaml` (e.g. `model_M1.yaml`), matching the argument passed to
`src.lib.config.load_config(model_name)`.

## Rules

- Each key defined here overrides the same top-level key in
  `configs/global.yaml`. Keys not set here are inherited from global.
- `use_mlflow` is project-wide — defined only in `global.yaml`, never here.
- The merge is shallow. If a nested key (e.g. `feature_selection`) is set
  in both files, the model version fully replaces the global one.
- Versioned in git. `configs/local.yaml` is the only gitignored config —
  everything else encodes reviewable project decisions.

## Example (delete after creating the first real model file)

```yaml
# configs/models/model_M1.yaml
primary_metric: mae
secondary_metric: r2
feature_selection:
  method: boruta_shap
  spearman_threshold: 0.7
```
