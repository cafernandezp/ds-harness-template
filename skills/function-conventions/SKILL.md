---
name: function-conventions
description: >-
  Rubric for function-level code style: argument naming (df, seed),
  docstring depth, when to extract a helper, and when the ≤4-args
  keyword-only guideline applies. Consult before writing or reviewing any
  function in src/ — activate whenever CONVENTIONS.md section 8 (Function
  signatures) applies, or the user asks about argument naming, docstring
  depth, helper extraction, or function-signature style in this repo.
---

# Function Conventions

Consulted by IMPLEMENTER when writing any function, and by REVIEWER when
checking it. Covers argument naming, docstring depth, and when a strict
argument-count guideline applies versus when it doesn't — the concrete
rubric and worked examples behind the project's general function-style
conventions.

## 1. Argument naming

- A single DataFrame argument is always named `df` — never `data`,
  `input_df`, or `dataframe`. (This is separate from any fixed names used
  for split data, like `X_train`/`y_train` — those follow whatever
  train/test naming convention the project already has; `df` is for a
  generic single frame outside that context.)
- Any argument controlling randomness is always named `seed` — never
  `random_state`, `rng`, or `random_seed`, even though the value usually
  comes from `config.random_state`.
- Exception: when calling a third-party function that itself expects a
  parameter with a different name (e.g. pandas' `.sample(random_state=...)`,
  sklearn's `train_test_split(random_state=...)`), use that library's own
  parameter name at the call site. Renaming a third-party API isn't ours
  to do — only our own function signatures use `seed`.

## 2. Docstring depth — calibrated to what the function does

- A function with real logic (more than a couple of lines, non-trivial
  branching, or anything public in `src/lib/`) gets a full docstring:
  one-line purpose, `Args`, `Returns`.
- A small internal helper (usually prefixed with `_`, called from exactly
  one place, a line or two of code) only needs a single short sentence
  describing what it does — no `Args`/`Returns` breakdown. A full
  docstring on a two-line helper adds more text than the function itself.

## 3. Prefer simple code over many small helpers

- Don't extract a helper function unless the logic is duplicated in more
  than one place, or a block is long/complex enough that naming it
  actually improves readability.
- A helper called from exactly one place and only 1-2 lines long should
  usually just be inlined instead of extracted.

## 4. When the "≤4 args, keyword-only" guideline applies

- Applies to: pure functions — take data in, return a transformed result,
  no side effects (no file writes, no logging, no orchestrating other calls).
- Does not apply to: orchestration or logging functions that legitimately
  bundle several related values together as part of their job (e.g. a
  function that logs a run and needs a name, parameters, metrics, and
  artifacts all together).

See `example.py` in this folder for a worked example covering all four points.
