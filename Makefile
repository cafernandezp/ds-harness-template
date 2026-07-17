.PHONY: install install-dev install-all install-clean install-reset \
        lint lint-fix format format-check test

# ---------------------------------------------------------------- install ---

# Standard install: reads pyproject.toml + uv.lock, creates .venv,
# installs the project editable. Idempotent.
install:
	uv sync

# With dev tools (pytest, ruff).
install-dev:
	uv sync --group dev

# Everything: dev + notebooks + experiments.
install-all:
	uv sync --all-groups

install-clean:
	rm -rf .venv

install-reset: install-clean install

# ------------------------------------------------------------------ quality -

# Check-only: non-zero exit on any violation. CI-safe.
lint:
	uv run ruff check .

# Local convenience: applies safe autofixes.
lint-fix:
	uv run ruff check --fix .

# Rewrites files in place.
format:
	uv run ruff format .

# Check-only formatting: non-zero exit if files would change. CI-safe.
format-check:
	uv run ruff format --check .

# --------------------------------------------------------------------- run --

# run:
# 	uv run python -m your_package.main

# -------------------------------------------------------------------- test --

test:
	uv run pytest
