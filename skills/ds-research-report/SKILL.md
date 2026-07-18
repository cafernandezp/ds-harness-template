---
name: ds-research-report
description: >-
  Produce technical data-science / machine-learning research reports as downloadable Markdown
  artifacts with a fixed, rigorous structure. Use this skill WHENEVER the user asks for a
  "report", "reporte", "research report", "detailed write-up", "deep dive", "comparison of
  methods/strategies", "cheatsheet", or a structured technical document about a DS/ML/stats topic
  (e.g. feature engineering, encoding strategies, model comparison, evaluation, statistics) —
  even if they don't say the word "report" explicitly. Trigger it any time the deliverable is a
  multi-section technical document rather than a quick inline answer. Also use it to UPDATE an
  existing report so the mandatory sections and conventions stay consistent.
---
 
# DS/ML Research Report
 
Generates rigorous, skimmable technical reports as **Markdown artifact files** (not inline chat).
The goal is a document the user can save, share, and trust: correct, current, well-sourced, and
consistently structured.
 
## When to use
 
- User wants a report / reporte / detailed write-up / deep dive / cheatsheet on a DS/ML/stats topic.
- User asks to **compare strategies, methods, or models** (the comparison itself is the report).
- User asks to **update or extend** a report already produced this way — keep the same conventions.
If the user only wants a quick conceptual answer with no deliverable, answer inline instead; don't
force a report.
 
## Output contract
 
- Deliver a single **`.md` file** written to `docs/research-reports/`, then present it. Do not dump
  the full report into the chat; give a short summary + the file.
- **Filename MUST be prefixed `rr-`** (e.g. `rr-encoding-strategies.md`).
- **Both the report and the chat summary are ALWAYS written in English**, regardless of the
  language the user writes in.
- Style: **professional, direct, minimal**. Bullets and compact notation over prose. No filler, no
  restating the prompt, no marketing tone.
- Per-claim structure inside sections follows **Answer → Why → How to apply / verify** (only the
  parts that add value).
## Mandatory sections (in this order)
 
ALWAYS include these. Omit one only if clearly irrelevant, and say why.
 
1. **Title** — `# <topic> — <scope/qualifier>`.
2. **Context box** — a top blockquote stating the concrete problem, key assumptions, and constraints
   (model, data shape, target type, metric). State assumptions explicitly and proceed.
3. **TL;DR / Recommendation** — the ranked, actionable bottom line first (3–6 bullets).
4. **Comparison table** — when ≥3 options/methods are discussed: one row per option, columns for the
   axes that drive the decision (cost, risk, when to use, suitability for the user's setup).
5. **Per-option / per-method sections** — one `##` per option. **Each section MUST contain:**
   - **What** it is — 1–3 lines.
   - **Pros** — bullet list of concrete benefits.
   - **Risks** — bullet list of failure modes, leakage risks, costs, caveats.
   - **How / verify** — minimal working code block (see Code rules) and/or verification steps.
   - **Critique when warranted** — if a method is popular but a poor fit for the stated problem,
     say so explicitly and explain why (don't silently omit it; address it and dismiss it on merit).
6. **Problem-specific considerations** — implications of the user's exact setup (target type, metric,
   model family, scale).
7. **Diagnostics & pitfalls** — sanity checks, failure modes, and especially **data-leakage** risks
   and train/validation/test separation.
8. **Decision rule / quick guide** — a numbered "if X → do Y" list.
9. **References** — ALWAYS the LAST section. Numbered list of the sources actually used, with full
   URLs. Never end a report without it. If a claim isn't sourced or derivable, drop the claim.
## Rigor requirements
 
- **Verify current facts before writing.** Library APIs, version behavior, parameter names, current
  model lineups, and defaults drift. Web-search the official docs for anything version-dependent
  (e.g. scikit-learn / XGBoost / pandas parameters) and cite them in **References**. Do not assert
  version-specific behavior from memory.
- When relevant, state the **objective/loss**, key **assumptions**, the **decision rule/estimator**,
  and minimal correct **core equations**.
- Be explicit about **leakage** and **train/val/test** separation wherever encoders, scalers, or
  target-derived features appear.
- Note **calibration** and proper **metric choice** when probabilities or bounded targets matter.
## Code rules (when including code)
 
- Minimal working example per method, in a single fenced block. **Procedural/functional**, not OOP.
- Standard stack first: `numpy`, `pandas`, `scikit-learn`; `xgboost` for XGBoost; `torch` for nets.
- Fixed `random_state`; minimal imports; brief comments only where they add clarity.
- Prefer **leakage-safe** patterns: fit on train only, wrap target-derived encoders inside a
  `Pipeline`/CV. Show the safe pattern, not the convenient-but-leaky one.
- Add a tiny usage example when it fits.
## Style checklist (run before presenting)
 
- [ ] Context box present with assumptions + constraints.
- [ ] TL;DR is first and actionable.
- [ ] Comparison table present if ≥3 options.
- [ ] Every method section has **What / Pros / Risks / How**.
- [ ] Popular-but-ill-fitting methods are critiqued, not omitted.
- [ ] Leakage / train-test separation addressed.
- [ ] **References** is the final section, numbered, with URLs.
- [ ] Version-specific claims were web-verified and cited.
- [ ] Report is written in English (even if the user wrote in another language); tone is minimal and direct.
- [ ] Delivered as a `.md` file + short chat summary (not the whole report inline).
- [ ] Filename prefixed `rr-`.
## Section template (copy and fill)
 
```markdown
## <Method name>  *(optional one-line qualifier)*
 
**What.** <one to three lines>
 
**Pros.**
- <benefit>
- <benefit>
 
**Risks.**
- <failure mode / leakage / cost / caveat>
- <caveat>
 
**How / verify.**
​```python
# minimal, procedural, leakage-safe, fixed random_state
​```
```
 
## Example trigger → action
 
**Input:** "Give me a detailed report comparing encoding strategies for high cardinality."
**Output:** An **English** `.md` report (even if the prompt were in another language) with context
box, TL;DR, comparison table, one section per strategy (What/Pros/Risks/How), a critique of
strategies that don't fit the stated model/target, diagnostics, a decision rule, and a final
**References** section with web-verified doc links — delivered as a file plus a short chat summary,
also in English.
