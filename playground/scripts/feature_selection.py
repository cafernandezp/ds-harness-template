"""
Funciones de seleccion multivariante de features para modelos de progreso judicial.

Pipeline: Redundancy -> Boruta-SHAP -> Stability Selection -> Backward Selection -> Evaluation.

Uso en notebooks:
    import importlib
    import feature_selection as fs
    importlib.reload(fs)
"""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import shap
from scipy import stats
from sklearn.base import clone
from sklearn.metrics import get_scorer
from sklearn.model_selection import StratifiedShuffleSplit, cross_validate


# =========================================================
# Utilities
# =========================================================

def nadeau_bengio_se(scores, n_train, n_test):
    """Calcula el error estandar corregido de Nadeau-Bengio.

    Los folds del CV repetido comparten train -> estan correlacionados;
    std/sqrt(n) infraestima el SE. El termino n_test/n_train corrige eso.

    Parameters
    ----------
    scores : array-like
        Scores fold-a-fold de una misma estrategia de validacion.
    n_train : int
        Numero de observaciones en train para cada split.
    n_test : int
        Numero de observaciones en validacion para cada split.

    Returns
    -------
    float
        Error estandar corregido.

    Notes
    -----
    Usar con scores comparables entre si. Para comparar dos modelos en los
    mismos splits, lo mas riguroso es aplicarlo sobre diferencias fold-a-fold.
    """
    # Buena practica: usar los scores fold-a-fold, no solo medias agregadas.
    # La correccion solo tiene sentido si n_train/n_test vienen del mismo CV.
    J = len(scores)
    s2 = np.var(scores, ddof=1)
    return np.sqrt((1.0 / J + n_test / n_train) * s2)


# =========================================================
# Phase 1: Redundancy Removal (Spearman + Cramer's V)
# =========================================================

def _pair_type_defaults(comparison_group):
    """Devuelve tipos esperados para pares conocidos de Phase 1."""
    defaults = {
        "flag_flag": ("binary", "binary"),
        "continuous_continuous": ("continuous", "continuous"),
        "nominal_flag": ("nominal", "binary"),
        "flag_continuous": ("binary", "continuous"),
    }
    return defaults.get(comparison_group, (None, None))


def _non_constant_cols(X, cols):
    """Filtra columnas con al menos dos valores no nulos distintos."""
    return [col for col in cols if X[col].nunique(dropna=True) > 1]


def _sorted_unique_cols(cols):
    """Ordena columnas para que los pares no dependan del orden de entrada."""
    return sorted(dict.fromkeys(cols))


def _add_pair_metadata(pair, comparison_group=None, var_a_type=None, var_b_type=None):
    """Anade metadatos opcionales sin romper consumidores antiguos."""
    if comparison_group is None and var_a_type is None and var_b_type is None:
        return pair

    default_a_type, default_b_type = _pair_type_defaults(comparison_group)
    pair = pair.copy()
    pair["comparison_group"] = comparison_group
    pair["var_a_type"] = var_a_type or default_a_type
    pair["var_b_type"] = var_b_type or default_b_type
    return pair


def spearman_pairs(
    X,
    num_cols,
    thr=0.90,
    min_periods=None,
    comparison_group=None,
    var_type=None,
):
    """Detecta pares numericos redundantes por correlacion Spearman absoluta.

    Parameters
    ----------
    X : pandas.DataFrame
        Dataset con las columnas numericas/binarias a evaluar.
    num_cols : list[str]
        Columnas numericas o binarias candidatas.
    thr : float, default=0.90
        Umbral inclusivo: pares con ``abs(rho) >= thr`` se consideran
        redundantes.
    min_periods : int, optional
        Minimo de observaciones validas por par. Si no se informa, se usa una
        regla conservadora dependiente del tamano de X.
    comparison_group : str, optional
        Grupo auditable de comparacion.
    var_type : str, optional
        Tipo comun de las variables comparadas.

    Returns
    -------
    list[dict]
        Pares redundantes con variables, metrica, valor de asociacion y umbral.
    """
    if len(num_cols) < 2:
        return []
    num_cols = _sorted_unique_cols(_non_constant_cols(X, num_cols))
    if len(num_cols) < 2:
        return []
    # Buena practica: exigir observaciones validas suficientes evita pares
    # espurios cuando dos variables solo solapan en muy pocos registros.
    min_periods = min_periods or max(50, int(0.01 * len(X)))
    corr_matrix = X[num_cols].corr(method="spearman", min_periods=min_periods).abs()
    # Solo triangulo superior: evita duplicar pares A-B/B-A y autocorrelaciones.
    upper = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )
    redundant_pairs = (
        upper.stack()
        .reset_index()
        .rename(
            columns={
                "level_0": "var_a",
                "level_1": "var_b",
                0: "association_value",
            }
        )
        .query("association_value >= @thr")
    )
    redundant_pairs["pair_metric"] = "spearman_abs"
    redundant_pairs["threshold"] = thr
    pairs = redundant_pairs[
        ["var_a", "var_b", "pair_metric", "association_value", "threshold"]
    ].to_dict("records")
    return [
        _add_pair_metadata(
            pair,
            comparison_group=comparison_group,
            var_a_type=var_type,
            var_b_type=var_type,
        )
        for pair in pairs
    ]


def spearman_pairs_between(
    X,
    left_cols,
    right_cols,
    thr=0.90,
    min_periods=None,
    comparison_group=None,
    left_type=None,
    right_type=None,
):
    """Detecta pares redundantes Spearman entre dos familias numericas."""
    if len(left_cols) == 0 or len(right_cols) == 0:
        return []

    left_cols = _sorted_unique_cols(_non_constant_cols(X, left_cols))
    right_cols = _sorted_unique_cols(_non_constant_cols(X, right_cols))
    if len(left_cols) == 0 or len(right_cols) == 0:
        return []

    min_periods = min_periods or max(50, int(0.01 * len(X)))
    cols = _sorted_unique_cols(list(left_cols) + list(right_cols))
    corr_matrix = X[cols].corr(method="spearman", min_periods=min_periods).abs()

    pairs = []
    seen = set()
    for a in left_cols:
        for b in right_cols:
            pair_key = frozenset([a, b])
            if a == b or pair_key in seen:
                continue
            seen.add(pair_key)
            value = corr_matrix.loc[a, b]
            if pd.notna(value) and value >= thr:
                pairs.append(
                    _add_pair_metadata(
                        {
                            "var_a": a,
                            "var_b": b,
                            "pair_metric": "spearman_abs",
                            "association_value": value,
                            "threshold": thr,
                        },
                        comparison_group=comparison_group,
                        var_a_type=left_type,
                        var_b_type=right_type,
                    )
                )
    return pairs


def cramers_v(a, b):
    """Calcula Cramer's V entre dos variables categoricas.

    Parameters
    ----------
    a, b : array-like
        Variables categoricas a comparar.

    Returns
    -------
    float
        Asociacion categorica en [0, 1]. Devuelve 0 si no hay informacion
        suficiente para construir una tabla valida.

    Notes
    -----
    Los NaN se tratan como nivel ``"__MISSING__"`` porque el missing puede ser
    informativo en variables de negocio.
    """
    # Buena practica: en variables categoricas de negocio, missing puede ser
    # informativo. Se codifica explicitamente para no perder esa senal.
    a_clean = pd.Series(a).astype("object").where(pd.notna(a), "__MISSING__")
    b_clean = pd.Series(b).astype("object").where(pd.notna(b), "__MISSING__")
    ct = pd.crosstab(a_clean, b_clean, dropna=False)
    n = ct.to_numpy().sum()
    r, k = ct.shape
    if n == 0 or min(r, k) <= 1:
        return 0.0
    chi2 = stats.chi2_contingency(ct, correction=False)[0]
    return np.sqrt(chi2 / (n * (min(r, k) - 1)))


def cramers_pairs(
    X,
    cat_cols,
    thr=0.80,
    comparison_group=None,
    var_type=None,
):
    """Detecta pares categoricos redundantes por Cramer's V.

    Parameters
    ----------
    X : pandas.DataFrame
        Dataset con columnas categoricas.
    cat_cols : list[str]
        Columnas categoricas candidatas.
    thr : float, default=0.80
        Umbral estricto: pares con ``V > thr`` se consideran redundantes.
    comparison_group : str, optional
        Grupo auditable de comparacion.
    var_type : str, optional
        Tipo comun de las variables comparadas.

    Returns
    -------
    list[dict]
        Pares redundantes con variables, metrica, valor de asociacion y umbral.
    """
    cat_cols = _sorted_unique_cols(cat_cols)
    if len(cat_cols) < 2:
        return []
    pairs = []
    # Buena practica: calcular asociacion solo entre variables de misma familia.
    # No mezclar aqui numericas-categoricas mantiene interpretacion clara.
    for i, a in enumerate(cat_cols):
        for b in cat_cols[i + 1:]:
            value = cramers_v(X[a], X[b])
            if pd.notna(value) and value > thr:
                pairs.append(
                    _add_pair_metadata(
                        {
                            "var_a": a,
                            "var_b": b,
                            "pair_metric": "cramers_v",
                            "association_value": value,
                            "threshold": thr,
                        },
                        comparison_group=comparison_group,
                        var_a_type=var_type,
                        var_b_type=var_type,
                    )
                )
    return pairs


def cramers_pairs_between(
    X,
    left_cols,
    right_cols,
    thr=0.80,
    comparison_group=None,
    left_type=None,
    right_type=None,
):
    """Detecta pares redundantes Cramer's V entre dos familias categoricas."""
    if len(left_cols) == 0 or len(right_cols) == 0:
        return []

    left_cols = _sorted_unique_cols(left_cols)
    right_cols = _sorted_unique_cols(right_cols)
    pairs = []
    seen = set()
    for a in left_cols:
        for b in right_cols:
            pair_key = frozenset([a, b])
            if a == b or pair_key in seen:
                continue
            seen.add(pair_key)
            value = cramers_v(X[a], X[b])
            if pd.notna(value) and value > thr:
                pairs.append(
                    _add_pair_metadata(
                        {
                            "var_a": a,
                            "var_b": b,
                            "pair_metric": "cramers_v",
                            "association_value": value,
                            "threshold": thr,
                        },
                        comparison_group=comparison_group,
                        var_a_type=left_type,
                        var_b_type=right_type,
                    )
                )
    return pairs


def correlation_ratio(cats, vals):
    """Calcula eta/correlation ratio entre categorica y target continuo.

    Parameters
    ----------
    cats : array-like
        Variable categorica.
    vals : array-like
        Variable continua, normalmente el target.

    Returns
    -------
    float
        Eta en [0, 1], donde valores altos indican mayor separacion de medias
        del target entre niveles de la categorica.

    Notes
    -----
    Se usa como relevancia feature-target para desempatar variables
    categoricas redundantes; no como test de seleccion supervisada.
    """
    # Buena practica: resetear indices antes de aplicar mascara evita
    # desalineaciones silenciosas entre categoria y target.
    vals = pd.to_numeric(pd.Series(vals).reset_index(drop=True), errors="coerce")
    cats = pd.Series(cats).reset_index(drop=True).astype("object")
    cats = cats.where(cats.notna(), "__MISSING__")
    mask = vals.notna()
    vals = vals[mask]
    cats = cats[mask]
    if len(vals) == 0:
        return np.nan
    grand_mean = vals.mean()
    ss_total = ((vals - grand_mean) ** 2).sum()
    if ss_total == 0:
        return 0.0
    ss_between = 0.0
    for level in cats.unique():
        group_vals = vals[cats == level]
        ss_between += len(group_vals) * (group_vals.mean() - grand_mean) ** 2
    return np.sqrt(ss_between / ss_total)


def build_phase1_relevance(df, num_cols, cat_cols, target_col):
    """Construye relevancia feature-target para desempates de Phase 1.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataset completo con features y target.
    num_cols : list[str]
        Variables numericas/binarias.
    cat_cols : list[str]
        Variables categoricas.
    target_col : str
        Nombre del target continuo.

    Returns
    -------
    pandas.DataFrame
        Columnas: ``feature_name``, ``corr_method`` y ``value``.

    Notes
    -----
    Numericas usan ``abs(Spearman(feature, target))``. Categoricas usan eta
    contra target continuo. Esta relevancia no elimina variables por si sola;
    solo decide que variable conservar dentro de pares redundantes.
    """
    rows = []
    # Numericas: Spearman es robusto ante relaciones monotonas no lineales y
    # outliers, por eso encaja mejor que Pearson en filtros iniciales.
    num_cols = _sorted_unique_cols(num_cols)
    cat_cols = _sorted_unique_cols(cat_cols)
    variable_num_cols = _sorted_unique_cols(_non_constant_cols(df, num_cols))
    target_is_constant = df[target_col].nunique(dropna=True) <= 1
    relevance_num = pd.Series(index=num_cols, dtype="float64")
    if variable_num_cols and not target_is_constant:
        relevance_num.loc[variable_num_cols] = (
            df[variable_num_cols]
            .corrwith(df[target_col], method="spearman")
            .abs()
        )
    for col, value in relevance_num.items():
        rows.append(
            {
                "feature_name": col,
                "corr_method": "spearman_abs_target",
                "value": value,
            }
        )
    # Categoricas: eta mide separacion de medias del target continuo por nivel.
    for col in cat_cols:
        rows.append(
            {
                "feature_name": col,
                "corr_method": "eta_target",
                "value": correlation_ratio(df[col], df[target_col]),
            }
        )
    return pd.DataFrame(rows)


def resolve_redundancy(X, pair_lists, relevance=None):
    """Resuelve pares redundantes eliminando variables de forma iterativa.

    Parameters
    ----------
    X : pandas.DataFrame
        Dataset restringido al universo de features candidatas.
    pair_lists : list[list[dict]]
        Listas de pares redundantes generadas por filtros type-aware, por
        ejemplo Spearman y Cramer's V.
    relevance : pandas.Series, optional
        Relevancia feature-target indexada por nombre de feature.

    Returns
    -------
    tuple[list[str], list[dict], list[dict]]
        ``survivors``: features no eliminadas.
        ``pairs``: todos los pares redundantes de entrada.
        ``decisions``: log auditable de cada baja.

    Notes
    -----
    El algoritmo procesa el par vivo mas redundante, elimina una variable y
    recalcula pares vivos. Esto evita bajas redundantes dentro de clusters ya
    resueltos.
    """
    pairs = [pair for pair_list in pair_lists for pair in pair_list]
    missing_rate = X.isna().mean()
    dropped = set()
    decisions = []

    def get_relevance(col):
        if relevance is None or col not in relevance.index:
            return np.nan
        return relevance[col]

    def choose_removed(a, b):
        rel_a = get_relevance(a)
        rel_b = get_relevance(b)
        miss_a = missing_rate[a]
        miss_b = missing_rate[b]

        # Orden de desempate auditable:
        # 1) conservar mayor relevancia con target;
        # 2) conservar menor missing rate;
        # 3) resolver alfabeticamente para reproducibilidad.
        if pd.notna(rel_a) and pd.isna(rel_b):
            return b, a, "lower_relevance"
        if pd.isna(rel_a) and pd.notna(rel_b):
            return a, b, "lower_relevance"
        if pd.notna(rel_a) and pd.notna(rel_b) and not np.isclose(rel_a, rel_b):
            return (a, b, "lower_relevance") if rel_a < rel_b else (b, a, "lower_relevance")
        if not np.isclose(miss_a, miss_b):
            return (a, b, "higher_missing_rate") if miss_a > miss_b else (b, a, "higher_missing_rate")

        kept = min(a, b)
        removed = max(a, b)
        return removed, kept, "alphabetical_tiebreak"

    step = 0
    while True:
        # Recalcular pares vivos tras cada baja evita eliminar dos variables del
        # mismo cluster cuando una eliminacion ya rompio la redundancia.
        live_pairs = [
            pair
            for pair in pairs
            if pair["var_a"] not in dropped and pair["var_b"] not in dropped
        ]
        if not live_pairs:
            break

        pair = sorted(
            live_pairs,
            key=lambda p: (-p["association_value"], p["var_a"], p["var_b"]),
        )[0]
        # Procesar primero la asociacion mas alta reduce riesgo de dejar vivo
        # un par extremadamente redundante por decisiones previas mas debiles.
        a = pair["var_a"]
        b = pair["var_b"]
        removed, kept, decision_rule = choose_removed(a, b)
        n_survivors_before = len(X.columns) - len(dropped)
        dropped.add(removed)
        step += 1
        decisions.append(
            {
                "step": step,
                "var_a": a,
                "var_b": b,
                "pair_metric": pair["pair_metric"],
                "association_value": pair["association_value"],
                "threshold": pair["threshold"],
                "relevance_a": get_relevance(a),
                "relevance_b": get_relevance(b),
                "missing_rate_a": missing_rate[a],
                "missing_rate_b": missing_rate[b],
                "removed": removed,
                "kept": kept,
                "decision_rule": decision_rule,
                "n_survivors_before": n_survivors_before,
                "n_survivors_after": n_survivors_before - 1,
            }
        )

    survivors = [col for col in X.columns if col not in dropped]
    return survivors, pairs, decisions


def resolve_redundancy_staged(X, pair_stages, relevance=None):
    """Resuelve redundancia en etapas deterministas.

    Parameters
    ----------
    X : pandas.DataFrame
        Dataset restringido al universo de features candidatas.
    pair_stages : list[dict]
        Etapas con ``stage_order``, ``stage_name`` y ``pairs``.
    relevance : pandas.Series, optional
        Relevancia feature-target indexada por nombre de feature.

    Returns
    -------
    tuple[list[str], list[dict], list[dict]]
        ``survivors``: features no eliminadas.
        ``pairs``: todos los pares redundantes de entrada con etapa.
        ``decisions``: log auditable de bajas y pares saltados.

    Notes
    -----
    No compara directamente Cramer's V contra Spearman. Primero respeta
    ``stage_order`` y, dentro de cada etapa, procesa la asociacion mas alta.
    """
    missing_rate = X.isna().mean()
    dropped = set()
    decisions = []
    all_pairs = []

    def get_relevance(col):
        if relevance is None or col not in relevance.index:
            return np.nan
        return relevance[col]

    def choose_removed(a, b):
        rel_a = get_relevance(a)
        rel_b = get_relevance(b)
        miss_a = missing_rate[a]
        miss_b = missing_rate[b]

        if pd.notna(rel_a) and pd.isna(rel_b):
            return b, a, "lower_relevance"
        if pd.isna(rel_a) and pd.notna(rel_b):
            return a, b, "lower_relevance"
        if pd.notna(rel_a) and pd.notna(rel_b) and not np.isclose(rel_a, rel_b):
            return (a, b, "lower_relevance") if rel_a < rel_b else (b, a, "lower_relevance")
        if not np.isclose(miss_a, miss_b):
            return (a, b, "higher_missing_rate") if miss_a > miss_b else (b, a, "higher_missing_rate")

        kept = min(a, b)
        removed = max(a, b)
        return removed, kept, "alphabetical_tiebreak"

    def build_log_row(
        pair,
        stage,
        action,
        step,
        removal_step=None,
        removed=None,
        kept=None,
        decision_rule=None,
    ):
        n_survivors = len(X.columns) - len(dropped)
        return {
            "step": step,
            "removal_step": removal_step,
            "stage_order": stage["stage_order"],
            "stage_name": stage["stage_name"],
            "comparison_group": pair.get("comparison_group", stage["stage_name"]),
            "action": action,
            "var_a": pair["var_a"],
            "var_b": pair["var_b"],
            "var_a_type": pair.get("var_a_type"),
            "var_b_type": pair.get("var_b_type"),
            "pair_metric": pair["pair_metric"],
            "association_value": pair["association_value"],
            "threshold": pair["threshold"],
            "relevance_a": get_relevance(pair["var_a"]),
            "relevance_b": get_relevance(pair["var_b"]),
            "missing_rate_a": missing_rate[pair["var_a"]],
            "missing_rate_b": missing_rate[pair["var_b"]],
            "removed": removed,
            "kept": kept,
            "decision_rule": decision_rule,
            "n_survivors_before": n_survivors,
            "n_survivors_after": n_survivors - 1 if action == "removed" else n_survivors,
        }

    normalized_stages = sorted(
        pair_stages,
        key=lambda stage: (stage["stage_order"], stage["stage_name"]),
    )
    pair_id = 0
    stage_pairs_by_order = {}

    for stage in normalized_stages:
        stage_pairs = []
        input_pairs = sorted(
            stage["pairs"],
            key=lambda pair: (
                -pair["association_value"],
                pair["var_a"],
                pair["var_b"],
                pair.get("comparison_group", stage["stage_name"]),
            ),
        )
        for pair in input_pairs:
            pair_id += 1
            pair_with_stage = pair.copy()
            pair_with_stage["stage_order"] = stage["stage_order"]
            pair_with_stage["stage_name"] = stage["stage_name"]
            pair_with_stage["pair_id"] = pair_id
            pair_with_stage.setdefault("comparison_group", stage["stage_name"])
            all_pairs.append(pair_with_stage)
            stage_pairs.append(pair_with_stage)
        stage_pairs_by_order[stage["stage_order"], stage["stage_name"]] = stage_pairs

    step = 0
    removal_step = 0
    processed_pair_ids = set()

    for stage in normalized_stages:
        stage_key = (stage["stage_order"], stage["stage_name"])
        pairs = stage_pairs_by_order[stage_key]

        while True:
            live_pairs = [
                pair
                for pair in pairs
                if (
                    pair["pair_id"] not in processed_pair_ids
                    and pair["var_a"] not in dropped
                    and pair["var_b"] not in dropped
                )
            ]
            if not live_pairs:
                break

            pair = sorted(
                live_pairs,
                key=lambda p: (-p["association_value"], p["var_a"], p["var_b"]),
            )[0]
            a = pair["var_a"]
            b = pair["var_b"]
            removed, kept, decision_rule = choose_removed(a, b)
            n_survivors_before = len(X.columns) - len(dropped)
            dropped.add(removed)
            step += 1
            removal_step += 1
            processed_pair_ids.add(pair["pair_id"])

            row = build_log_row(
                pair=pair,
                stage=stage,
                action="removed",
                step=step,
                removal_step=removal_step,
                removed=removed,
                kept=kept,
                decision_rule=decision_rule,
            )
            row["n_survivors_before"] = n_survivors_before
            row["n_survivors_after"] = n_survivors_before - 1
            decisions.append(row)

        for pair in pairs:
            if pair["pair_id"] in processed_pair_ids:
                continue
            if pair["var_a"] in dropped or pair["var_b"] in dropped:
                step += 1
                decisions.append(
                    build_log_row(
                        pair=pair,
                        stage=stage,
                        action="skipped_prior_removal",
                        step=step,
                        decision_rule="prior_removal",
                    )
                )
                processed_pair_ids.add(pair["pair_id"])

    survivors = [col for col in X.columns if col not in dropped]
    return survivors, all_pairs, decisions


# =========================================================
# Phase 3: Boruta-SHAP
# =========================================================

def make_shadow_features(X, cols, rng):
    """Crea variables shadow permutando cada columna original.

    Parameters
    ----------
    X : pandas.DataFrame
        Dataset base.
    cols : list[str]
        Columnas reales a permutar.
    rng : numpy.random.Generator
        Generador aleatorio ya inicializado.

    Returns
    -------
    pandas.DataFrame
        DataFrame con columnas ``shadow_<feature>``.

    Notes
    -----
    Implementacion eficiente:
    - Evita insertar columnas una a una en un DataFrame vacio.
    - Construye primero un diccionario y luego crea el DataFrame de una sola vez.
    - Mantiene dtype category cuando aplica.
    """
    shadow_dict = {}

    for col in cols:
        permuted = rng.permutation(X[col].to_numpy())

        # Buena practica: mantener dtype category si aplica. XGBoost con
        # enable_categorical necesita categorias coherentes entre real/shadow.
        if str(X[col].dtype) == "category":
            permuted = pd.Categorical(
                permuted,
                categories=X[col].cat.categories
            )

        shadow_dict[f"shadow_{col}"] = permuted

    shadow = pd.DataFrame(
        shadow_dict,
        index=X.index
    )

    return shadow


def boruta_shap(model, X, y, cols=None, n_iter=30, alpha=0.05, seed=42):
    """Ejecuta Boruta-SHAP como selector all-relevant.

    Parameters
    ----------
    model : estimator
        Modelo compatible con ``fit`` y ``shap.TreeExplainer``. En el notebook
        se usa ``XGBRegressor``.
    X : pandas.DataFrame
        Matriz de features candidatas.
    y : pandas.Series
        Target continuo.
    cols : list[str], optional
        Universo de variables reales a evaluar. Si es None, usa todas las
        columnas de X.
    n_iter : int, default=30
        Numero de iteraciones Boruta/shadow.
    alpha : float, default=0.05
        Nivel de significacion del test binomial.
    seed : int, default=42
        Semilla para permutaciones reproducibles.

    Returns
    -------
    tuple[list[str], pandas.Series, pandas.Series, pandas.DataFrame]
        ``selected_cols``: Confirmed + Tentative.
        ``status``: estado Boruta por feature.
        ``hits``: numero de veces que cada feature supera el maximo shadow.
        ``results``: tabla auditable con hits, hit_rate y status.

    Notes
    -----
    Boruta-SHAP no estima rendimiento por CV. Su objetivo es proteger variables
    con senal real frente a ruido shadow. La seleccion final se refina despues
    con estabilidad y backward selection.
    """
    if cols is None:
        cols = X.columns.tolist()

    cols = list(cols)

    # Buena practica: fallar pronto si `cols` no coincide con X. Evita que una
    # seleccion previa incompleta se convierta en un resultado silencioso.
    missing_cols = sorted(set(cols) - set(X.columns))
    assert len(missing_cols) == 0, f"Columnas no encontradas en X: {missing_cols}"

    # Resetear indices hace que permutaciones, concat y target queden
    # perfectamente alineados por posicion.
    X_base = X[cols].reset_index(drop=True).copy()
    y_base = y.reset_index(drop=True).copy()

    rng = np.random.default_rng(seed)
    hits = pd.Series(0, index=cols, dtype=int)

    for i in range(n_iter):
        # En cada iteracion se crean shadows nuevas. Si se reutilizaran, el test
        # binomial sobre hits sobrestimaria evidencia por dependencia artificial.
        shadow = make_shadow_features(X_base, cols, rng)

        Xa = pd.concat(
            [X_base, shadow.reset_index(drop=True)],
            axis=1
        )

        fitted_model = clone(model).fit(Xa, y_base)

        # SHAP importance inline (mean |SHAP| por feature). Se compara contra
        # el maximo shadow para aplicar criterio all-relevant conservador.
        explainer = shap.TreeExplainer(fitted_model)
        shap_values = explainer.shap_values(Xa)
        imp = pd.Series(
            np.abs(shap_values).mean(axis=0),
            index=Xa.columns
        )

        shadow_cols = shadow.columns.tolist()
        shadow_max = imp.loc[shadow_cols].max()

        hits.loc[cols] += (imp.loc[cols] > shadow_max).astype(int)

        if (i + 1) % 10 == 0:
            print(f"Boruta-SHAP iteracion {i + 1}/{n_iter}")

    def decide(h):
        # Test binomial de Boruta: muchos hits -> Confirmed; pocos hits ->
        # Rejected; zona no concluyente -> Tentative.
        p_greater = stats.binomtest(
            h,
            n_iter,
            0.5,
            alternative="greater"
        ).pvalue

        p_less = stats.binomtest(
            h,
            n_iter,
            0.5,
            alternative="less"
        ).pvalue

        if p_greater < alpha:
            return "Confirmed"
        elif p_less < alpha:
            return "Rejected"
        else:
            return "Tentative"

    status = hits.map(decide)

    selected_cols = status[status != "Rejected"].index.tolist()

    results = (
        pd.DataFrame({
            "feature_name": cols,
            "hits": hits.values,
            "n_iter": n_iter,
            "hit_rate": hits.values / n_iter,
            "status": status.values,
        })
        .sort_values(["status", "hit_rate"], ascending=[True, False])
        .reset_index(drop=True)
    )

    return selected_cols, status, hits, results


# =========================================================
# Phase 4: Stability Selection
# =========================================================

def stability_selection(model, X, y, strat, cols=None, n_iter=200, sample_fraction=0.7,
                        pi_thr=0.75, importance_type="gain", cover=0.95, seed=42):
    """Selecciona features estables bajo submuestreo estratificado.

    Parameters
    ----------
    model : estimator
        Modelo compatible con ``fit`` y ``get_booster().get_score``.
    X : pandas.DataFrame
        Matriz de features candidatas.
    y : pandas.Series
        Target continuo.
    strat : array-like
        Etiqueta de estratificacion usada por ``StratifiedShuffleSplit``.
    cols : list[str], optional
        Universo de variables a evaluar. Si es None, usa todas las columnas de X.
    n_iter : int, default=200
        Numero de perturbaciones/submuestras.
    sample_fraction : float, default=0.7
        Fraccion de muestra usada en cada iteracion, sin reemplazo.
    pi_thr : float, default=0.75
        Umbral minimo de frecuencia de seleccion.
    importance_type : str, default="gain"
        Tipo de importancia XGBoost usado en cada ronda.
    cover : float, default=0.95
        Cobertura acumulada de gain que define las variables votadas por ronda.
    seed : int, default=42
        Semilla para reproducibilidad del submuestreo.

    Returns
    -------
    tuple[list[str], pandas.Series, pandas.DataFrame]
        ``selected_cols``: features con estabilidad >= pi_thr.
        ``stability``: frecuencia de seleccion por feature.
        ``results``: tabla con feature y stability.

    Notes
    -----
    Esta fase mide robustez de seleccion, no performance predictiva. Por eso
    usa ``StratifiedShuffleSplit`` en lugar del K-fold compartido del notebook.
    """
    cols = X.columns.tolist() if cols is None else list(cols)
    missing = sorted(set(cols) - set(X.columns))
    assert len(missing) == 0, f"Columns not found in X: {missing}"
    # Reset por posicion: StratifiedShuffleSplit devuelve indices posicionales.
    X = X[cols].reset_index(drop=True)
    y = y.reset_index(drop=True)
    strat = pd.Series(np.asarray(strat))
    counts = pd.Series(0, index=cols, dtype=int)

    # Buena practica: Stability Selection necesita perturbaciones aleatorias
    # independientes; ShuffleSplit es mas apropiado que reutilizar KFold.
    sss = StratifiedShuffleSplit(n_splits=n_iter, train_size=sample_fraction,
                                 random_state=seed)

    for i, (idx, _) in enumerate(sss.split(X, strat), start=1):
        m = clone(model).fit(X.iloc[idx], y.iloc[idx])
        # Gain importance es no negativa y sparse: variables sin splits quedan a 0.
        score = m.get_booster().get_score(importance_type=importance_type)
        imp = pd.Series(score).reindex(cols).fillna(0.0).clip(lower=0)

        # Cobertura adaptativa: se selecciona lo necesario para explicar `cover`
        # del gain total, sin fijar un top-k arbitrario.
        s = imp.sort_values(ascending=False)              # cobertura adaptativa
        total = s.sum()
        if total > 0:
            n_keep = int((s.cumsum() / total < cover).sum()) + 1
            counts[s.index[:n_keep]] += 1

        if i % 50 == 0:
            print(f"Stability selection iteration {i}/{n_iter}")

    stability = (counts / n_iter).sort_values(ascending=False)
    selected_cols = stability[stability >= pi_thr].index.tolist()
    results = stability.reset_index()
    results.columns = ["feature", "stability"]

    print(f"Selected features (stability >= {pi_thr}): {len(selected_cols)}")
    return selected_cols, stability, results


# =========================================================
# Phase 5: Backward Selection
# =========================================================

def cv_eval(model, X, y, splits, scoring):
    """Evalua un subconjunto con CV y calcula SHAP out-of-fold.

    Parameters
    ----------
    model : estimator
        Modelo sklearn-like compatible con ``fit``.
    X : pandas.DataFrame
        Features del subconjunto actual.
    y : pandas.Series
        Target continuo.
    splits : list[tuple[array-like, array-like]]
        Indices posicionales train/validation precomputados.
    scoring : str
        Scorer sklearn. Ejemplo: ``neg_mean_absolute_error``.

    Returns
    -------
    tuple[float, float, pandas.Series]
        Score medio CV, SE corregido Nadeau-Bengio e importancia SHAP OOF.

    Notes
    -----
    Los scorers de sklearn siguen "higher is better". Con
    ``neg_mean_absolute_error``, un score mayor significa MAE menor.
    """
    _scorer = get_scorer(scoring)
    fold_scores = []
    shap_acc = np.zeros(X.shape[1])
    for tr, va in splits:                       # indices POSICIONALES
        # Buena practica: clonar modelo por fold evita fuga de estado entre fits.
        m = clone(model).fit(X.iloc[tr], y.iloc[tr])
        fold_scores.append(_scorer(m, X.iloc[va], y.iloc[va]))
        # SHAP se calcula sobre validacion, no train. Asi el ranking usado para
        # eliminar variables refleja contribucion fuera de muestra.
        sv = shap.TreeExplainer(m).shap_values(X.iloc[va])   # SHAP fuera de muestra
        shap_acc += np.abs(sv).mean(axis=0)
    fold_scores = np.asarray(fold_scores)
    n_train, n_test = len(splits[0][0]), len(splits[0][1])
    mean = fold_scores.mean()
    se = nadeau_bengio_se(fold_scores, n_train, n_test)
    shap_imp = pd.Series(shap_acc / len(splits), index=X.columns)
    return mean, se, shap_imp


def backward_selection(model, X, y, splits, scoring, min_features=1):
    """Ejecuta backward selection greedy con SHAP OOF y regla 1-SE.

    Parameters
    ----------
    model : estimator
        Modelo sklearn-like compatible con ``fit``.
    X : pandas.DataFrame
        Features candidatas iniciales.
    y : pandas.Series
        Target continuo.
    splits : list[tuple[array-like, array-like]]
        Splits CV posicionales compartidos con el notebook.
    scoring : str
        Scorer sklearn. En el notebook: ``neg_mean_absolute_error``.
    min_features : int, default=1
        Numero minimo de features hasta el que se permite reducir.

    Returns
    -------
    tuple[list[str], list[dict]]
        ``selected_features``: subconjunto elegido por regla 1-SE.
        ``history``: trayectoria completa con scores, SE, features y variable
        eliminada en cada paso.

    Notes
    -----
    En cada iteracion se elimina la feature con menor SHAP out-of-fold medio.
    La regla 1-SE elige el subconjunto mas pequeno cuyo score sigue dentro del
    margen estadistico del mejor modelo. Para scorers negativos como MAE, el
    criterio sigue funcionando porque sklearn maximiza el score.
    """
    feats = list(X.columns)
    history, step_num = [], 0
    while True:
        mean, se, imp = cv_eval(model, X[feats], y, splits, scoring)
        # Greedy backward: elimina menor importancia OOF. Es O(p) iteraciones,
        # mucho mas barato que probar todos los subconjuntos.
        removed = imp.idxmin() if len(feats) > min_features else None
        history.append({
            "step": step_num, "features": list(feats),
            "cv_score_mean": mean, "cv_score_se": se,
            "removed_feature": removed,
            "removed_importance": (imp.loc[removed] if removed else None),
        })
        if len(feats) <= min_features:
            break
        feats = [f for f in feats if f != removed]
        step_num += 1
        if step_num % 5 == 0:
            print(f"  step {step_num}: {len(feats)} feats, "
                  f"score={mean:.6f} (SE={se:.6f}), removed={removed}")
    # Scikit-learn scorers siguen convencion "higher is better"; por eso
    # neg_mean_absolute_error se maximiza aunque represente menor MAE.
    best = max(history, key=lambda h: h["cv_score_mean"])  # mejor score
    # Regla 1-SE conservadora: escoger el subconjunto mas pequeno cuyo borde
    # inferior no cae por debajo del mejor score menos 1 SE.
    threshold = best["cv_score_mean"] - best["cv_score_se"]
    chosen = min((h for h in history if h["cv_score_mean"] - h["cv_score_se"] >= threshold),
                 key=lambda h: len(h["features"]))
    return chosen["features"], history


# =========================================================
# Phase 6: Evaluation
# =========================================================

def evaluate_phase(phase_name, features, model, df, y, splits, scoring, n_train_cv, n_test_cv):
    """Evalua una fase del pipeline con los splits compartidos.

    Parameters
    ----------
    phase_name : str
        Nombre de fase para trazabilidad.
    features : list[str]
        Features supervivientes de esa fase.
    model : estimator
        Modelo sklearn-like compatible con ``cross_validate``.
    df : pandas.DataFrame
        Dataset completo; se seleccionan explicitamente ``features``.
    y : pandas.Series
        Target continuo.
    splits : list[tuple[array-like, array-like]]
        Splits CV posicionales precomputados.
    scoring : str
        Scorer sklearn usado para performance.
    n_train_cv : int
        Tamano de train en cada split.
    n_test_cv : int
        Tamano de validation en cada split.

    Returns
    -------
    tuple[dict, pandas.DataFrame, pandas.DataFrame]
        ``summary``: metricas agregadas de la fase.
        ``importances``: importancias XGBoost promedio por fold.
        ``cv_results``: metricas fold-a-fold para auditoria.

    Notes
    -----
    Las importancias son diagnosticas. La comparacion de fases debe apoyarse
    en MAE, SE corregido y resultados fold-a-fold.
    """
    # Buena practica: seleccionar columnas explicitamente por fase evita que
    # columnas auxiliares de estratificacion entren accidentalmente al modelo.
    X = df.loc[:, features].copy()

    # n_jobs=1 evita sobreparalelizar: XGBoost ya usa n_jobs interno.
    res = cross_validate(
        estimator=model, X=X, y=y,
        cv=splits, scoring=scoring,
        return_train_score=True, n_jobs=1,
        return_estimator=True,
    )

    mae_val = -res["test_score"]
    mae_train = -res["train_score"]
    # El SE corregido se reporta junto al MAE para comparar fases con regla
    # practica de no degradacion estadisticamente relevante.
    se_nb = nadeau_bengio_se(-res["test_score"], n_train_cv, n_test_cv)

    mae_val_mean = mae_val.mean()
    mae_val_std = mae_val.std()
    mae_train_mean = mae_train.mean()
    gap = mae_val_mean - mae_train_mean
    cv_pct = 100 * mae_val_std / mae_val_mean if mae_val_mean != 0 else np.nan

    if mae_val_std > 0:
        z = (mae_val - mae_val_mean) / mae_val_std
        n_outliers = int(np.sum(np.abs(z) > 2))
    else:
        z = np.zeros_like(mae_val)
        n_outliers = 0

    # Feature importances promedio entre folds: diagnostico, no criterio de
    # seleccion final en esta fase.
    fi_rows = []
    for i, est in enumerate(res["estimator"]):
        fi_rows.append(pd.DataFrame({
            "feature_name": features,
            "importance": est.feature_importances_,
            "fold": i,
        }))

    importances = (
        pd.concat(fi_rows, ignore_index=True)
        .groupby("feature_name", as_index=False)
        .agg(
            importance_mean=("importance", "mean"),
            importance_std=("importance", "std"),
            importance_min=("importance", "min"),
            importance_max=("importance", "max"),
        )
        .sort_values("importance_mean", ascending=False)
        .reset_index(drop=True)
    )

    # CV por fold: permite auditar outliers y comparar fases con los mismos
    # splits, no solo con una media agregada.
    cv_results = pd.DataFrame({
        "fold": np.arange(len(mae_val)),
        "mae_train": mae_train,
        "mae_validation": mae_val,
        "gap_train_validation": mae_val - mae_train,
        "z_validation_mae": z,
        "is_outlier_fold": np.abs(z) > 2,
    })

    summary = {
        "phase": phase_name,
        "n_vars": len(features),
        "mae_val_mean": round(mae_val_mean, 6),
        "mae_val_std": round(mae_val_std, 6),
        "se_nb": round(se_nb, 6),
        "mae_train_mean": round(mae_train_mean, 6),
        "gap": round(gap, 6),
        "cv_pct": round(cv_pct, 2),
        "n_outlier_folds": n_outliers,
    }

    return summary, importances, cv_results
