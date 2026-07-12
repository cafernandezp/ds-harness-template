# CHECKPOINTS.md

> **Read by:** REVIEWER (phase verification), LEAD (feature gating).  
> A checkpoint is **passed** only when every criterion in its section is met and REVIEWER has signed off. Criteria are verifiable by reading code and artifacts — no subjective calls.

---

## Phase 1 — ETL Complete

All input data preparation is reviewed pipeline code; nothing lives only in `analysis/` notebooks.

- [ ] `src/etl/perimeter/` implemented: population definition is deterministic and reproducible from source data.
- [ ] `src/etl/features/` implemented: every feature transformation is an explicit function call; no sklearn `Pipeline` or `ColumnTransformer`.
- [ ] `src/etl/target/` implemented: target variable construction is code-reviewed and documented.
- [ ] `src/etl/train_test/` implemented: train/test split is fixed by `random_state`; no downstream code has seen test labels.
- [ ] All paths resolve through `src.lib.paths`; no hardcoded path strings in any `src/etl/` file.
- [ ] REVIEWER verdict: `APPROVED` on all ETL features in the backlog.

---

## Phase 2 — Model Selection Complete

A final model has been chosen via a reviewed comparison; the decision is recorded.

- [ ] At least one experiment cycle complete: `src/models/<name>/experiments/` contains reviewed baseline and at least one tuning round.
- [ ] `src/models/<name>/experiments/model_comparison.py` ran and ranked all tracked runs.
- [ ] Final model chosen and rationale recorded in an ADR (`docs/adr/`).
- [ ] `src/models/<name>/final_model/train.py` trains the chosen model reproducibly (same result on two independent runs with the same `random_state`).
- [ ] `src/models/<name>/final_model/evals.py` reports primary and secondary metrics on held-out test data — test set touched **once**, at this step only.
- [ ] No transformer was fit on validation or test data (REVIEWER leakage check passed).
- [ ] REVIEWER verdict: `APPROVED` on the final model feature.

---

## Phase 3 — Production Ready

Inference code is tested, reproducible, and safe to deploy.

- [ ] `src/inference/` implemented: scores the production perimeter using the final model artifact.
- [ ] Every `src/lib/` function imported by `src/inference/` has a corresponding test in `tests/` mirroring the same relative path.
- [ ] All `tests/` pass (`uv run pytest`).
- [ ] End-to-end reproduction verified: a fresh `uv sync` + full pipeline run produces the same predictions as the original run (within floating-point tolerance).
- [ ] `configs/global.yaml` has `primary_metric` and `secondary_metric` set (not commented out).
- [ ] No absolute paths, no hardcoded strings outside `src.lib.paths`.
- [ ] REVIEWER verdict: `APPROVED` on all inference features.
