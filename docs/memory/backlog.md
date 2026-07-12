# Backlog

> **Owner:** LEAD (read/write). No other agent reads or writes this file directly —
> IMPLEMENTER and REVIEWER receive their task context from LEAD via `current.md`.
> **Entry rule:** a feature is added to this table only after its plan has been
> approved (see `docs/memory/plans/`). This is not a wishlist and not a pre-loaded
> generic DS pipeline.
> **Concurrency rule:** only one feature may be `in_progress` at a time.

> **Note:** See `docs/memory/examples/backlog.md` for an example of a populated backlog.

## Allowed `status` values
`todo` · `in_progress` · `review` · `done` · `blocked` · `cancelled`

## Table

| ID | Title | Status | Depends on | Plan | ADR |
|---|---|---|---|---|---|

**Column notes:**
- `ID`: sequential, zero-padded, never reused (a cancelled FEAT-002 leaves a gap; the next new feature is still FEAT-003).
- `Depends on`: comma-separated feature IDs, or `—` if none (e.g. `FEAT-001, FEAT-003`).
- `Plan` / `ADR`: the slug only, not the full path (e.g. `PLAN-008`, `adr-2026-06-15-vif-threshold`). LEAD resolves the full path when it needs to open the file.
- Completed features stay in the table — don't delete rows; git history plus this table is the audit trail. If the table grows past ~30 rows, move `done`/`cancelled` rows to `docs/memory/backlog_archive.md` to keep this file scannable.

---

## Row template (copy-paste for a new feature)

```
| FEAT-XXX | <short one-line title> | todo | <FEAT-YYY or —> | PLAN-XXX | <adr-slug or —> |
```

---

## What does NOT belong in this table

- Acceptance criteria → live in `docs/memory/plans/PLAN-XXX-<slug>.md`.
- Who executes → always IMPLEMENTER → REVIEWER, fixed by design, no need to record it.
- Created/closed dates → captured in `docs/memory/progress/history.md`.
- Experiment runs, metrics, hyperparameters tried → live in MLflow. A pointer, if wanted, goes in `impl_<feature>.md`, not here.
- Single-session tasks with no future dependency → don't need a row at all.
