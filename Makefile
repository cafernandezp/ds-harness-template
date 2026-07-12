.PHONY: install install-dev install-all install-clean install-reset

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