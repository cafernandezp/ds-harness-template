---
name: explanation-report
description: >-
  Produce a human-readable, example-driven walkthrough of how a specific
  already-built pipeline/flow/mechanism in this codebase actually works — a
  Mermaid data-flow diagram with sourced numbers, one consistent worked
  example traced through every step, and a small glossary. Use this skill
  WHENEVER the user asks to understand or get a step-by-step explanation of
  something already built, e.g. "necesito entender", "explícame el flujo",
  "paso a paso", "con ejemplos", "quiero un diagrama de cómo fluyen los
  datos", "walk me through", "explain step by step", "how does X work". This
  is NOT for recording a decision (see create-adr) and NOT for comparing
  options/methods (see ds-research-report) — it's for explaining a mechanism
  that already exists. Also use it to UPDATE an existing explanation-report
  so it stays in sync with the real, current code.
---

# Skill: explanation-report

Generates a single **`.md` file** saved to `docs/explanation-reports/`, prefixed `er-`. The goal is
a document a human can read once and come away actually understanding a mechanism — not a spec, not
a decision record, a **walkthrough**. See `example.md` in this folder for a full worked example of
the required depth and rigor — a real explanation-report from a credit-risk feature-engineering
pipeline, trimmed to 3 representative families. Its *domain* (loans, prior-loan aggregation) is
incidental — on an unrelated project, ignore the vocabulary and copy the *shape*: the diagram +
bullets + glossary pattern in §0, the single core rule in §1, one example threaded through every
family with a visibly different null-policy per family in §3, the cross-cutting summary table in
§4, the excluded-and-why list in §5, and the code-location map in §6. Read it before producing a
new explanation-report.

## When to use

- The user wants to understand **how** something already built works, with a clear mental model and
  concrete numbers — not which option to pick (`ds-research-report`) and not a decision to persist
  (`create-adr`).
- Trigger phrases: "necesito entender esto muy bien", "explícame el flujo", "paso a paso", "con
  ejemplos", "un diagrama de cómo fluyen los datos", "walk me through", "explain step by step", "how
  does X actually work".
- Also use to **update** an existing explanation-report after the underlying code changes — an
  explanation-report that silently drifts out of sync with the code it describes is worse than none.

## Output contract

- Deliver a single **`.md` file** in `docs/explanation-reports/`, filename prefixed `er-` (e.g.
  `er-feature-engineering-numeric.md`). Do not dump the whole document into chat — write the file,
  then give a short chat summary.
- **Always written in English**, regardless of the language the user writes in — matches every other
  docs-producing skill in this project.
- Style: concise, example-driven, tables and bullets over prose wherever the content is enumerable.

## Sections

### Always include (in this order)

1. **Header quote block** — one short paragraph stating scope, plus pointers to the binding spec /
   ADR / plan this explains (if any exist) and to the exhaustive machine-readable reference (a
   dictionary CSV, the source code itself) if one exists. This document complements those — it does
   not replace or duplicate their content.
2. **`## 0. Data flow`** — a single Mermaid `flowchart TD` (see "Diagram rules" below), followed
   immediately by concise **bullet-point** takeaways (never a prose paragraph), followed by a small
   `### Glossary` of any non-obvious term the diagram or the rest of the document uses.
3. **`## 1. The one thing to understand before anything else`** — the single core mental model or
   rule the reader needs before any further detail makes sense.
4. **Worked example** — introduce ONE synthetic-but-labeled example (named entities — a customer,
   an order, a record — not "Example 1"/"Example 2") early, then trace it through **every**
   component/step described in the rest of the document. Never a different example per section —
   the entire point is that a reader can follow one thread start to finish.
5. **Per-component/family sections** — one per step/engine/stage in the flow. Each gets: a
   **Criterion** paragraph (the exact rule/formula, read from the real source code, never
   paraphrased from memory or an older planning doc) + a table applying that criterion to the one
   worked example, with real, hand-computed numbers.
6. **`## What's deliberately excluded`** — anything a reader might reasonably expect to find but
   won't, and why. Cross-reference the relevant ADR(s) if one governs the exclusion; do not
   reproduce its content, link to it.
7. **`## Where each piece lives in code`** — a table mapping every component/family discussed to its
   real source file path. Verify every path against the actual repo before writing it down — never
   infer a path from naming convention alone.

### Include when applicable

- **Naming convention section** — only if the topic has one worth spelling out explicitly (e.g. a
  systematic feature-name or file-name pattern).
- **Cross-cutting summary table(s)** — when something recurs across components and is easy to get
  wrong (e.g. a null-policy table, a status-transition table, a timing-window table).
- **Execution-order section** (`## 0.5` or similar) — when "what runs first" isn't obvious from the
  §0 dependency graph alone. §0 shows what data feeds what; this section answers the *different*
  question of what a reader debugging cold actually runs, in order, with file:line references —
  useful whenever there's a single entry point calling several internal steps in a fixed sequence
  that the dependency graph doesn't make explicit.

## Diagram rules (Mermaid `flowchart TD`)

- Prefer a **flat graph** over nested `subgraph` blocks unless a subgraph demonstrably reduces
  crossing edges — subgraphs often make the automatic layout *worse*, not better, once edges have to
  cross the subgraph boundary.
- Every node label: `<br/>`-separated lines. Component nodes get file/module name, then a short
  description, then the size/count **on its own line** (`"228 cols"` on its own line, not folded
  into the description with an em-dash).
- Input/source nodes additionally get, each **on its own line**: the relevant date field's name and
  min/max range, the total row count, and the total unique-entity count (e.g. unique customers) —
  so the diagram doubles as a review/sanity-check artifact, not just an illustration.
- If something is banned/excluded from the flow (e.g. a leakage-column bucket), fold it into the
  relevant node's own label as an extra line (`"excludes: X, N cols, never used"`) instead of a
  separate node connected by a dashed cross-cutting edge — a standalone excluded-node usually adds
  visual clutter without adding clarity.
- Declare nodes in an order that keeps sources near their immediate consumers — this measurably
  helps the automatic layout even though it isn't a hard positioning guarantee.

## Number provenance (non-negotiable)

Every number in the diagram or the worked example must be traceable to one of:

1. **An existing log line** under `reports/**/*.log` — cite the exact log file in a "Number
   provenance" note under the diagram.
2. **An already-reviewed trace** (`docs/memory/progress/impl_*.md`, `review_*.md`, `current.md`,
   `history.md`) — cite which one.
3. **A fresh, deterministic read of an already-shipped, reviewed artifact** (e.g. `.nunique()` on a
   column of an approved parquet) — allowed **only** when 1–2 don't have the number, and it **must**
   be marked with a `*` in the diagram plus a short provenance note naming exactly which figures are
   fresh-computed and why no log covers them yet.

Never blend log-sourced and freshly-computed numbers without marking which is which — a reader using
this document to sanity-check a pipeline needs to know whether a number is an audited fact or a
one-off check run for this document.

## Worked-example rigor

- Hand-verify every calculation against the actual source code — read the real function, don't
  reconstruct the formula from memory or from an earlier planning document (plans can drift or
  contain arithmetic typos; the shipped code is ground truth).
- Design the example to hit the *interesting* edges on purpose: a boundary case (e.g. exactly at a
  window cutoff), a "same period, doesn't count" case, and a "no history / undefined" case are
  usually worth engineering into the synthetic data deliberately, not left to chance.

## Style checklist (run before presenting)

- [ ] Single Mermaid `flowchart TD`, node labels multi-line with counts/sizes on their own line, no
      unnecessary `subgraph` clutter.
- [ ] Every diagram/example number is either log/trace-sourced (cited) or marked `*` with a
      provenance note explaining why.
- [ ] Bullet points directly under the diagram, not a prose paragraph.
- [ ] Small glossary present for any non-obvious term.
- [ ] Exactly ONE worked example, reused across every section — not a different example per section.
- [ ] Every formula/criterion was read from the real, current source file, not reconstructed from
      memory or an older planning document.
- [ ] "What's deliberately excluded" section present if the topic has real exclusions.
- [ ] Code-location table present, every path verified to actually exist in the repo.
- [ ] Written in English; delivered as a file + short chat summary, not dumped inline.
- [ ] Filename prefixed `er-`, saved under `docs/explanation-reports/`.

## Example trigger → action

**Input:** "necesito entender muy bien cómo se arman estas features, con ejemplos" (about a
feature-engineering pipeline already built in `src/`).

**Output:** `docs/explanation-reports/er-<topic>.md` containing: a Mermaid data-flow diagram with
real, sourced input stats and a provenance note for anything not logged; concise bullets and a small
glossary under it; one named synthetic example traced through every engine/step with hand-verified
numbers; a null-policy-style (or equivalent) summary table; a "what's excluded" section citing the
relevant ADR; a code-location table — delivered as a file plus a short chat summary, in English.
