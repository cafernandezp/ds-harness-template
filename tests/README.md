# tests/

Test suite. Mirrors the `src/` layout by relative path — a test for
`src/inference/perimeter/apply.py` lives at
`tests/inference/perimeter/test_apply.py`.

## Scope (see `docs/CONVENTIONS.md` §13)

Tests are **not required** in the development phase (`src/etl/`,
`src/models/`). This code churns fast; the cost of maintaining tests
outweighs the benefit.

Tests are **mandatory** once code enters production:

- Every module under `src/inference/`.
- Every `src/lib/` function that `src/inference/` code imports
  (directly or transitively).

## Running

```bash
uv run pytest          # all tests
uv run pytest tests/lib/test_paths.py::test_repo_root   # single test
```

## Layout

Add subfolders only when the first test in that area is written — do
not scaffold empty mirror directories.
