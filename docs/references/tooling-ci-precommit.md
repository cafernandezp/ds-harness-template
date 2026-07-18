# Tooling: pre-commit and CI

> Personal note to re-read once the project enters production phase and it's
> time to decide whether to enable CI. Current phase: early development — CI
> deliberately removed from the template; pre-commit stays active.

---

## `.pre-commit-config.yaml`

### What it is

Config for the [pre-commit](https://pre-commit.com/) framework — orchestrates
Git hooks. On `git commit`, Git runs local hooks before creating the commit.
If a hook fails, the commit doesn't happen.

### How it works

1. `uv run pre-commit install` — once per clone. Writes
   `.git/hooks/pre-commit` pointing at the framework.
2. Every `git commit` → framework reads the yaml → runs the listed hooks
   over staged files.
3. Hooks that **modify** (ruff `--fix`, `ruff-format`, `end-of-file-fixer`)
   rewrite the file. The commit aborts with "files were modified" → re-stage
   and re-commit once clean.
4. Hooks that **only validate** (`check-yaml`, `check-toml`) fail if the file
   is malformed.

### When it runs

- Every local commit, automatically.
- Manual, repo-wide: `uv run pre-commit run --all-files` (useful the first
  time or after changing config).

### What it's for in this template

- Rejects commits with trailing whitespace, missing final newline,
  malformed yaml/toml, files >1MB (prevents accidentally committing data).
- Ruff format + `--fix` normalize style before the diff reaches the
  remote → clean PRs, reviewer doesn't have to argue about formatting.

### Alternative if you don't want it

Delete the file. You lose commit-time autofix — ruff/format only run when
called by hand or in CI.

---

## `.github/workflows/ci.yml`

### What it is

A GitHub Actions workflow. On every push/PR, GitHub spins up a Linux
runner and executes the steps in the yaml. Green ✅ / red ❌ on the PR.

### What this one would specifically do

1. Checkout the repo.
2. Install `uv` with dependency caching.
3. Python 3.12.
4. `uv sync --group dev`.
5. `ruff check .` — lint.
6. `ruff format --check .` — verifies formatting without modifying.
7. `pytest` (with a shim that tolerates "no tests collected" while the
   template ships without tests).

### Is it necessary during development phase?

Depends on the working mode:

| Scenario | CI adds |
|---|---|
| Just you, one branch, no PRs, fast iteration in notebooks | Little. Local pre-commit covers 90%. |
| Multi-agent writing code (IMPLEMENTER, LEAD doing quick-fixes) | Yes — safety net against an agent skipping pre-commit or committing without it installed. |
| PRs, human reviewer, or repos others will clone | Yes — objective signal before merge. |
| Public template / one others fork | Yes — proves it boots on a clean machine. |

### Arguments against CI in early development

- Slower feedback loop (minutes vs. seconds for pre-commit).
- Requires a GitHub Actions account with available minutes.
- In a pure-experimentation DS project, ruff+pytest in CI doesn't catch
  what actually matters (leakage, miscalculated metrics — that's
  REVIEWER's job, not CI's).

### Arguments for it even in development

- Day-1 of the template is the cheapest time to add it. Adding it later
  risks it never happening.
- Agents can `--no-verify` or commit without pre-commit installed. CI is
  the real enforcement.
- Serves as executable documentation: "this is how the repo boots on a
  clean machine."

### Pragmatic recommendation

Keep it. If the noise is annoying, comment out the `push` trigger and
keep only `pull_request` — that way it only runs when you open a PR, zero
cost on commits to the working branch.

---

## When to revisit this

Turn CI back on when any of these happen:

- First code lands under `src/inference/` (production → tests become
  mandatory per CONVENTIONS §13, and without CI there's no remote
  enforcement).
- A second person starts collaborating on the repo.
- The first real PR is opened (no more direct commits to main).
- The project goes public / is shared with external stakeholders.

---

## Retired `ci.yml` content (to restore)

Save as `.github/workflows/ci.yml`:

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.12

      - name: Sync dev dependencies
        run: uv sync --group dev

      - name: Ruff check
        run: uv run ruff check .

      - name: Ruff format check
        run: uv run ruff format --check .

      - name: Pytest
        # `|| code=5` treats "no tests collected" as success — the template
        # ships without tests. Remove this fallback once tests exist.
        run: |
          uv run pytest || code=$?
          if [ "${code:-0}" = "5" ]; then exit 0; else exit ${code:-0}; fi
```

Before restoring: check the action versions (`checkout@v4`, `setup-uv@v3`)
— they'll be outdated by then.
