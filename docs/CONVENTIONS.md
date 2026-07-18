# CONVENTIONS.md

> Consulted by IMPLEMENTER and REVIEWER before writing or reviewing any code.
> Static reference — update only when a convention changes project-wide.

## 1. Naming
- Variables: `X_train`, `y_train`, `X_val`, `y_val`, `X_test`, `y_test`.
- Functions: verb_noun (`compute_mae`, `filter_by_variance`).
- Library modules and stage-specific scripts must never share a filename
  (e.g. a shared `metrics.py` in `src/lib/` vs. a model-specific `evals.py`
  in `final_model/` — different names prevent trace ambiguity).

## 2. Code style
- Functional over OOP.
- Type hints required on every function signature.
- Docstrings required (purpose, args, returns).
- Never use sklearn `Pipeline` or `ColumnTransformer`. Preprocessing steps
  are written as explicit, separate function calls instead — this keeps
  every transformation visible and inspectable, rather than hidden behind
  a Pipeline's fit/transform abstraction.

## 3. Imports
- No wildcard imports.
- Absolute imports from the `src` package (`from src.lib.metrics import compute_mae`).
- No `sys.path` manipulation.

## 4. File formats
- Parquet for tabular data meant to be read by other code downstream
  (anything under `data/`).
- CSV is acceptable for small, human-inspectable diagnostic tables tied
  to a single experiment run (via `src.lib.experiment_tracking.log_run`).
- Trained models: never pickle directly. Prefer the model's own
  `.save_model()` method when available (XGBoost, LightGBM, etc.),
  falling back to `joblib` otherwise — see section 14.

## 5. Metrics
- Primary metric: <TBD per project>
- Secondary metric: <TBD per project>

## 6. `lib/` vs. orchestration — placement rule
- If a module is reused by more than one model OR more than one type of
  pipeline stage → `src/lib/`.
- If a module is specific to one script of one stage of one model →
  it stays nested inside that script's folder, even though it is also
  written as a function (functional style applies repo-wide, it is not
  the placement criterion).

## 7. Reports & artifacts policy
- `reports/` is fully gitignored, no per-file exceptions.
- Any fitted artifact that downstream code must reproduce exactly — not
  regenerate — lives in `src/`, version-controlled, as a `.py` module
  (never a notebook or a CSV). Examples: a selected feature list, a
  categorical encoding map fit on train. These are contracts, not
  regenerable diagnostics, so they never go in `reports/` or `data/`.

## 8. Function signatures
General guideline, not a hard limit: prefer keyword-only arguments and
fewer than 4 parameters for pure `lib/` functions (e.g. `src.lib.metrics`,
`src.lib.feature_selection`). Orchestration/logging functions that
legitimately bundle several related values (e.g.
`src.lib.experiment_tracking.log_run`) are exempt from this — see
`skills/function-conventions/` for the full rubric and worked examples.

## 9. Reproducibility
- Fixed `random_state` across all splits, models, and stochastic steps.
- All transformers fit on train only; never fit on val/test.

## 10. Paths
- No absolute paths anywhere in `src/`.
- No path to `data/` or `reports/` is ever written by hand as a string in
  a script — import the location from `src.lib.paths` instead. If a
  location isn't defined there yet, add it when the need arises, rather
  than anticipating every possible path upfront.
- `src` imports resolve identically regardless of execution location
  because the repo is installed as a package via `uv sync` — see
  section 16 (Packaging).

## 11. Owner-only spaces (`*/analysis/` and `playground/`)
Two kinds of folder are reserved for the project owner's personal, manual
work and are invisible to every agent (LEAD, IMPLEMENTER, REVIEWER, ADVISOR)
by default:
- any folder named `analysis` anywhere under `src/` (typically scratch
  notebooks, tied to a specific pipeline stage);
- the top-level `playground/` — free-form scratch, temporary code, and notes
  outside the pipeline entirely.

Both:
- are not part of the reviewed pipeline;
- must never be written to, read from, or depended upon by any agent, unless
  the project owner explicitly says otherwise for a specific case;
- `analysis/` folders are versioned in git like the rest of `src/` — no
  special gitignore treatment.

Since agents never read these folders by default, any durable conclusion
from this exploration (a decision, a finding worth keeping) must be
formalized separately — an ADR in `docs/adr/` or a write-up in
`docs/research-reports/` — rather than left only inside a notebook.

## 12. Config loading
Model-specific config values override `global.yaml` when both define the
same key. Any key not overridden by the model is inherited from
`global.yaml`. `use_mlflow` is project-wide and defined only in
`global.yaml` — model-specific files are not expected to override it.
Only `configs/local.yaml` is gitignored; the rest of `configs/` is
versioned, since it represents reviewable project decisions, not
machine-specific or regenerable data.

## 13. Testing
Tests are not required during model development (`etl/`, `models/`
experiments/final_model). This phase is exploratory and code changes
fast — the cost of maintaining tests outweighs the benefit here.

Testing becomes mandatory once code enters the inference/production phase:
any script under `src/inference/`, plus any `src/lib/` function that
`inference/` code actually imports, must have a corresponding test in
`tests/`, mirroring the same relative path.

## 14. Model persistence
- Never use pickle directly to save a model — it is fragile across
  library/Python version changes and can silently fail to load after an
  upgrade.
- Prefer a model's own `.save_model()` method when it exposes one
  (XGBoost, LightGBM, and others do), falling back to `joblib` otherwise.
  No ML library is hardcoded as a dependency for this.
- This logic lives inline in `src.lib.experiment_tracking._save_artifact`
  today, since it is currently only needed there. If another script
  (e.g. the final model's training script) also needs to persist a
  model, decide then whether to reuse that helper or duplicate the
  four-line check — do not extract a shared module preemptively.

## 15. Experiment tracking
- Toggled by a single project-wide `use_mlflow` flag in
  `configs/global.yaml` (never per-model — see section 12).
- All experiment logging goes through
  `src.lib.experiment_tracking.log_run` — no script calls `mlflow.log_*`
  or writes run files directly.
- When `use_mlflow=True`: the tracking store lives at
  `reports/models/model_<name>/mlruns/`.
- When `use_mlflow=False`: writes to
  `reports/models/model_<name>/manual_runs/<run_name>/` instead —
  `params.json`, `metrics.json`, plus one file per artifact, with format
  inferred from type (see section 14 for models).
- Scope: `log_run` is only for small, disposable artifacts tied to one
  experimental run. Any dataset meant to be read later by another script
  (e.g. predictions, a preprocessed matrix) does not belong here — save it
  as parquet under `src.lib.paths.model_data_dir(model_name)` instead.
- `model_comparison.py` reads back via `mlflow.search_runs()` rather than
  re-implementing comparison logic by hand.

## 16. Packaging
- Official install method: `uv sync` (installs dependencies, creates
  `.venv/`, and installs the project itself in editable mode — no
  separate `pip install -e .` step needed). Run `uv sync --extra dev` to
  also include test-only dependencies.
- `uv.lock` is versioned in git — it pins the exact resolved version of
  every dependency (including transitive ones) so every clone gets an
  identical environment. Regenerate it with `uv lock` after changing
  `dependencies` or `optional-dependencies` in `pyproject.toml`.
- `.venv/` is gitignored — never commit a virtual environment.
- Any folder under `src/` that another module imports from using dotted
  notation (`from src.x.y import z`) needs an empty `__init__.py` — add it
  only when that import is actually written, not preemptively.
- Runtime dependencies go in `[project.dependencies]`; test-only
  dependencies (e.g. `pytest`) go in `[project.optional-dependencies]`
  under a `dev` group.

## 17. Git workflow
- Commits (local): never automatic. Every commit — even local, before any
  push — requires explicit confirmation from the project owner first.
- Push: never automatic and never without explicit permission, every time.
- Author identity: the project owner's own git identity, not a separate
  "agent" identity — commits made by an agent are not distinguished in
  git history from ones made manually.
- Commit message format: free-form, no fixed convention (e.g. no
  Conventional Commits prefix required). Keep messages short and
  concise — optimize for fewer tokens, not for following a template.
