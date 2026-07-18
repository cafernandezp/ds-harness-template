# Harness readiness audit — Claude CLI / Codex

Date: 2026-07-18
Scope: full repo read (tracked files, `Makefile`, `pyproject.toml`,
`.pre-commit-config.yaml`, `src/lib/*`, all docs/agents/skills), plus smoke
checks (`uv sync` env, `ruff check .`, `pytest`, import of `src.lib.*`).

Overall verdict: the documentation/prose layer is strong and internally
mostly consistent. The **runtime wiring for Claude Code is missing** —
skills and subagents live in the repo's own `skills/`/`agents/` convention,
not Claude Code's `.claude/skills/`, `.claude/agents/`. Codex uses
`AGENTS.md` natively so it fares better, but the SDK orchestration the
agent files reference doesn't exist yet either.

---

## 1. No `.claude/` directory — Claude CLI cannot discover skills or agents

**Finding.** Claude Code looks for skills at `.claude/skills/<name>/SKILL.md`
and subagents at `.claude/agents/<name>.md`. This repo has neither path —
skills live at `skills/<name>/SKILL.md`, agent instructions at
`agents/<role>.md`.

**Consequence.**
- The 3 skills (`create-adr`, `ds-research-report`, `function-conventions`)
  never auto-trigger in Claude Code, despite each having a frontmatter
  `description` clearly written for trigger matching.
- The 4 agents (LEAD, IMPLEMENTER, REVIEWER, ADVISOR) never spawn as real
  subagents. One Claude Code session ends up roleplaying all four itself.
  Role boundaries (LEAD owns memory, REVIEWER is an independent gate) are
  honor-system only, not enforced by separate contexts.
- The delegation flow described in `agents/lead.md:45-54` ("IMPLEMENTER
  executes one sub-task... REVIEWER reviews... returns a verdict") cannot
  actually execute as multi-agent handoff.

**Fix sketch.** Symlink or move `skills/` → `.claude/skills/` and `agents/`
→ `.claude/agents/`. Subagent frontmatter needs `name` + `description`
fields for the harness to route to them — current `agents/*.md` files
don't have that frontmatter (they open straight into a `# ROLE — Agent
Instructions` heading), so it would need to be added, not just moved.

**Priority:** highest — blocks the core "Claude CLI" half of the intended
use case entirely.

---

## 2. `present_files` — not a real Claude Code tool

**Finding.** `skills/create-adr/SKILL.md:47` and `:205` instruct the skill
to call `present_files` after writing the ADR file.

```
skills/create-adr/SKILL.md:47:  - **Deliver:** write the file → call `present_files` → add a one-paragraph chat
skills/create-adr/SKILL.md:205: 4. Calls `present_files`.
```

No such tool exists in Claude Code's toolset. Likely leftover from a
Claude Projects / different-SDK draft.

**Fix sketch.** Remove the `present_files` step; describe the deliverable
as "write the file, then summarize in chat" — matches how
`ds-research-report/SKILL.md` already phrases its own output contract.

**Priority:** low, mechanical — but should be verified/fixed alongside
finding #1 since it's in the same file.

---

## 3. Contradiction — `ds-research-report` recommends a pattern `CONVENTIONS.md` bans

**Finding.**

`skills/ds-research-report/SKILL.md:79-80` (Code rules):
> Prefer **leakage-safe** patterns: fit on train only, wrap target-derived
> encoders inside a `Pipeline`/CV. Show the safe pattern, not the
> convenient-but-leaky one.

`docs/CONVENTIONS.md:17-20` (§2 Code style):
> Never use sklearn `Pipeline` or `ColumnTransformer`. Preprocessing steps
> are written as explicit, separate function calls instead...

These directly conflict. As written, ADVISOR-generated research reports
will recommend code patterns that REVIEWER is instructed to reject.

**Fix sketch.** Edit the skill's Code rules bullet to show the safe
pattern using explicit train-only-fit function calls (matching
CONVENTIONS.md §2), not `Pipeline`. `CONVENTIONS.md` is the correct source
of truth here — it's the "static reference," per its own header.

**Priority:** high — a real correctness bug (agent produces on-brand
output that contradicts a hard repo rule), not just doc hygiene.

---

## 4. `CONVENTIONS.md` §16 describes a packaging layout the repo doesn't use

**Finding.**

`docs/CONVENTIONS.md:156-158`:
> Runtime dependencies go in `[project.dependencies]`; test-only
> dependencies (e.g. `pytest`) go in `[project.optional-dependencies]`
> under a `dev` group.

and `docs/CONVENTIONS.md` §16 top also says `uv sync --extra dev`.

Actual `pyproject.toml` uses `[dependency-groups]` (PEP 735 style, uv's
newer mechanism), not `[project.optional-dependencies]`. The `Makefile`
correctly uses `uv sync --group dev` / `--all-groups`, matching the real
file — so the **Makefile and pyproject agree with each other**, and
**CONVENTIONS.md disagrees with both**.

**Consequence.** Anyone (agent or human) following CONVENTIONS.md's
literal instructions for adding a dependency group would write to the
wrong TOML table and use the wrong CLI flag.

**Fix sketch.** Update CONVENTIONS.md §16 to say `[dependency-groups]` /
`uv sync --group dev`, matching current `pyproject.toml` + `Makefile`.

**Priority:** medium — doc-only fix, but a concrete "will fail if
followed literally" bug, not just style.

---

## 5. Dependency footprint is heavy for an empty template

**Finding.** `pyproject.toml` `[project.dependencies]` (always installed,
not optional) includes `torch`, `xgboost`, `lightgbm`, `shap`,
`statsmodels`, `fastapi`, `numba`/`llvmlite` (numba dep) — multi-GB
install before any project-specific code exists. `mlflow`/`optuna` are
already correctly split into the `experiments` group; the rest aren't.

**Fix sketch.** Move heavier/optional-feeling libs (`torch`, `shap`,
`fastapi` in particular — `xgboost`/`lightgbm` are probably fine to keep
core since CONVENTIONS.md's model-persistence section names them
explicitly) into an appropriate dependency group, or leave as-is if the
intent is "batteries-included template." Judgment call, not a bug —
flagging for discussion.

**Priority:** low/discretionary.

---

## 6. `main.py` — hello-world leftover

**Finding.** Root `main.py` just prints "Hello from ds-harness!". Not
mentioned anywhere in `README.md`'s repo layout section. Likely
`uv init` scaffolding never cleaned up.

**Fix sketch.** Delete, or repurpose as a real CLI entrypoint if one is
intended (Makefile has a commented-out `run:` target referencing
`your_package.main`, suggesting the latter was once planned).

**Priority:** low, cosmetic.

---

## 7. `docs/references/tooling-ci-precommit.md` is invisible to agents

**Finding.** File exists and is tracked, but isn't listed in `AGENTS.md`'s
Docs table (`docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`,
`docs/adr/`, `docs/research-reports/` are the only four rows). No agent
instruction points to it, so none of LEAD/IMPLEMENTER/REVIEWER/ADVISOR
will ever read it per their own protocol.

**Fix sketch.** Add a row to AGENTS.md's Docs table, or fold its content
into `docs/CONVENTIONS.md` §16/17 if it's small enough not to warrant a
separate file.

**Priority:** low.

---

## 8. CI half-wired

**Finding.** `.pre-commit-config.yaml` is configured (ruff + basic
hygiene hooks) but there's no `.github/workflows/` — so pre-commit only
runs if a human/agent remembers to run it locally or install the git
hook. Nothing enforces `lint`/`format-check`/`test` on push.

**Fix sketch.** Either add a minimal CI workflow running
`make lint format-check test`, or explicitly document that CI is
intentionally out of scope for this template stage.

**Priority:** low/discretionary — may be intentional for a template repo.

---

## 9. License mismatch

**Finding.** `README.md:124` says "## License \n TBD." but a `LICENSE`
file (MIT, per recent commit history) already exists at repo root.

**Fix sketch.** One-line edit: replace "TBD" with "MIT — see `LICENSE`."

**Priority:** trivial.

---

## Priority order (suggested)

1. `.claude/skills/` + `.claude/agents/` wiring — finding #1 (blocks Claude CLI use case entirely)
2. Pipeline/Pattern contradiction — finding #3 (real correctness bug)
3. `present_files` dead call — finding #2 (same file as #1, cheap)
4. CONVENTIONS.md §16 packaging text — finding #4 (doc will actively mislead if followed)
5. Dependency footprint — finding #5 (discretionary)
6. Cosmetics — findings #6, #7, #8, #9

Nothing in this repo has been modified as part of this audit. All fixes
above are proposals for discussion, not yet applied.
