# Architecture

> High-level map of the repo. Consulted by IMPLEMENTER before every feature
> and by REVIEWER during review. Read this once, keep the mental model,
> revisit it a few times a year — not on every change.

## Bird's-eye view

`ds-harness` is a template for building a single supervised-learning model
end-to-end: from raw data selection through feature engineering, target
construction, train/test splits, model experiments, a final model, and
inference. The repo enforces a **linear pipeline** where each stage reads
the output of the previous stage and writes artifacts consumed by the next.
Ad-hoc exploration and reviewed pipeline code live side by side but are
strictly separated by folder convention.

Two axes shape the layout:

- **Pipeline stage** (`etl` → `models` → `inference`) — the order data
  flows through the system.
- **Reuse scope** (`lib` vs. stage-nested modules) — whether a piece of
  code is shared or belongs to one script of one stage.

Everything else — configs, experiment tracking, reports — is cross-cutting
and orthogonal to both axes.

## Codemap

### `src/`

The reviewed, versioned pipeline. Every module here is expected to be
reproducible and to obey the conventions in `CONVENTIONS.md`.

#### `src/lib/`

Shared utilities imported across stages and models. A module lands here
only when reused by more than one model or more than one pipeline stage —
otherwise it stays nested in the stage that owns it. Current members:

- `paths` — canonical locations for `data/`, `reports/`, per-model
  directories. Every path in the pipeline resolves through this module;
  no script hardcodes a path string.
- `config` — loads `configs/global.yaml` and merges per-model overrides.
- `experiment_tracking` — single entry point `log_run` for every
  experiment artifact. Backed by MLflow or a manual filesystem layout
  depending on the `use_mlflow` global flag.

Future shared helpers (metrics, feature selection, inspection, eval
utilities) also belong here once a second caller appears.

#### `src/etl/`

Data preparation, in pipeline order:

- `perimeter/` — defines the population under study (rows that enter the
  model). `perimeter/analysis/` is scratch space for the owner and is
  invisible to agents (see invariant below).
- `features/` — feature engineering on the perimeter.
- `target/` — target construction. Also carries an `analysis/` scratch folder.
- `train_test/` — split logic. All transformers downstream must fit on
  train only; this invariant originates here.

#### `src/models/`

Per-model experiments and the final chosen model. The structure repeats
per model (`model_name1/`, `model_name2/`, …). Cross-cutting model
diagnostics that are not tied to a single model live at the top of
`models/`: `univariate/`, `bivariate/`, `drift/`, `correlation/`.

Inside each model:

- `experiments/base_models/` — baseline and hyperparameter tuning (`hpo/`).
- `experiments/multivariate/` — multi-feature experiments.
- `experiments/preprocessing/` — preprocessing candidates. Written as
  explicit function calls, never as a sklearn `Pipeline` or
  `ColumnTransformer` (see `CONVENTIONS.md` §2).
- `experiments/model_comparison.py` — reads back experiment runs and
  ranks them. Consumes tracking output rather than re-running models.
- `final_model/train.py` and `final_model/evals.py` — the chosen model's
  training entry point and evaluation. The output of `train.py` is the
  contract that `inference/` consumes.

#### `src/inference/`

Production-facing code. Currently `inference/perimeter/`, mirroring the
etl stage that defines who gets scored. Anything here — plus any
`src/lib/` function it imports — is subject to mandatory tests under a
`tests/` mirror (see `CONVENTIONS.md` §13).

### `configs/`

Project-wide and per-model configuration. `global.yaml` holds project-wide
keys (e.g. `use_mlflow`); per-model files override the subset of keys
they care about. `configs/local.yaml` is machine-specific and gitignored;
everything else is versioned because it encodes reviewable decisions.

### `reports/`

Fully gitignored. All generated artifacts — MLflow store, manual run
directories, per-model data — land here. Nothing in `reports/` is a
contract; anything the pipeline must reproduce exactly (a selected
feature list, a fitted encoding) is stored as a `.py` module under
`src/` instead, never as a CSV in `reports/`.

### `docs/`

- `ARCHITECTURE.md` — this file.
- `CONVENTIONS.md` — code style, naming, imports, formats, testing.
- `adr/` — binding decisions. Consult before reopening any decision.
- `research-reports/` — prior technical explorations by ADVISOR.
- `memory/` — agent state (`progress/`, `backlog.md`, `plans/`).

### `agents/`, `skills/`, `AGENTS.md`

Agent instructions and skill definitions. Not pipeline code; the runtime
agents (LEAD, IMPLEMENTER, REVIEWER, ADVISOR) read from here to know how
to operate on `src/` and `docs/`.

### `playground/`

Free-form scratch space outside the pipeline. Never imported from `src/`.

## Architectural invariants

Invariants are load-bearing rules that hold repo-wide. Most are absences
— things the code does *not* do — which are hard to see by reading.

- **The pipeline is one-way.** `perimeter` never imports from `features`;
  `features` never imports from `target`; `models` never imports from
  `inference`. If a downstream stage needs upstream logic, that logic
  moves into `src/lib/`.
- **`src/lib/` has no upward dependencies.** No module in `lib/` imports
  from `etl/`, `models/`, or `inference/`. `lib/` is a leaf.
- **`analysis/` folders are invisible to agents.** Any folder named
  `analysis` under `src/` belongs to the human owner. Agents (LEAD,
  IMPLEMENTER, REVIEWER, ADVISOR) never read from, write to, or depend on
  it. Findings from `analysis/` become durable only via an ADR or a
  research report — never by another script importing from it.
- **Transformers fit on train only.** No preprocessing, encoding, or
  feature selection ever calls `.fit` on validation or test data. Enforced
  by review, not by types.
- **No sklearn `Pipeline` or `ColumnTransformer`.** Preprocessing is a
  sequence of explicit function calls so every transformation is visible
  in the trace.
- **No hardcoded paths.** All filesystem locations resolve through
  `src.lib.paths`. No absolute paths anywhere in `src/`. No handwritten
  strings pointing at `data/` or `reports/`.
- **One feature in progress at a time.** Only one entry in
  `docs/memory/backlog.md` may have `status: "in_progress"`. LEAD
  enforces this before any work starts.
- **`reports/` is never a contract.** Nothing in `src/` reads a file from
  `reports/` expecting it to exist. Contracts live as `.py` modules
  under `src/`.

## Boundaries

- **`src/` ↔ `reports/`.** `src/` writes to `reports/` (via
  `src.lib.paths` and `src.lib.experiment_tracking.log_run`), but never
  reads from it except through `experiment_tracking` itself (e.g.
  `model_comparison.py` calling `mlflow.search_runs()`). This boundary
  is what makes `reports/` safe to delete.
- **Development ↔ production.** Anything under `src/etl/` and
  `src/models/` is exploratory: tests optional, code churns fast.
  Anything under `src/inference/` — and any `lib/` function it pulls in
  — is production: tests mandatory in `tests/`, mirroring the path.
- **Global config ↔ per-model config.** `configs/global.yaml` owns
  project-wide switches (`use_mlflow`). Per-model files override only
  the keys they need. A per-model file never sets a project-wide key.
- **Agents ↔ human owner.** Reviewed pipeline code and `docs/` are the
  agents' surface. `analysis/` folders and `playground/` are the owner's
  surface. The two surfaces do not import from each other.

## Cross-cutting concerns

- **Paths.** Every location goes through `src.lib.paths`. New locations
  are added there when a caller first needs them, not preemptively.
- **Config.** `src.lib.config` merges `global.yaml` with per-model
  overrides. Callers ask for a resolved config; they do not open YAML
  files themselves.
- **Experiment tracking.** `src.lib.experiment_tracking.log_run` is the
  only writer of experiment artifacts. The `use_mlflow` flag decides
  whether the store is MLflow (`reports/models/model_<name>/mlruns/`) or
  the manual filesystem layout
  (`reports/models/model_<name>/manual_runs/<run_name>/`). Callers do
  not branch on this flag.
- **Reproducibility.** A single fixed `random_state` threads through all
  splits, models, and stochastic steps. There is no per-experiment seed
  override — differences between runs must come from code, not from RNG.
- **Model persistence.** Models are saved via their own `.save_model()`
  when available, falling back to `joblib`. Never pickle directly. The
  logic lives inline in `experiment_tracking._save_artifact` and stays
  there until a second caller needs it.
- **Packaging.** The repo is installed as an editable package via
  `uv sync`, so `from src.x.y import z` resolves the same regardless of
  where a script is launched from. `uv.lock` is versioned; `.venv/` is
  not.
- **Testing.** Absent by design in `etl/` and `models/` during
  development. Mandatory once code enters `inference/`, mirrored under
  `tests/`.
