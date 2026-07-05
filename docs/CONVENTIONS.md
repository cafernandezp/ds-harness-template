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

## 3. Imports
- No wildcard imports.
- Absolute imports from the `src` package (`from src.lib.metrics import compute_mae`).
- No `sys.path` manipulation.

## 4. File formats
- Parquet over CSV for tabular data.
- Any artifact that other code depends on downstream (e.g. a selected
  feature list) must be a `.py` module, not a notebook or a CSV.

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
  regenerate — lives in `src/`, version-controlled. Examples: a selected
  feature list, a categorical encoding map fit on train. These are
  contracts, not regenerable diagnostics, so they never go in `reports/`
  or `data/`.

## 8. Function signatures
- Keyword-only arguments for any function with more than 2 parameters.
- Max 4 arguments per function; refactor into a config object beyond that.

## 9. Reproducibility
- Fixed `random_state` across all splits, models, and stochastic steps.
- All transformers fit on train only; never fit on val/test.

## 10. Paths
- No absolute paths anywhere in `src/`.
- Repo installed in editable mode (`pip install -e .`) so `src` imports
  resolve identically regardless of execution location.


## 11. Analysis folders (`*/analysis/`)
Any folder named `analysis` anywhere under `src/` is reserved for the project
owner's personal, manual, ad hoc exploration (typically scratch notebooks).
These folders:
- are not part of the reviewed pipeline;
- must never be written to, read from, or depended upon by any agent
  (LEAD, IMPLEMENTER, REVIEWER, ADVISOR);
- are versioned in git like the rest of `src/` — no special gitignore treatment.

Since agents never read these folders, any durable conclusion from this
exploration (a decision, a finding worth keeping) must be formalized
separately — an ADR in `docs/adr/` or a write-up in `docs/research-reports/` —
rather than left only inside a notebook.

## 12. Config loading
Model-specific config values override `global.yaml` when both define the
same key. Any key not overridden by the model is inherited from
`global.yaml`. Only `configs/local.yaml` is gitignored; the rest of
`configs/` is versioned, since it represents reviewable project decisions,
not machine-specific or regenerable data.