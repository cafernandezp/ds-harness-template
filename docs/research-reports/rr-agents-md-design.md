# How to Design AGENTS.md — Generic Router for AI-Assisted DS Projects

> **Created by:** Claude Sonnet 4.6
> **Date:** 2026-06-17
> **Skill:** ds-research-report

---

> **Context.**
> The question is not "what goes in AGENTS.md" in general, but specifically for a
> **data science project** where multiple AI agents (Leader, Implementer, Reviewer,
> Advisor) collaborate using Codex and/or Claude Code. The project follows a
> developing → production lifecycle in Python, uses notebooks in the developing phase
> and refactored modules in production, and has explicit conventions around tools
> (uv, ruff, mlflow, xgboost, shap, optuna, click, FastAPI, Pydantic), file formats
> (parquet over CSV), coding style (functional over OOP, no sklearn.Pipeline,
> explicit keyword arguments), and documentation (ADRs, research reports, memory).
>
> **Core constraint:** AGENTS.md must be tool-agnostic — identical file works in
> Codex and Claude Code without modification.
>
> **Key design tension:** AGENTS.md must be short enough to load in every context
> window, but complete enough that an agent can navigate the entire harness from it.
> The answer is progressive disclosure: AGENTS.md is a router, not a manual.

---

## TL;DR — Recommended Structure

1. **One-line purpose** — what this file is and how to use it.
2. **Project identity** — problem type, phase, primary metric. Anchors every agent decision.
3. **Agent roster** — name, role summary, pointer to full instructions.
4. **Skill registry** — skill name, which agent invokes it, pointer to `SKILL.md`.
5. **Memory map** — pointers to live state files the agents read/write.
6. **Docs map** — pointers to reference documents (architecture, conventions, ADRs).
7. **One-feature-at-a-time rule** — the single most important harness constraint, stated explicitly.
8. **Session protocol** — three lines: how to start, how to end, what is append-only.

Do **not** include: detailed rules (those live in `agents/*.md`), skill instructions
(those live in `skills/*/SKILL.md`), or project conventions (those live in
`docs/conventions.md`). AGENTS.md contains pointers, not content.

---

## The Core Design Question: What Belongs in AGENTS.md vs Elsewhere?

Before defining sections, the key decision is what kind of information lives here.

| Information type | Lives in | Why |
|---|---|---|
| "Where do I go to do X?" | `AGENTS.md` | Navigation — every agent needs this |
| "How do I do X as an agent?" | `agents/<role>.md` | Role-specific — only that agent needs it |
| "How do I produce artifact Y?" | `skills/<skill>/SKILL.md` | Skill-specific — loaded on demand |
| "What has been decided about this project?" | `docs/adr/` | Historical — consulted, not loaded always |
| "What is the current task?" | `docs/memory/progress/current.md` | Live state — read every session |
| "What conventions does the code follow?" | `docs/conventions.md` | Reference — consulted by IMPLEMENTER |
| "What is the system architecture?" | `docs/architecture.md` | Reference — consulted before any feature |

**The test for whether something belongs in AGENTS.md:**
> "Does every agent need this at the start of every session?"

If yes → it belongs in AGENTS.md.
If only one agent needs it, or only in specific situations → it belongs in the
pointed-to file, not in AGENTS.md.

---

## Section 1 — One-Line Purpose

**What it contains:** a single sentence explaining what AGENTS.md is and the
instruction to read it before doing anything else.

**Why it matters:** agents do not always read files top-to-bottom with full attention.
An explicit directive at line 1 anchors the document.

```markdown
# AGENTS.md

> This file is the entry point for all AI agents working on this project.
> Read it fully before taking any action. Follow the pointers — do not improvise.
```

---

## Section 2 — Project Identity

**What it contains:** problem type, current phase, primary metric, and a one-line
description of what the system does.

**Why it matters:** every agent decision — what to implement, how to evaluate,
what counts as "done" — depends on knowing what the project is. Without this,
REVIEWER cannot validate that the right metric is used, ADVISOR cannot calibrate
the depth of a research report, and IMPLEMENTER does not know whether it is
writing notebook code (developing phase) or production modules (production phase).

**For a DS project specifically**, the phase distinction is critical because it
determines the output format:

| Phase | Output format | Location |
|---|---|---|
| Developing | Jupyter notebooks | `notebooks/` |
| Production | Python modules | `<repo_name>/<repo_name>/` |

```markdown
## Project Identity

- **Name:** Judicial Progress Score
- **Type:** Regression (continuous score [0,1])
- **Primary metric:** MAE
- **Current phase:** Developing → Production refactor
- **One-liner:** Predict judicial case progress; score communicated directly to business.
```

---

## Section 3 — Agent Roster

**What it contains:** one row per agent with name, role in one line, and pointer
to full instructions. Nothing more.

**Why it matters:** this is the core navigation entry. An agent reading AGENTS.md
identifies its role here and loads its full instructions from the pointer. The
description must be short enough to scan but specific enough to disambiguate roles.

**What NOT to include here:** detailed rules, prohibitions, checklists. Those live
in `agents/<role>.md`. If you put rules here, you duplicate them and they diverge.

```markdown
## Agents

| Agent | Role | Instructions |
|---|---|---|
| LEAD | Orchestrates sessions, owns state, writes ADRs and plans | `agents/leader.md` |
| IMPLEMENTER | Writes and runs code; produces artifacts | `agents/implementer.md` |
| REVIEWER | Quality gate: leakage, metrics, reproducibility | `agents/reviewer.md` |
| ADVISOR | DS/ML senior consultant; writes research reports on demand | `agents/advisor.md` |
```

---

## Section 4 — Skill Registry

**What it contains:** skill name, which agent invokes it, what it produces, and
pointer to `SKILL.md`.

**Why it matters:** without explicit ownership, any agent may invoke any skill,
producing artifacts in the wrong format or at the wrong moment. The registry makes
invocation unambiguous.

**For a DS project**, the skill set reflects the documentation workflow:
research reports feed ADRs, ADRs feed plans, plans feed features. Each skill
corresponds to one artifact type in that chain.

```markdown
## Skills

| Skill | Invoked by | Produces | Instructions |
|---|---|---|---|
| `ds-research-report` | ADVISOR | Technical exploration report in `docs/research-reports/` | `skills/ds-research-report/SKILL.md` |
| `create-adr` | LEAD | Binding decision record in `docs/adr/` | `skills/create-adr/SKILL.md` |
| `function-conventions` | IMPLEMENTER | Code following project style conventions | `skills/function-conventions/SKILL.md` |
```

---

## Section 5 — Memory Map

**What it contains:** pointers to the live state files that agents read and write
during sessions. These are the files that make state persistent across context
window resets.

**Why it matters:** this is the "working memory" of the harness. Every session
starts by reading these files. If an agent does not know where they are, it starts
from scratch and loses continuity.

**Files that belong here:** only files that change during normal operation.
Static reference docs (architecture, conventions) belong in Section 6.

```markdown
## Memory

| File | Owner | Contains |
|---|---|---|
| `docs/memory/progress/current.md` | LEAD (R/W), others (R) | Active session: current feature, sub-tasks, blockers |
| `docs/memory/progress/history.md` | LEAD (append-only) | Session log — never edited, only appended |
| `docs/memory/backlog.json` | LEAD (R/W) | Feature list with status, priority, plan, ADR links |
| `docs/memory/plans/` | LEAD (R/W) | Exec plans — one file per plan |
| `docs/memory/progress/impl_<feature>.md` | IMPLEMENTER (W), REVIEWER (R) | Implementation trace per feature |
| `docs/memory/progress/review_<feature>.md` | REVIEWER (W), LEAD (R) | Review trace per feature |
```

---

## Section 6 — Docs Map

**What it contains:** pointers to stable reference documents. These are read before
implementing a feature, not every session.

**Why it matters:** agents need to know where authoritative project decisions live.
Without this map, IMPLEMENTER may make assumptions about the pipeline order,
stack, or conventions that contradict existing ADRs.

**The most critical file for a DS project is `architecture.md`** — it defines the
pipeline step order, approved libraries, and src/ structure. An agent that
implements without reading it may introduce steps out of order or unapproved
dependencies.

```markdown
## Docs

| File | Read by | Contains |
|---|---|---|
| `docs/architecture.md` | IMPLEMENTER (before every feature), REVIEWER | Pipeline order, approved stack, src/ structure, active ADRs |
| `docs/conventions.md` | IMPLEMENTER, REVIEWER | Code style, naming, metric definitions, import rules |
| `docs/adr/` | LEAD, ADVISOR, REVIEWER | Binding project decisions — consult before reopening any decision |
| `docs/research-reports/` | ADVISOR, LEAD | Technical explorations — consult before writing a new one on the same topic |
| `CHECKPOINTS.md` | REVIEWER, LEAD | Verifiable "done" criteria per project phase |
```

---

## Section 7 — One-Feature-at-a-Time Rule

**What it contains:** a single explicit constraint: only one feature may be
`in_progress` in `backlog.json` at any time.

**Why it merits its own section:** this is the single most important harness
constraint. It prevents context fragmentation, overlapping traces, and state
inconsistency. It must be visible at the top level — not buried in `leader.md`
where only LEAD reads it.

**Why it applies to DS projects specifically:** DS features often have implicit
dependencies (e.g., Spearman filter must come after imputation). Running two
features in parallel risks one IMPLEMENTER reading stale pipeline state from the
other.

```markdown
## One-Feature-at-a-Time Rule

Only one feature may have `status: "in_progress"` in `backlog.json` at any time.
LEAD enforces this at session start. If two features are `in_progress`, LEAD
must resolve the conflict before proceeding.
```

---

## Section 8 — Session Protocol

**What it contains:** three explicit steps for session start and session end.
No more.

**Why it matters:** Codex and Claude Code do not have persistent memory between
sessions. The session protocol is the mechanism that bridges context windows.
Without it, each session starts from scratch regardless of how good the harness
files are.

**Keep it to three lines each.** Detailed agent behavior belongs in `agents/leader.md`.

```markdown
## Session Protocol

**Start:**
1. LEAD reads `docs/memory/progress/current.md` and `docs/memory/backlog.json`.
2. LEAD reads `docs/architecture.md` if the active feature touches the pipeline.
3. LEAD decomposes the active feature into sub-tasks and updates `current.md`.

**End:**
1. LEAD marks completed sub-tasks in `current.md`.
2. LEAD updates `status` in `backlog.json` if the feature is done.
3. LEAD appends a session summary to `docs/memory/progress/history.md`.
```

---

## What Does NOT Belong in AGENTS.md

These are common mistakes that bloat AGENTS.md and break the progressive
disclosure principle:

| What to avoid | Why | Where it belongs instead |
|---|---|---|
| Detailed agent rules ("IMPLEMENTER must not edit backlog") | Only IMPLEMENTER needs it; bloats context for others | `agents/implementer.md` |
| Skill instructions | Only the invoking agent needs them; loaded on demand | `skills/<skill>/SKILL.md` |
| Project conventions (naming, imports, metrics) | Only IMPLEMENTER and REVIEWER need them | `docs/conventions.md` |
| ADR contents | Historical record, consulted not loaded | `docs/adr/` |
| Full pipeline description | Too long; only needed before a feature | `docs/architecture.md` |
| Anti-patterns list | Belongs in agent instructions | `agents/*.md` |
| Examples of outputs | Belongs in skills | `skills/*/example.*` |

---

## Full AGENTS.md Template for a DS Project

```markdown
# AGENTS.md

> Entry point for all AI agents. Read fully before any action. Follow pointers.

---

## Project Identity

- **Name:** <project name>
- **Type:** <regression / classification / other>
- **Primary metric:** <MAE / AUC-ROC / other>
- **Current phase:** <Developing / Production>
- **One-liner:** <what the model does and who uses it>

---

## Agents

| Agent | Role | Instructions |
|---|---|---|
| LEAD | Orchestrates sessions, owns state, writes ADRs and plans | `agents/leader.md` |
| IMPLEMENTER | Writes and runs code; produces artifacts | `agents/implementer.md` |
| REVIEWER | Quality gate: leakage, metrics, reproducibility | `agents/reviewer.md` |
| ADVISOR | DS/ML senior consultant; writes research reports on demand | `agents/advisor.md` |

---

## Skills

| Skill | Invoked by | Produces | Instructions |
|---|---|---|---|
| `ds-research-report` | ADVISOR | Technical report in `docs/research-reports/` | `skills/ds-research-report/SKILL.md` |
| `create-adr` | LEAD | Decision record in `docs/adr/` | `skills/create-adr/SKILL.md` |
| `function-conventions` | IMPLEMENTER | Code following project style | `skills/function-conventions/SKILL.md` |

---

## Memory

| File | Owner | Contains |
|---|---|---|
| `docs/memory/progress/current.md` | LEAD | Active session state |
| `docs/memory/progress/history.md` | LEAD (append-only) | Session log |
| `docs/memory/backlog.json` | LEAD | Feature backlog |
| `docs/memory/plans/` | LEAD | Exec plans |
| `docs/memory/progress/impl_<feature>.md` | IMPLEMENTER | Implementation trace |
| `docs/memory/progress/review_<feature>.md` | REVIEWER | Review trace |

---

## Docs

| File | Read by | Contains |
|---|---|---|
| `docs/architecture.md` | IMPLEMENTER, REVIEWER | Pipeline order, approved stack, src/ structure |
| `docs/conventions.md` | IMPLEMENTER, REVIEWER | Code style, naming, metrics |
| `docs/adr/` | All agents | Binding project decisions |
| `docs/research-reports/` | ADVISOR, LEAD | Prior technical explorations |
| `CHECKPOINTS.md` | REVIEWER, LEAD | Verifiable "done" criteria |

---

## One-Feature-at-a-Time Rule

Only one feature may have `status: "in_progress"` in `backlog.json` at any time.
LEAD resolves conflicts before proceeding.

---

## Session Protocol

**Start:**
1. LEAD reads `current.md` + `backlog.json`.
2. LEAD reads `architecture.md` if the active feature touches the pipeline.
3. LEAD decomposes the active feature and updates `current.md`.

**End:**
1. LEAD marks completed sub-tasks in `current.md`.
2. LEAD updates feature `status` in `backlog.json`.
3. LEAD appends session summary to `history.md`.
```

---

## DS-Specific Considerations

### Phase affects what IMPLEMENTER produces

AGENTS.md should make the current phase explicit because it changes the output
format of every IMPLEMENTER task:

- **Developing phase:** output is a Jupyter notebook cell or section in `notebooks/`.
  Code can be exploratory; sklearn.Pipeline not used; transformations are explicit
  and sequential.
- **Production phase:** output is a Python module in `<repo_name>/<repo_name>/`.
  Code must be refactored, testable, and follow all conventions in `docs/conventions.md`.

If the phase is not stated in AGENTS.md, IMPLEMENTER defaults to its own judgment
and produces the wrong artifact type.

### Tool-agnostic by design

AGENTS.md as described here works identically in Codex and Claude Code because:
- It contains no tool-specific syntax (no `.claude/` references, no Codex-specific tags).
- All pointers are relative file paths — valid in any environment where the repo is mounted.
- The session protocol is manual (LEAD reads files explicitly) — no dependency on
  tool-native memory or hook mechanisms.

If you later add tool-specific features (e.g., Claude Code hooks in `.claude/settings.json`),
those go in tool-specific config files, not in AGENTS.md.

### conventions.md vs architecture.md for DS

A common confusion in DS projects is what goes in each:

| Belongs in `conventions.md` | Belongs in `architecture.md` |
|---|---|
| Variable naming (`X_train`, `y_train`) | Pipeline step order |
| Primary / secondary metric definitions | Approved library stack with versions |
| Import style (no wildcard imports) | `src/` module structure |
| File format preferences (parquet over CSV) | Active ADRs list |
| Keyword-only function arguments rule | Train/val/test split ratios and strategy |
| No absolute paths rule | Data source locations and formats |
| Functional over OOP preference | Model class and hyperparameter baseline |

Both files are read by IMPLEMENTER and REVIEWER — but at different moments.
`conventions.md` is consulted when writing any code. `architecture.md` is consulted
before starting any feature that touches the pipeline.

---

## Diagnostics & Pitfalls

- **AGENTS.md grows over time** — if you find yourself adding rules or content
  beyond the 8 sections above, it is a signal that something belongs in a
  pointed-to file instead. Keep AGENTS.md under ~80 lines.
- **Stale phase** — if the project moves from Developing to Production and
  AGENTS.md still says "Developing", IMPLEMENTER will produce notebooks instead
  of modules. Update the phase field immediately on transition.
- **Missing skill ownership** — if a skill has no "Invoked by" entry, any agent
  may invoke it. Always specify ownership explicitly.
- **Memory section not updated after renaming** — if you rename a memory file,
  update AGENTS.md immediately. Agents will fail silently if the pointer is wrong.
- **Tool-specific content creeping in** — if AGENTS.md starts referencing
  `.claude/` or Codex-specific syntax, it breaks the tool-agnostic guarantee.
  Keep all tool-specific config in separate files.

---

## Decision Rule

1. Does every agent need this information at the start of every session? → **AGENTS.md**
2. Does only one agent need it? → `agents/<role>.md`
3. Is it a skill invocation rule? → `skills/<skill>/SKILL.md`
4. Is it a stable project reference (pipeline, stack, conventions)? → `docs/architecture.md` or `docs/conventions.md`
5. Is it live state that changes during sessions? → `docs/memory/`
6. Is it a binding project decision? → `docs/adr/`
7. Is it a technical exploration without a decision? → `docs/research-reports/`

---

## References

1. Anthropic — Claude Code agent documentation: https://docs.claude.ai/en/docs/claude-code/overview
2. betta-tech — ejemplo-harness-subagentes (progressive disclosure pattern): https://github.com/betta-tech/ejemplo-harness-subagentes
3. Michael Nygard — Documenting Architecture Decisions (ADR format origin): https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
4. MADR — Markdown Architectural Decision Records: https://adr.github.io/madr/
5. Kuhn & Johnson — Feature Engineering and Selection (pipeline structure reference): https://feat.engineering/
