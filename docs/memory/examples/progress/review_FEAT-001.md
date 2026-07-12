# review_FEAT-001.md — Review Trace (Example)

> **This file is illustrative only.** The live traces live at
> `docs/memory/progress/review_<feature>.md`. Copy the format below;
> never add real project reviews here.
>
> **Owner:** REVIEWER (write). Read-only for LEAD. IMPLEMENTER never
> touches this file.
> **Rule:** One trace file per feature. One review block per sub-task,
> appended in order. Never rewrite past blocks.

---

## Feature

**ID:** `FEAT-001`
**Title:** Feature selection pipeline — filter stage
**Plan:** `PLAN-001`

---

## Sub-task ST-001-a — Load + validate raw data

**Reviewed:** 2026-06-17
**Trace read:** `impl_FEAT-001.md` (sub-task ST-001-a)

**Checklist:**
- Leakage: N/A — pure IO + validation, no fit.
- Reproducibility: ✅ deterministic; no RNG involved.
- Metrics: N/A.
- Conventions: ✅ `df` naming (§1), functional style (§2), absolute
  import from `src` (§3), path via `src.lib.paths` (§10).
- Acceptance criteria: (1) loads parquet ✅ (2) raises on schema
  mismatch ✅.

**Verdict:** `APPROVED`

---

## Sub-task ST-001-b — Spearman correlation filter

**Reviewed:** 2026-06-18
**Trace read:** `impl_FEAT-001.md` (sub-task ST-001-b)

**Checklist:**
- Leakage: ❌ filter runs on full `df` before train/test split. Even
  though this feature does not yet define a split, the convention
  (§9) requires fit-on-train-only wherever a fit-like step exists.
- Reproducibility: ✅ fixed `seed`, deterministic tiebreak.
- Metrics: N/A.
- Conventions: ✅ `seed` naming (§1), keyword-only args (§8),
  functional style (§2).
- Acceptance criteria: (1) drops one column per correlated pair ✅
  (2) deterministic ✅ (3) leakage-safe ❌.

**Verdict:** `REVISION NEEDED`
**Action for IMPLEMENTER:** in
`src/etl/features/correlation_filter.py:12`, make the leakage-safety
contract explicit (docstring at minimum) so any caller passing the
full frame is caught in review.

---

### Re-review — 2026-06-18

**Trace read:** `impl_FEAT-001.md` (Revision block on ST-001-b)

- Leakage: ✅ docstring now states `df` must be train only; enforced
  by review per §9.
- All other items unchanged from first pass.

**Verdict:** `APPROVED`

---

## Trace format rules

- **One block per sub-task**, in the order reviewed.
- **Fields per block:** Reviewed date, Trace read (which impl section),
  Checklist (each item ✅ / ❌ / N/A with a one-line note), Verdict,
  Action on `REVISION NEEDED`.
- **On re-review after a revision:** append a `Re-review` sub-block;
  do not rewrite the original verdict block.
- **Verdict must cite the file + line on failure** (e.g.
  `src/etl/features/correlation_filter.py:12`), not vague language.
- **What NOT to include:** how to fix it (that's IMPLEMENTER's call
  unless genuinely ambiguous), personal preference, scope creep into
  unrelated code (mention only, do not demand).
