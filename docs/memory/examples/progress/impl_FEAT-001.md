# impl_FEAT-001.md — Implementation Trace (Example)

> **This file is illustrative only.** The live traces live at
> `docs/memory/progress/impl_<feature>.md`. Copy the format below; never
> add real project work here.
>
> **Owner:** IMPLEMENTER (write). Read-only for REVIEWER and LEAD.
> **Rule:** One trace file per feature — never per sub-task, never
> shared across features. Append a new sub-task section after each one
> is done; never rewrite past sections.

---

## Feature

**ID:** `FEAT-001`
**Title:** Feature selection pipeline — filter stage
**Plan:** `PLAN-001`
**Started:** 2026-06-17

---

## Sub-task ST-001-a — Load + validate raw data

**Status:** done
**Reviewed:** APPROVED (see `review_FEAT-001.md`)

**What changed:**
- `src/etl/perimeter/load.py` — new. Reads `data/raw/customers.parquet`,
  validates presence of `customer_id`, `target`, and required feature
  columns, raises `ValueError` on schema mismatch.
- `src/lib/paths.py` — added `PERIMETER_RAW_FILE` constant. New path
  needed by this sub-task; no other caller yet.

**Why (assumptions):**
- Raw data is a single parquet, not a directory of shards. Confirmed
  with owner in session notes.
- Schema validation is fail-loud, not fail-silent — a missing column is
  a bug in upstream data, not something to impute past.

**Verification:**
- Ran `uv run python -m src.etl.perimeter.load` against
  `data/raw/customers.parquet` — 47,832 rows loaded, schema OK.
- Ran against a synthetic frame missing `target` — `ValueError` raised
  as expected.

**Notes for REVIEWER:**
- No transformer fit here — pure IO + validation. Leakage check N/A.

---

## Sub-task ST-001-b — Spearman correlation filter

**Status:** done
**Reviewed:** REVISION NEEDED → fixed → APPROVED (see review trace)

**What changed:**
- `src/etl/features/correlation_filter.py` — new. `filter_by_spearman(df,
  threshold=0.85, seed=42)` drops one column per pair above the
  threshold, keeping the one with higher variance.
- Threshold sourced from `config.feature_selection.spearman_threshold`
  in the caller, defaulted to 0.85 here for the standalone entry point.

**Why (assumptions):**
- Spearman (not Pearson) because feature distributions are skewed —
  documented in session notes.
- Higher-variance-wins tiebreak is the current pick; if this becomes a
  binding rule, it belongs in an ADR.

**Verification:**
- Synthetic frame with two collinear pairs (r > 0.9) — filter drops one
  per pair.
- Fixed `seed=42` → deterministic output across runs.

**Revision (from REVIEWER, 2026-06-18):**
- Flagged: filter was fit on the full frame before the train/test
  split existed downstream. Not leakage yet (no split defined this
  feature), but conventions require fitting on train only.
- Fix: added a docstring note that any real call must pass `df=X_train`
  only. Signature unchanged — enforced by review, per convention §9.

---

## Blockers

None.

---

## Trace format rules

- **Section per sub-task**, in the order they were done.
- **Fields per section:** Status, What changed (files + one line each),
  Why / assumptions, Verification (what was run, what the result was),
  Notes for REVIEWER (leakage, seeds, anything non-obvious).
- **On revision:** append a `Revision` block; do not rewrite the
  original section. Preserves the trail.
- **What NOT to include:** full code diffs (git has them), narrative,
  meta-commentary, or anything for a different feature.
