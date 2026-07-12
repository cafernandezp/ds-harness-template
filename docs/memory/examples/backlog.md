# Backlog — Example (do not use as live file)

> This file is illustrative only. The live backlog lives at `docs/memory/backlog.md`.
> Copy the row format below; never add real project features here.

## Allowed `status` values
`todo` · `in_progress` · `review` · `done` · `blocked` · `cancelled`

## Table

| ID | Title | Status | Depends on | Plan | ADR |
|---|---|---|---|---|---|
| FEAT-001 | Feature selection pipeline (filter + VIF) | done | — | PLAN-001 | adr-2026-06-15-vif-threshold |
| FEAT-002 | Target encoding for high-cardinality features | in_progress | FEAT-001 | PLAN-002 | — |
| FEAT-003 | Baseline XGBoost model + cross-validation | todo | FEAT-001, FEAT-002 | PLAN-003 | — |

**Column notes:**
- `ID`: sequential, zero-padded, never reused (a cancelled FEAT-002 leaves a gap; the next new feature is still FEAT-003).
- `Depends on`: comma-separated feature IDs, or `—` if none.
- `Plan` / `ADR`: slug only, not full path (e.g. `PLAN-008`, `adr-2026-06-15-vif-threshold`). LEAD resolves the full path when needed.
- Completed features stay in the table — don't delete rows. If the table grows past ~30 rows, move `done`/`cancelled` rows to `docs/memory/backlog_archive.md`.

---

## Row template

```
| FEAT-XXX | <short one-line title> | todo | <FEAT-YYY or —> | PLAN-XXX | <adr-slug or —> |
```
