# ds-harness

Repository template for building a single supervised-learning model
end-to-end with an AI multi-agent workflow. Clone, adapt, run — the
harness enforces a linear pipeline (perimeter → features → target →
train/test → models → inference), leakage-safe conventions, and a
lightweight memory system so agent sessions stay coherent across time.

Not a project — a starting point. There is no live model, no data, no
active feature. Everything below is scaffolding to be filled in.

## What's in the box

- **Four agents** (LEAD, IMPLEMENTER, REVIEWER, ADVISOR) with roles,
  boundaries, and delegation flow defined in `AGENTS.md` and
  `agents/*.md`. Same text loads as the system prompt in Claude Projects
  or as `instructions` in the Codex/Agents SDK.
- **Three skills** (`create-adr`, `ds-research-report`,
  `function-conventions`) under `skills/` that agents invoke to produce
  binding decisions, research reports, and convention-compliant code.
- **A memory system** in `docs/memory/` — active session state, an
  append-only session log, a per-feature backlog, and plans. LEAD owns
  it; other agents write only their own trace files.
- **A shared library skeleton** (`src/lib/`) with `paths`, `config`, and
  `experiment_tracking` — the three cross-cutting utilities every DS
  pipeline needs, wired to a single `use_mlflow` switch.
- **Reviewed conventions** (`docs/CONVENTIONS.md`) and an
  **architecture map** (`docs/ARCHITECTURE.md`) — the two documents
  every agent reads before writing or reviewing code.

## Prerequisites

- Python 3.12 (see `.python-version`).
- [`uv`](https://docs.astral.sh/uv/) for dependency management.

## Quick start

```bash
# Standard install: creates .venv and installs the project editable.
make install

# With dev tools (pytest, ruff).
make install-dev

# Everything — dev + notebooks + experiments (mlflow, optuna).
make install-all
```

Verify:

```bash
uv run python -c "from src.lib.paths import REPO_ROOT; print(REPO_ROOT)"
```

## Adapting the template to a new project

1. **Fill in `AGENTS.md` → Project Identity.** Name, task type,
   primary/secondary metric, phase, one-liner. Six placeholders.
2. **Set metric defaults in `configs/global.yaml`.** Replace `mae`/`r2`
   with the project's actual choices (or leave for the first ADR).
3. **Create the first `configs/models/<model_name>.yaml`** when the
   first real model appears — see `configs/models/README.md` for
   format.
4. **Populate `docs/memory/backlog.md`.** No pre-loaded generic
   pipeline — every entry is added only after a plan is approved.
5. **Launch a session.** LEAD reads `docs/memory/progress/current.md`
   and the backlog, decomposes the active feature, and delegates.

## Repo layout

```
AGENTS.md              # entry point for every agent — read fully before acting
CLAUDE.md              # -> AGENTS.md (Claude Code convention)
agents/                # per-agent instructions (LEAD, IMPLEMENTER, REVIEWER, ADVISOR)
skills/                # invocable skills (create-adr, ds-research-report, function-conventions)
configs/
  global.yaml          # project-wide defaults
  models/              # per-model overrides (one file per model)
docs/
  ARCHITECTURE.md      # pipeline order, stack, src/ structure, invariants
  CONVENTIONS.md       # code style, naming, metrics, paths, testing
  adr/                 # binding decisions (LEAD writes via create-adr)
  research-reports/    # technical explorations (ADVISOR writes via ds-research-report)
  memory/
    backlog.md         # feature backlog (LEAD only)
    plans/             # execution plans (LEAD only)
    progress/          # current.md + history.md + per-feature traces
    examples/          # illustrative populated versions of the above
src/
  lib/                 # shared utilities: paths, config, experiment_tracking
  etl/                 # perimeter -> features -> target -> train_test
  models/              # per-model experiments and final_model
  inference/           # production-facing code (tests mandatory)
tests/                 # mirrors src/ by relative path
playground/            # scratch, notes, personal references — never imported from src/
reports/               # gitignored: mlflow store, manual runs, generated artifacts
data/                  # gitignored: raw + intermediate parquets
```

## Where things go — quick decision guide

| Situation | Destination |
|---|---|
| Persistent project decision (algorithm, protocol, threshold) | `docs/adr/` via LEAD + `create-adr` |
| Technical exploration, options + tradeoffs, no decision | `docs/research-reports/` via ADVISOR + `ds-research-report` |
| One-off implementation choice | `impl_<feature>.md` trace, not an ADR |
| Reusable helper called by ≥2 stages or ≥2 models | `src/lib/` |
| Helper used by exactly one script | nested next to that script, not in `lib/` |
| Fitted artifact downstream must reproduce exactly | `.py` module under `src/`, never a CSV in `reports/` |
| Anything regenerable by rerunning the pipeline | `reports/` or `data/` (both gitignored) |
| Owner's personal scratch exploration | `src/<stage>/analysis/` — invisible to agents |
| Free-form scratch, temp code, notes, or personal references | `playground/` — invisible to agents |

## Key invariants (don't break these)

See "Architectural invariants" in `docs/ARCHITECTURE.md` for the full,
authoritative list (one-way pipeline, `lib/` as a leaf, train-only
fitting, no sklearn `Pipeline`/`ColumnTransformer`, no hardcoded paths,
one feature in progress, `reports/` never a contract). Kept in one place
so it can't drift out of sync with this file.

## License

MIT — see `LICENSE`.
