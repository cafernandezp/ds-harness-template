# current.md — Active Task State

> **Owner:** LEAD  
> **Updated:** <!-- LEAD updates this at session start and after each sub-task state change -->  
> **Session:** #001

---

## Active Task

**Task ID:** `FEAT-001`  
**Title:** <!-- e.g. "Implement feature selection pipeline — filter stage" -->  
**Status:** `todo` | `in-progress` | `review` | `done` | `blocked`  
**Assigned to:** IMPLEMENTER  
**Priority:** `high` | `medium` | `low`

**Description:**
<!-- One paragraph max. What needs to be built, what inputs/outputs are expected. -->

**Acceptance criteria:**
- [ ] <!-- Criterion 1 -->
- [ ] <!-- Criterion 2 -->

**Dependencies / blockers:**
<!-- None | or describe -->

---

## Sub-tasks

| ID | Description | Assigned | Status | Review |
|---|---|---|---|---|
| ST-001-a | <!-- e.g. Load + validate raw data --> | IMPLEMENTER | `todo` | — |
| ST-001-b | <!-- e.g. Apply Spearman correlation filter --> | IMPLEMENTER | `todo` | — |
| ST-001-c | <!-- e.g. Unit test on synthetic data --> | IMPLEMENTER | `todo` | — |

---

## IMPLEMENTER Output Log

<!-- IMPLEMENTER fills this after each sub-task -->

```
sub-task: ST-001-a
file: src/data/loader.py
status: done
notes: loads CSV, validates schema, raises ValueError on missing target column
```

---

## REVIEWER Notes

<!-- REVIEWER appends one line per sub-task -->

```
ST-001-a → APPROVED (2026-06-17)
```

---

## Session Notes (LEAD)

<!-- Key decisions, assumptions, open questions for next session -->
- Assumption: dataset is tabular, stored as CSV at `data/raw/`.
- Open: confirm whether target is binary or multiclass before ST-001-b.
