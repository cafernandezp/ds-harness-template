import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def nadeau_bengio_se(scores, n_train, n_test):
    scores = np.asarray(scores)

    assert len(scores) > 1, "Se necesitan al menos 2 scores para calcular varianza."
    assert n_train > 0, "n_train debe ser > 0."
    assert n_test > 0, "n_test debe ser > 0."

    J = len(scores)
    s2 = np.var(scores, ddof=1)

    return np.sqrt((1.0 / J + n_test / n_train) * s2)


def _regression_metrics(y_true, y_pred, success_threshold):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    finite_mask = np.isfinite(y_true) & np.isfinite(y_pred)
    n_obs = int(finite_mask.sum())
    n_excluded_non_finite = int((~finite_mask).sum())

    _nan_result = {
        "mae": np.nan,
        "rmse": np.nan,
        "mse": np.nan,
        "mape": np.nan,
        "smape": np.nan,
        "mdape": np.nan,
        "rmspe": np.nan,
        "r2": np.nan,
        "success_rate": np.nan,
        "mae_p10": np.nan,
        "rmse_p10": np.nan,
        "mse_p10": np.nan,
        "mape_p10": np.nan,
        "smape_p10": np.nan,
        "mdape_p10": np.nan,
        "rmspe_p10": np.nan,
        "r2_p10": np.nan,
        "success_rate_p10": np.nan,
        "n_obs": n_obs,
        "n_excluded_non_finite": n_excluded_non_finite,
    }

    if n_obs == 0:
        return _nan_result

    y_true = y_true[finite_mask]
    y_pred = y_pred[finite_mask]
    error = y_true - y_pred
    abs_error = np.abs(error)
    squared_error = error**2

    # R²
    ss_res = np.sum(squared_error)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan

    # APE-based (mape, mdape, rmspe)
    nonzero_mask = y_true != 0
    if nonzero_mask.any():
        ape = np.abs(error[nonzero_mask] / y_true[nonzero_mask])
        mape = float(np.mean(ape))
        mdape = float(np.median(ape))
        rmspe = float(np.sqrt(np.mean(ape**2)))
        mape_p10 = float(np.percentile(ape, 10))
        mdape_p10 = mape_p10
        rmspe_p10 = mape_p10
    else:
        mape = mdape = rmspe = np.nan
        mape_p10 = mdape_p10 = rmspe_p10 = np.nan

    # SMAPE-based
    denom = np.abs(y_true) + np.abs(y_pred)
    smape_mask = denom > 0
    if smape_mask.any():
        per_obs_smape = 2.0 * np.abs(error[smape_mask]) / denom[smape_mask]
        smape = float(np.mean(per_obs_smape))
        smape_p10 = float(np.percentile(per_obs_smape, 10))
    else:
        smape = smape_p10 = np.nan

    # Success rate
    flag_success = (abs_error <= success_threshold).astype(float)

    return {
        "mae": float(np.mean(abs_error)),
        "rmse": float(np.sqrt(np.mean(squared_error))),
        "mse": float(np.mean(squared_error)),
        "mape": mape,
        "smape": smape,
        "mdape": mdape,
        "rmspe": rmspe,
        "r2": r2,
        "success_rate": float(np.mean(flag_success)),
        # P10 variants
        "mae_p10": float(np.percentile(abs_error, 10)),
        "rmse_p10": float(np.percentile(abs_error, 10)),
        "mse_p10": float(np.percentile(squared_error, 10)),
        "mape_p10": mape_p10,
        "smape_p10": smape_p10,
        "mdape_p10": mdape_p10,
        "rmspe_p10": rmspe_p10,
        "r2_p10": np.nan,
        "success_rate_p10": float(np.percentile(flag_success, 10)),
        # Meta
        "n_obs": n_obs,
        "n_excluded_non_finite": n_excluded_non_finite,
    }


def summarize_cv_model_results(
    res,
    selected_features,
    name_model,
    overfitting_thresholds=(0.02, 0.05),
    z_outlier_threshold=2.0,
    splits=None,
    nadeau_bengio_se_fn=nadeau_bengio_se,
):
    """
    Resume resultados de validación cruzada y feature importances.

    Parameters
    ----------
    res : dict
        Resultado de sklearn.model_selection.cross_validate.
        Debe contener: "test_score", "train_score", "estimator".

    selected_features : list
        Lista de features usadas por el modelo, en el mismo orden que estimator.feature_importances_.

    name_model : str
        Identificador del modelo.

    overfitting_thresholds : tuple(float, float)
        Umbrales para clasificar overfitting:
        - gap < threshold_low  -> Bajo
        - gap < threshold_high -> Moderado
        - gap >= threshold_high -> Alto

    z_outlier_threshold : float
        Umbral absoluto de z-score para marcar folds atípicos.

    splits : list or None
        Lista de splits de CV. Se usa solo si quieres calcular Nadeau-Bengio SE.

    nadeau_bengio_se_fn : callable or None
        Función tipo nadeau_bengio_se(scores, n_train_cv, n_test_cv).

    Returns
    -------
    dict[str, pd.DataFrame]
    """

    threshold_low, threshold_high = overfitting_thresholds
    n_vars = len(selected_features)

    mae_val = -np.asarray(res["test_score"])
    mae_train = -np.asarray(res["train_score"])

    assert len(mae_val) == len(
        mae_train
    ), "test_score y train_score deben tener el mismo número de folds."

    mae_val_mean = mae_val.mean()
    mae_val_std = mae_val.std()

    mae_train_mean = mae_train.mean()
    mae_train_std = mae_train.std()

    gap_folds = mae_val - mae_train
    gap_mean = gap_folds.mean()
    gap_std = gap_folds.std()

    cv_pct = 100 * mae_val_std / mae_val_mean if mae_val_mean != 0 else np.nan

    if mae_val_std > 0:
        z = (mae_val - mae_val_mean) / mae_val_std
    else:
        z = np.zeros_like(mae_val)

    is_outlier_fold = np.abs(z) > z_outlier_threshold
    n_outlier_folds = int(is_outlier_fold.sum())

    if gap_mean < threshold_low:
        overfitting_diagnosis = "Bajo"
    elif gap_mean < threshold_high:
        overfitting_diagnosis = "Moderado"
    else:
        overfitting_diagnosis = "Alto"

    # =========================================================
    # 1) Resultados fold a fold
    # =========================================================
    cv_folds = pd.DataFrame(
        {
            "name_model": name_model,
            "fold": np.arange(len(mae_val)),
            "mae_train": mae_train,
            "mae_validation": mae_val,
            "gap_train_validation": gap_folds,
            "z_validation_mae": z,
            "is_outlier_fold": is_outlier_fold,
        }
    )

    # =========================================================
    # 2) Feature importances fold a fold + agregado
    # =========================================================
    feature_importances_all = []

    for fold, estimator in enumerate(res["estimator"]):
        fold_importance = pd.DataFrame(
            {
                "name_model": name_model,
                "feature_name": selected_features,
                "importance": estimator.feature_importances_,
                "fold": fold,
            }
        )
        feature_importances_all.append(fold_importance)

    feature_importance_folds = pd.concat(feature_importances_all, ignore_index=True)

    feature_importances = (
        feature_importance_folds.groupby(["name_model", "feature_name"], as_index=False)
        .agg(
            importance_mean=("importance", "mean"),
            importance_std=("importance", "std"),
            importance_min=("importance", "min"),
            importance_max=("importance", "max"),
        )
        .sort_values(
            ["name_model", "importance_mean"],
            ascending=[True, False],
        )
        .reset_index(drop=True)
    )

    importance_sum = feature_importances["importance_mean"].sum()

    assert np.isclose(importance_sum, 1.0, atol=1e-6), (
        f"Las feature importances medias no suman aproximadamente 1. "
        f"Suma actual: {importance_sum:.8f}"
    )

    # =========================================================
    # 3) Nadeau-Bengio SE opcional
    # =========================================================
    se_nb = np.nan

    if splits is not None and nadeau_bengio_se_fn is not None:
        n_train_cv = len(splits[0][0])
        n_test_cv = len(splits[0][1])
        se_nb = nadeau_bengio_se_fn(mae_val, n_train_cv, n_test_cv)

    # =========================================================
    # 4) Summary en formato long
    # =========================================================
    cv_summary = pd.DataFrame(
        {
            "name_model": name_model,
            "metric": [
                "mae_validation_mean",
                "mae_validation_std",
                "mae_train_mean",
                "mae_train_std",
                "gap_train_validation_mean",
                "gap_train_validation_std",
                "cv_pct",
                "n_folds",
                "n_outlier_folds",
                "n_vars",
                "se_nb",
                "importance_mean_sum",
                "overfitting_threshold_low",
                "overfitting_threshold_high",
            ],
            "value": [
                mae_val_mean,
                mae_val_std,
                mae_train_mean,
                mae_train_std,
                gap_mean,
                gap_std,
                cv_pct,
                len(mae_val),
                n_outlier_folds,
                n_vars,
                se_nb,
                importance_sum,
                threshold_low,
                threshold_high,
            ],
        }
    )

    # =========================================================
    # 5) Baseline ref en formato ancho
    #    Útil para comparar modelos directamente
    # =========================================================
    model_summary = pd.DataFrame(
        [
            {
                "name_model": name_model,
                "mae_val_mean": mae_val_mean,
                "mae_val_std": mae_val_std,
                "se_nb": se_nb,
                "mae_train_mean": mae_train_mean,
                "mae_train_std": mae_train_std,
                "gap_mean": gap_mean,
                "gap_std": gap_std,
                "cv_pct": cv_pct,
                "n_folds": len(mae_val),
                "n_outlier_folds": n_outlier_folds,
                "n_vars": n_vars,
                "overfitting_diagnosis": overfitting_diagnosis,
                "overfitting_threshold_low": threshold_low,
                "overfitting_threshold_high": threshold_high,
            }
        ]
    )

    return {
        "cv_folds": cv_folds,
        "cv_summary": cv_summary,
        "feature_importances": feature_importances,
        "model_summary": model_summary,
    }


def summarize_model_results(
    estimator,
    X_train,
    y_train,
    X_validation,
    y_validation,
    selected_features=None,
    name_model=None,
    overfitting_thresholds=(0.02, 0.05),
    success_threshold=0.05,
):
    """
    Resume performance train/validation de un modelo ya entrenado.

    Si selected_features es None, usa todas las columnas de X_train.
    Si selected_features se entrega, evalua usando solo esas columnas.
    """

    if name_model is None:
        name_model = estimator.__class__.__name__

    if selected_features is None:
        selected_features = list(X_train.columns)
    else:
        selected_features = list(selected_features)

    missing_train = sorted(set(selected_features) - set(X_train.columns))
    missing_validation = sorted(set(selected_features) - set(X_validation.columns))

    assert not missing_train, f"Columnas faltantes en X_train: {missing_train}"
    assert (
        not missing_validation
    ), f"Columnas faltantes en X_validation: {missing_validation}"

    X_train_eval = X_train.loc[:, selected_features]
    X_validation_eval = X_validation.loc[:, selected_features]

    threshold_low, threshold_high = overfitting_thresholds
    n_vars = len(selected_features)

    y_train_true = pd.Series(
        np.asarray(y_train), index=X_train_eval.index, name="y_true"
    )
    y_validation_true = pd.Series(
        np.asarray(y_validation),
        index=X_validation_eval.index,
        name="y_true",
    )

    pred_train = pd.Series(
        estimator.predict(X_train_eval),
        index=X_train_eval.index,
        name="y_pred",
    )

    pred_validation = pd.Series(
        estimator.predict(X_validation_eval),
        index=X_validation_eval.index,
        name="y_pred",
    )

    train_metrics = _regression_metrics(
        y_true=y_train_true,
        y_pred=pred_train,
        success_threshold=success_threshold,
    )

    validation_metrics = _regression_metrics(
        y_true=y_validation_true,
        y_pred=pred_validation,
        success_threshold=success_threshold,
    )

    if train_metrics["n_obs"] == 0 or validation_metrics["n_obs"] == 0:
        raise ValueError(
            "No hay pares finitos (y_true, y_pred) suficientes para evaluar "
            f"{name_model}. train={train_metrics['n_obs']}, "
            f"validation={validation_metrics['n_obs']}."
        )

    mae_train = train_metrics["mae"]
    mae_validation = validation_metrics["mae"]
    gap_train_validation = mae_validation - mae_train

    if gap_train_validation < threshold_low:
        overfitting_diagnosis = "Bajo"
    elif gap_train_validation < threshold_high:
        overfitting_diagnosis = "Moderado"
    else:
        overfitting_diagnosis = "Alto"

    predictions = pd.concat(
        [
            pd.DataFrame(
                {
                    "name_model": name_model,
                    "sample": "train",
                    "row_index": y_train_true.index.astype(str),
                    "y_true": y_train_true.to_numpy(),
                    "y_pred": pred_train.to_numpy(),
                }
            ),
            pd.DataFrame(
                {
                    "name_model": name_model,
                    "sample": "validation",
                    "row_index": y_validation_true.index.astype(str),
                    "y_true": y_validation_true.to_numpy(),
                    "y_pred": pred_validation.to_numpy(),
                }
            ),
        ],
        ignore_index=True,
    )

    predictions["error"] = predictions["y_true"] - predictions["y_pred"]
    predictions["abs_error"] = predictions["error"].abs()
    predictions["squared_error"] = predictions["error"] ** 2
    predictions["flag_success"] = predictions["abs_error"] <= success_threshold

    if hasattr(estimator, "feature_importances_"):
        importances = np.asarray(estimator.feature_importances_)

        assert len(importances) == n_vars, (
            "El largo de estimator.feature_importances_ no coincide con selected_features. "
            f"feature_importances_={len(importances)}, selected_features={n_vars}"
        )

        feature_importances = (
            pd.DataFrame(
                {
                    "name_model": name_model,
                    "feature_name": selected_features,
                    "importance_mean": importances,
                }
            )
            .sort_values(["name_model", "importance_mean"], ascending=[True, False])
            .reset_index(drop=True)
        )

        importance_sum = feature_importances["importance_mean"].sum()
        top_feature = feature_importances.iloc[0]
        feature_name_top1 = top_feature["feature_name"]
        feature_importance_top1 = top_feature["importance_mean"]

        assert np.isclose(importance_sum, 1.0, atol=1e-6), (
            f"Las feature importances no suman aproximadamente 1. "
            f"Suma actual: {importance_sum:.8f}"
        )
    else:
        feature_importances = pd.DataFrame(
            columns=[
                "name_model",
                "feature_name",
                "importance_mean",
            ]
        )
        importance_sum = np.nan
        feature_name_top1 = np.nan
        feature_importance_top1 = np.nan

    model_summary = pd.DataFrame(
        [
            {
                "name_model": name_model,
                "mae_val_mean": mae_validation,
                "mae_train_mean": mae_train,
                "rmse_val_mean": validation_metrics["rmse"],
                "rmse_train_mean": train_metrics["rmse"],
                "mape_val_mean": validation_metrics["mape"],
                "mape_train_mean": train_metrics["mape"],
                "success_rate_val_mean": validation_metrics["success_rate"],
                "success_rate_train_mean": train_metrics["success_rate"],
                "success_threshold": success_threshold,
                "gap_mean": gap_train_validation,
                "n_train": len(y_train_true),
                "n_validation": len(y_validation_true),
                "n_train_evaluated": train_metrics["n_obs"],
                "n_validation_evaluated": validation_metrics["n_obs"],
                "n_train_excluded_non_finite": train_metrics["n_excluded_non_finite"],
                "n_validation_excluded_non_finite": validation_metrics[
                    "n_excluded_non_finite"
                ],
                "n_vars": n_vars,
                "importance_mean_sum": importance_sum,
                "feature_name_top1": feature_name_top1,
                "feature_importance_top1": feature_importance_top1,
                "overfitting_diagnosis": overfitting_diagnosis,
                "overfitting_threshold_low": threshold_low,
                "overfitting_threshold_high": threshold_high,
            }
        ]
    )

    return {
        "model_predictions": predictions,
        "feature_importances": feature_importances,
        "model_summary": model_summary,
    }


ALL_METRICS = [
    "mae",
    "rmse",
    "mse",
    "mape",
    "smape",
    "mdape",
    "rmspe",
    "r2",
    "success_rate",
]
P10_METRICS = [f"{m}_p10" for m in ALL_METRICS]
AVAILABLE_METRICS = ALL_METRICS + P10_METRICS


def _success_rate_col_name(success_threshold):
    return f"success_rate_{int(success_threshold * 100)}"


def _build_output_row(m, success_threshold, metrics):
    """Renombra success_rate (y su P10) y filtra metricas solicitadas."""
    sr_name = _success_rate_col_name(success_threshold)
    sr_p10_name = f"{sr_name}_p10"

    m[sr_name] = m.pop("success_rate")
    m[sr_p10_name] = m.pop("success_rate_p10")

    metric_cols = []
    for metric in metrics:
        if metric == "success_rate":
            metric_cols.append(sr_name)
        elif metric == "success_rate_p10":
            metric_cols.append(sr_p10_name)
        else:
            metric_cols.append(metric)

    # Mantener solo metricas solicitadas + meta columnas
    keep_keys = set(metric_cols) | {
        "n_obs",
        "n_excluded_non_finite",
        "sample",
        "decile_target",
        "decile_range_target",
        "avg_target",
        "avg_pred",
        "seg_col",
        "seg_value",
    }
    for key in list(m.keys()):
        if key not in keep_keys:
            m.pop(key, None)
    return m, metric_cols


def performance_global(
    y_true, y_pred, success_threshold, sample_name=None, metrics=None
):
    """
    Performance global de regresion.

    Parameters
    ----------
    metrics : list or None
        Lista de metricas a incluir. Default: todas.
        Opciones: "mae", "rmse", "mape", "smape", "r2", "success_rate".
    """
    if metrics is None:
        metrics = ALL_METRICS

    m = _regression_metrics(y_true, y_pred, success_threshold)
    m["sample"] = sample_name
    m, metric_cols = _build_output_row(m, success_threshold, metrics)

    col_order = ["sample"] + metric_cols + ["n_obs", "n_excluded_non_finite"]
    result = pd.DataFrame([m])[col_order]
    numeric_cols = result.select_dtypes(include="number").columns
    result[numeric_cols] = result[numeric_cols].round(4)
    return result


def performance_by_decile(
    df,
    target_col,
    pred_col,
    success_threshold,
    sample_name=None,
    n_bins=10,
    metrics=None,
):
    """
    Performance por decil de y_true.

    Usa pd.qcut sobre target_col para crear bins.
    Retorna DataFrame con 1 fila por decil.

    Parameters
    ----------
    metrics : list or None
        Lista de metricas a incluir. Default: todas.
    """
    if metrics is None:
        metrics = ALL_METRICS

    df = df.copy()
    df["_decile"], bins = pd.qcut(
        df[target_col], q=n_bins, labels=False, retbins=True, duplicates="drop"
    )
    # decile 1-based
    df["_decile"] = df["_decile"] + 1

    rows = []
    metric_cols = None
    for decile, grp in df.groupby("_decile", dropna=False):
        m = _regression_metrics(grp[target_col], grp[pred_col], success_threshold)
        idx = int(decile) - 1
        lo = bins[idx]
        hi = bins[idx + 1]
        m["sample"] = sample_name
        m["decile_target"] = int(decile)
        m["decile_range_target"] = f"({lo:.4f}, {hi:.4f}]"
        m["avg_target"] = float(grp[target_col].mean())
        m["avg_pred"] = float(grp[pred_col].mean())
        m, metric_cols = _build_output_row(m, success_threshold, metrics)
        rows.append(m)

    col_order = (
        ["sample", "decile_target", "decile_range_target", "avg_target", "avg_pred"]
        + metric_cols
        + ["n_obs", "n_excluded_non_finite"]
    )
    result = pd.DataFrame(rows)[col_order].reset_index(drop=True)
    numeric_cols = result.select_dtypes(include="number").columns
    result[numeric_cols] = result[numeric_cols].round(4)
    return result


def performance_by_segment(
    df,
    target_col,
    pred_col,
    seg_cols,
    success_threshold,
    sample_name=None,
    metrics=None,
):
    """
    Performance por segmento (columnas categoricas).

    Itera por cada columna en seg_cols y por cada valor unico.
    NaNs se mantienen como grupo separado.
    Retorna DataFrame con 1 fila por (seg_col, seg_value).

    Parameters
    ----------
    metrics : list or None
        Lista de metricas a incluir. Default: todas.
    """
    if metrics is None:
        metrics = ALL_METRICS

    rows = []
    metric_cols = None
    for seg_col in seg_cols:
        for seg_value, grp in df.groupby(seg_col, dropna=False):
            m = _regression_metrics(grp[target_col], grp[pred_col], success_threshold)
            m["sample"] = sample_name
            m["seg_col"] = seg_col
            m["seg_value"] = seg_value
            m["avg_target"] = float(grp[target_col].mean())
            m["avg_pred"] = float(grp[pred_col].mean())
            m, metric_cols = _build_output_row(m, success_threshold, metrics)
            rows.append(m)

    col_order = (
        ["sample", "seg_col", "seg_value", "avg_target", "avg_pred"]
        + metric_cols
        + ["n_obs", "n_excluded_non_finite"]
    )
    result = pd.DataFrame(rows)[col_order].reset_index(drop=True)
    numeric_cols = result.select_dtypes(include="number").columns
    result[numeric_cols] = result[numeric_cols].round(4)
    return result


def add_real_vs_pred_pages_to_pdf(
    df_pred,
    target_col,
    pred_col,
    sample_name,
    model_name,
    pdf,
    bins=50,
    show_plots=True,
    xlim=None,
    ylim=None,
    title_metrics=("mae", "rmse", "smape"),
    success_threshold=0.05,
):
    """
    Agrega 2 páginas a un PdfPages:
    1. Histograma distribución real vs predicha.
    2. Scatter real vs predicha con línea de predicción perfecta.

    Parameters
    ----------
    title_metrics : tuple/list of str or None
        Métricas a mostrar en el título. Opciones: cualquier clave de
        _regression_metrics (mae, rmse, mape, smape, r2, success_rate, etc.).
        Si None o vacío, no se añaden métricas al título.
    success_threshold : float
        Umbral para success_rate (solo relevante si "success_rate" en title_metrics).
    """
    required_cols = [target_col, pred_col]
    missing_cols = [col for col in required_cols if col not in df_pred.columns]
    assert not missing_cols, f"Faltan columnas en df_pred: {missing_cols}"

    df_plot = df_pred[required_cols].dropna().copy()
    assert len(df_plot) > 0, f"No hay datos para plotear: {model_name} | {sample_name}"

    # Calcular métricas para el título
    metrics_subtitle = ""
    if title_metrics:
        m = _regression_metrics(
            df_plot[target_col].values,
            df_plot[pred_col].values,
            success_threshold,
        )
        parts = [
            f"{k.upper()}={m[k]:.4f}"
            for k in title_metrics
            if k in m and np.isfinite(m[k])
        ]
        if parts:
            metrics_subtitle = " | ".join(parts)

    # Page 1: Distribution True vs Predicted
    fig, ax = plt.subplots(figsize=(8, 4))

    df_plot[target_col].hist(
        bins=bins,
        alpha=0.5,
        label="True",
        ax=ax,
    )

    df_plot[pred_col].hist(
        bins=bins,
        alpha=0.5,
        label="Predicted",
        ax=ax,
    )

    title_hist = f"{model_name} | {sample_name}\nTrue vs Predicted Distribution"
    if metrics_subtitle:
        title_hist += f"\n{metrics_subtitle}"
    ax.set_title(title_hist, fontsize=10)
    ax.set_xlabel(target_col)
    ax.set_ylabel("Frequency")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.3)

    fig.tight_layout()
    pdf.savefig(fig)

    if show_plots:
        plt.show()

    plt.close(fig)

    # Page 2: Scatter True vs Predicted
    fig, ax = plt.subplots(figsize=(6, 6))

    ax.scatter(
        df_plot[target_col],
        df_plot[pred_col],
        alpha=0.25,
        s=20,
    )

    # Compute axis limits from data if not provided
    if xlim is None:
        data_min = df_plot[target_col].min()
        data_max = df_plot[target_col].max()
        margin = (data_max - data_min) * 0.05
        xlim = (data_min - margin, data_max + margin)
    if ylim is None:
        data_min = df_plot[pred_col].min()
        data_max = df_plot[pred_col].max()
        margin = (data_max - data_min) * 0.05
        ylim = (data_min - margin, data_max + margin)

    ax.plot(
        [xlim[0], xlim[1]],
        [ylim[0], ylim[1]],
        "r--",
        lw=2,
        label="Perfect prediction",
    )

    title_scatter = f"{model_name} | {sample_name}\nTrue vs Predicted"
    if metrics_subtitle:
        title_scatter += f"\n{metrics_subtitle}"
    ax.set_title(title_scatter, fontsize=10)
    ax.set_xlabel("True value")
    ax.set_ylabel("Predicted value")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend()

    fig.tight_layout()
    pdf.savefig(fig)

    if show_plots:
        plt.show()

    plt.close(fig)
