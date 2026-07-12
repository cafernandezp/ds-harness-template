# docs/adr/

Architecture Decision Records. Binding project decisions that persist
beyond the current feature — algorithm choices, evaluation protocols,
data strategies, anything future agents must inherit without reopening.

## Rules

- One file per decision: `adr-YYYY-MM-DD-<slug>.md`.
- Written exclusively by LEAD via the `create-adr` skill
  (`skills/create-adr/SKILL.md`).
- Mandatory sections and frontmatter: see the skill file.
- Never mix a research report and an ADR in the same file. Research
  report = options explored. ADR = decision made.
- Consult before reopening any decision this ADR covers.

## Status field

`accepted` · `superseded` · `deprecated`

When superseding an older ADR, set `supersedes:` in the new one's
frontmatter, and flip the old one's status to `superseded` — do not
delete the old file.
