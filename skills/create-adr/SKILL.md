---
name: create-adr
description: >-
  Generate a binding Architecture Decision Record (ADR) as a Markdown file in docs/adr/.
  Activate whenever the user says "crea un ADR", "create an ADR", "escribe un ADR",
  "write an ADR", or any equivalent phrasing in Spanish or English.
  ADRs document project decisions that persist beyond the current feature — algorithm
  choices, data strategies, evaluation protocols, or any call that future agents or
  developers must inherit without reopening.
---

# Skill: create-adr

Generates a single **`.md` file** saved to `docs/adr/` following the canonical structure
below. The file is the authoritative record; chat output is a short confirmation only.

---

## When to activate

Activate this skill when:
- User says "crea un ADR", "create an ADR", "escribe un ADR", "write an ADR", or similar.
- LEAD decides to record a project decision after reviewing a research report or
  discussion.
- A decision persists **beyond the current feature** and future agents must inherit it.

Do NOT activate for:
- One-off implementation choices (those go in `impl_<feature>.md`).
- Technical explorations without a decision (those go in `docs/research-reports/`
  via the `ds-research-report` skill).
- Conceptual questions answered in chat.

**Rule:** research report = options explored, no decision. ADR = decision made, reasons
documented. Never mix the two in the same file.

---

## Output contract

- **File:** `docs/adr/adr-YYYY-MM-DD-<slug>.md`
  - `YYYY-MM-DD`: today's date (ISO format).
  - `<slug>`: 2–5 lowercase words joined by hyphens that identify the decision
    (e.g. `stratified-kfold`, `target-encoding-strategy`, `backward-selection-1se`).
- **Language:** always English, regardless of the language the user writes in.
- **Length:** complete but concise. Each section gets what it needs — no padding,
  no repetition of the title in prose.
- **Deliver:** write the file, then add a one-paragraph chat summary in
  English. Do not dump the full ADR in chat.

---

## File naming convention

```
docs/adr/adr-YYYY-MM-DD-<slug>.md
```

Examples:
- `docs/adr/adr-2026-06-08-backward-selection-1se.md`
- `docs/adr/adr-2026-06-18-stratified-kfold.md`
- `docs/adr/adr-2026-07-01-target-encoding-strategy.md`

---

## Mandatory frontmatter

Always open the file with this YAML block:

```yaml
---
title: "<MacroTopic>: <specific topic>"
date: YYYY-MM-DD
status: accepted          # accepted | superseded | deprecated
author: LEAD
research_report: ""       # path to docs/research-reports/ if one exists; else ""
supersedes: ""            # path to older ADR if this replaces one; else ""
related_features: []      # list of FEAT-XXX ids this decision governs
---
```

---

## Mandatory sections (in this order)

Every ADR must contain exactly these six sections. Do not add, remove, or reorder them.

### 1. Title  `#`
Format: `# <MacroTopic>: <specific topic>`

The macro-topic is the broad area (e.g. Feature Selection, Cross-Validation Strategy,
Model Architecture, Data Encoding). The specific topic is the concrete decision
(e.g. Conservative 1-SE Rule, StratifiedKFold with 5 Folds).

### 2. Context  `## Context`
- What problem or question triggered this decision.
- Relevant facts about the project setup (model type, metric, data characteristics).
- Why a decision was needed at this point.
- Keep to 3–6 sentences; no alternatives here.

### 3. Alternatives  `## Alternatives`
- One subsection `###` per alternative considered.
- Each alternative: name in bold, then a compact description, pros, and cons/risks.
- If a research report covers this in depth, reference it and summarize; don't duplicate.
- Minimum two alternatives; maximum whatever was actually considered.

### 4. Decision  `## Decision`
- State what was chosen, in one clear sentence at the top.
- Then explain why: the reasoning that connects the project context to this option.
- Be specific — "because it fits our metric/context/constraint" not "because it is better."
- This is the most important section; give it the space it deserves.

### 5. Consequences  `## Consequences`
Two subsections:
- `### Positive` — concrete benefits.
- `### Negative` — concrete costs, tradeoffs, or limitations.
No hedging language; state tradeoffs plainly.

### 6. Advice  `## Advice`
- Practical guidance for future agents or developers who inherit this decision.
- Warn against common mistakes related to this decision.
- Flag conditions under which this decision should be revisited.
- Keep as a bullet list; 2–5 items.

---

## Section template (copy and fill)

```markdown
---
title: "<MacroTopic>: <specific topic>"
date: YYYY-MM-DD
status: accepted
author: LEAD
research_report: ""
supersedes: ""
related_features: []
---

# <MacroTopic>: <Specific Topic>

## Context
<!-- 3–6 sentences: what triggered this decision and what the project context is. -->

## Alternatives

### Alternative 1: <Name>
<!-- Description, pros, cons. -->

### Alternative 2: <Name>
<!-- Description, pros, cons. -->

## Decision
<!-- One sentence stating the choice, then the reasoning. -->

## Consequences

### Positive
- <!-- benefit -->
- <!-- benefit -->

### Negative
- <!-- cost or tradeoff -->
- <!-- cost or tradeoff -->

## Advice
- <!-- practical tip for future agents/developers -->
- <!-- when to revisit this decision -->
```

---

## Style rules

- Write in English always.
- No filler ("It is worth noting that…", "In conclusion…").
- Bullet lists over prose in Consequences and Advice.
- Alternatives may use short prose + bullets — whatever is clearest.
- If a number exists (threshold, split ratio, SE formula), include it explicitly.
- Cross-reference the research report if one exists; do not reproduce its content.

---

## Checklist (run before presenting)

- [ ] Frontmatter complete with date, status, and slug.
- [ ] Title follows `MacroTopic: specific topic` format.
- [ ] All six sections present in correct order.
- [ ] Decision section opens with one unambiguous sentence stating the choice.
- [ ] At least two alternatives documented.
- [ ] Consequences split into Positive and Negative.
- [ ] Advice contains at least one "when to revisit" bullet.
- [ ] File saved to `docs/adr/adr-YYYY-MM-DD-<slug>.md`.
- [ ] Chat summary written in English.

---

## Example trigger → action

**User says:** "Create an ADR about the conservative 1-SE rule for backward selection."

**Agent action:**
1. Reads any relevant research report in `docs/research-reports/` on the topic.
2. Builds the ADR with the six sections, filling the Decision from the project context.
3. Saves to `docs/adr/adr-<today>-backward-selection-1se.md`.
4. Writes a one-paragraph summary in English confirming what was decided and where the file lives.

