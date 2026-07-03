.PHONY: install-init install-clean install-reset

install-init:
	uv init --python 3.12
	uv add "numba>=0.60" "llvmlite>=0.43" pandas numpy scikit-learn xgboost lightgbm shap scipy statsmodels joblib seaborn matplotlib click fastapi torch
	uv add --dev pytest ruff
	uv add --group notebooks ipykernel jupyter
	uv add --group experiments mlflow optuna

install-clean:
	rm -rf .venv
	rm -f pyproject.toml
	rm -f uv.lock
	rm -f .python-version

install-reset: install-clean install-init