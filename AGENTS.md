# AGENTS.md

> Entry point for all AI agents working on this project.
> Read this file fully before taking any action. Follow the pointers — do not improvise.

---

## Project Identity

- **Name:** <!-- e.g. Judicial Progress Score -->
- **Type:** <!-- regression / binary classification / multiclass -->
- **Primary metric:** <!-- MAE / AUC-ROC / F1 -->
- **Secondary metric:** <!-- R² / precision-recall -->
- **Current phase:** <!-- Developing / Production -->
- **One-liner:** <!-- What the model does and who uses the output -->

---

## Agents

| Agent       | Role                                                                             | Instructions            |
| ----------- | -------------------------------------------------------------------------------- | ----------------------- |
| LEAD        | Orchestrates sessions, owns all state, writes ADRs and plans                     | `agents/leader.md`      |
| IMPLEMENTER | Writes and runs code; produces artifacts                                         | `agents/implementer.md` |
| REVIEWER    | Quality gate: leakage, metrics, reproducibility, conventions                     | `agents/reviewer.md`    |
| ADVISOR     | Senior DS/ML consultant; answers questions and writes research reports on demand | `agents/advisor.md`     |

---

## Skills

| Skill                  | Invoked by  | Produces                                                 | Instructions                           |
| ---------------------- | ----------- | -------------------------------------------------------- | -------------------------------------- |
| `ds-research-report`   | ADVISOR     | Technical exploration report in `docs/research-reports/` | `skills/ds-research-report/SKILL.md`   |
| `create-adr`           | LEAD        | Binding decision record in `docs/adr/`                   | `skills/create-adr/SKILL.md`           |
| `function-conventions` | IMPLEMENTER | Code following project style and conventions             | `skills/function-conventions/SKILL.md` |

---

## Memory

| File                                       | Owner                          | Contains                                                  |
| ------------------------------------------ | ------------------------------ | --------------------------------------------------------- |
| `docs/memory/progress/current.md`          | LEAD (R/W)                     | Active session: feature in progress, sub-tasks, blockers  |
| `docs/memory/progress/history.md`          | LEAD (append-only)             | Session log — never edited, only appended                 |
| `docs/memory/backlog.json`                 | LEAD (R/W)                     | Feature backlog with status, priority, plan and ADR links |
| `docs/memory/plans/`                       | LEAD (R/W)                     | Exec plans — one `.md` file per plan                      |
| `docs/memory/progress/impl_<feature>.md`   | IMPLEMENTER (W) / REVIEWER (R) | Implementation trace per feature                          |
| `docs/memory/progress/review_<feature>.md` | REVIEWER (W) / LEAD (R)        | Review trace per feature                                  |

---

## Docs

| File                     | Read by                                      | Contains                                                                |
| ------------------------ | -------------------------------------------- | ----------------------------------------------------------------------- |
| `docs/ARCHITECTURE.md`   | IMPLEMENTER (before every feature), REVIEWER | Pipeline order, approved stack, `src/` structure, active ADRs           |
| `docs/CONVENTIONS.md`    | IMPLEMENTER, REVIEWER                        | Code style, naming, metrics, import rules, file formats                 |
| `docs/adr/`              | All agents                                   | Binding project decisions — consult before reopening any decision       |
| `docs/research-reports/` | ADVISOR, LEAD                                | Prior technical explorations — consult before writing on the same topic |
| `CHECKPOINTS.md`         | REVIEWER, LEAD                               | Verifiable "done" criteria per project phase                            |

---

## One-Feature-at-a-Time Rule

Only one feature may have `status: "in_progress"` in `docs/memory/backlog.json` at any time.
LEAD resolves any conflict before the session proceeds.

---

## Session Protocol

**Start:**
1. LEAD reads `docs/memory/progress/current.md` + `docs/memory/backlog.json`.
2. LEAD reads `docs/ARCHITECTURE.md` if the active feature touches the pipeline.
3. LEAD decomposes the active feature into sub-tasks and updates `current.md`.

**End:**
1. LEAD marks completed sub-tasks in `current.md`.
2. LEAD updates feature `status` in `docs/memory/backlog.json`.
3. LEAD appends a session summary to `docs/memory/progress/history.md`.


## Engineering Principles

Every agent that writes or reviews code follows these four rules:

| Principle             | Rule                                                                                                                                                     |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Think Before Coding   | State assumptions explicitly. If a request is ambiguous, ask instead of guessing.                                                                        |
| Simplicity First      | Write the minimum code that solves the request. No speculative features, no premature abstractions.                                                      |
| Surgical Changes      | Touch only what the task requires. Read adjacent exports/callers before writing next to them. Don't refactor unrelated working code.                     |
| Goal-Driven Execution | Define verifiable success criteria before starting a sub-task. If a sub-task fails, stop and report — don't build the next one on top of a broken state. |