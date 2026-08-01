# Template: Task planning prompt (for Claude Code)

> **What this is:** a template for writing the prompt for ONE task/feature inside a project
> already in motion (e.g. `src/etl/features/something.py`, a target, a customer perimeter). It
> is not a full project PRD (for that, see
> `playground/notes/product-requirement-document-in-data-science.md`) — this is the level of
> detail you need to give in chat before LEAD/Claude Code plans and implements one concrete
> pipeline step.
>
> **How to use it:** copy this file, don't edit the original in `playground/templates/`, fill
> in only the sections that apply and delete the rest — don't force empty sections. Order
> matters: context and objective first, so the agent understands the "why" before the "what".
> The `<!-- -->` lines are guidance, not part of the final prompt.

---

## Task: [short task name]
## Location: [target module/file path, e.g. `src/etl/features`]

## Context
<!--
What already exists and why this comes now: relevant ADRs already decided, prior artifacts
(tables, notebooks, variable lists) this step consumes or continues. If this task depends on
a decision already closed, name it explicitly (e.g. "now that we have
adr-2026-07-30-...") so the agent doesn't reopen it.
-->

## Objective
<!--
One or two sentences. What gets accomplished in THIS phase, and what is explicitly left for
a later phase (e.g. "raw features now, advanced feature engineering later"). Bounding the
task's scope in time keeps the agent from trying to solve the whole pipeline at once.
-->

## Inputs
<!-- Tables/samples/files to read and the role of each. -->
- `file.parquet`: [what it represents, at what grain — customer, loan, etc.]

## Parameters
<!--
Values that are fixed today but could change later (cutoff dates, windows in months,
thresholds). Declare them as explicit configurable parameters in the code, not hardcoded, and
note where the decision came from if it's backed by an ADR or is an assumption of yours.
-->
- `param_name = value`  <!-- source/reason, e.g. "defined in ADR", "assumption to validate" -->

## Logic / Requirements
<!--
Bullet-level detail of the expected logic, edge cases spelled out explicitly (what happens if
there isn't enough history, if there are duplicates, if two events land in the same month). If
you already have a rough query/pseudocode in mind, include it — it helps far more than
describing it in prose. Be explicit about design decisions and their reason, not just the what
but the why (e.g. "exclude customers in recent default because we don't know the current risk
policy").
-->
-

## Naming conventions
<!--
Only if this task creates new variables/columns. Naming should be self-explanatory about
timeframe and aggregation without opening the dictionary (e.g. `avg_salary_w3m_lag0` = average
of the last 3 months; `avg_debt_w3m_lag3` = same average but shifted 3 months back). If the
project already has a convention (see `docs/CONVENTIONS.md`), just reference it.
-->

## Explicitly out of scope
<!--
What the agent should NOT do in this task, even if it seems natural to include (e.g. "no
interactions or powers — keep it simple", "formal feature selection happens later, don't drop
columns here yet"). This is what most prevents scope creep.
-->
-

## Reusability
<!--
If the code should be built to be reused on other samples/perimeters later (e.g. "it should
also run on perimeter_w_target_12m"), say so explicitly — it changes how the
function/interface gets designed.
-->

## Expected validation / logging
<!--
What should be printed to console or notebook so you can verify the result without opening the
parquet: shape, min/max of dates (and which field was used to compute them), overall rates,
breakdown tables by period (with count() and countDistinct()).
-->

## Technical questions / open questions
<!--
Things you're not sure about and want the agent to resolve, confirm, or take to ADVISOR before
coding blind (e.g. "why is this variable in post_origination_leakage?").
-->
-

## Review
<!--
If this task touches leakage, statistical validation, or methodology decisions, explicitly ask
for it to be reviewed in depth with ADVISOR before the plan is considered final.
-->

## Expected output
<!--
Concrete deliverables and their names, one per line — this is the baseline, not a hard ceiling.
The agent has license to propose additional outputs beyond this list, or a better version of
what's listed here, if something clearly relevant surfaces during planning (e.g. a diagnostic
table, a dictionary, a sanity-check notebook). Any such addition should be flagged explicitly
and justified, not slipped in silently — you decide whether to keep it.
-->
- [ ]
