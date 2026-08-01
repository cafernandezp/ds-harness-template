# docs/explanation-reports/

Example-driven walkthroughs of already-built mechanisms/flows by LEAD. A
Mermaid data-flow diagram, one worked example traced through every step, and
a small glossary — for a reader who needs to actually understand how
something already-built works, not decide between options or record a
decision.

## Rules

- One file per topic: `er-<slug>.md`.
- Written exclusively by LEAD via the `explanation-report` skill
  (`skills/explanation-report/SKILL.md`), consulting ADVISOR on demand for
  the technical judgment calls inside it.
- Always written in English, regardless of chat language.
- Explains a mechanism that **already exists** — not a comparison of options
  (`docs/research-reports/`) and not a decision to persist (`docs/adr/`).
- Update in place when the underlying code changes — a stale
  explanation-report is worse than none.
