# Correlation between features and explainability

import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression

def compute_vif(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute VIF for all columns in a numeric DataFrame.
    """
    X = df.select_dtypes(include="number").copy()

    vif = pd.DataFrame({
        "feature": X.columns,
        "VIF": [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    })

    vif["level"] = np.select(
        [
            vif["VIF"] < 5,
            vif["VIF"] < 10,
        ],
        [
            "Low",
            "Moderate",
        ],
        default="High",
    )

    return vif.sort_values("VIF", ascending=False).reset_index(drop=True)


def explain_feature_vif (
    df: pd.DataFrame,
    feature: str,
    n_repeats: int = 20,
    random_state: int = 42,
    n_jobs: int = -1,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute the VIF of one feature and explain which remaining variables
    are most relevant to reconstruct it using Permutation Feature Importance.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing numeric variables.
    feature : str
        Variable whose VIF will be computed and explained.
    n_repeats : int, default=20
        Number of permutations per predictor.
    random_state : int, default=42
        Random seed.
    n_jobs : int, default=-1
        Number of parallel jobs used by permutation importance.

    Returns
    -------
    summary : pd.DataFrame
        One-row table containing the explained feature, R² and VIF.
    explainability : pd.DataFrame
        Predictor-level permutation importance results.
    """
    if feature not in df.columns:
        raise ValueError(f"Feature '{feature}' does not exist in the DataFrame.")

    numeric_df = df.select_dtypes(include="number").copy()

    if feature not in numeric_df.columns:
        raise TypeError(f"Feature '{feature}' must be numeric.")

    if numeric_df.shape[1] < 2:
        raise ValueError("At least two numeric variables are required.")

    cols_with_nulls = numeric_df.columns[numeric_df.isna().any()].tolist()
    if cols_with_nulls:
        raise ValueError(
            "Missing values detected. Impute or remove them before computing VIF. "
            f"Columns with nulls: {cols_with_nulls}"
        )

    constant_cols = [
        col
        for col in numeric_df.columns
        if numeric_df[col].nunique(dropna=False) <= 1
    ]
    if constant_cols:
        raise ValueError(
            "Constant columns detected. Remove them before computing VIF. "
            f"Constant columns: {constant_cols}"
        )

    X = numeric_df.drop(columns=[feature])
    y = numeric_df[feature]

    model = LinearRegression()
    model.fit(X, y)

    r2 = model.score(X, y)

    if np.isclose(r2, 1.0):
        vif = np.inf
    else:
        vif = 1.0 / (1.0 - r2)

    pfi = permutation_importance(
        estimator=model,
        X=X,
        y=y,
        scoring="r2",
        n_repeats=n_repeats,
        random_state=random_state,
        n_jobs=n_jobs,
    )

    explainability = pd.DataFrame({
        "predictor": X.columns,
        "pfi_mean": pfi.importances_mean,
        "pfi_std": pfi.importances_std,
    })

    positive_importance = explainability["pfi_mean"].clip(lower=0)
    total_positive_importance = positive_importance.sum()

    if total_positive_importance > 0:
        explainability["pfi_relative"] = (
            positive_importance / total_positive_importance
        )
    else:
        explainability["pfi_relative"] = 0.0

    explainability = (
        explainability
        .sort_values("pfi_mean", ascending=False)
        .reset_index(drop=True)
    )

    summary = pd.DataFrame({
        "feature": [feature],
        "r2_auxiliary_regression": [r2],
        "vif": [vif],
        "n_predictors": [X.shape[1]],
    })

    return summary, explainability


#Example of use:
#vif = compute_vif(df[selected_features])
#display(vif)

#vif_summary, vif_explainability=explain_feature_vif(df=df[selected_features], feature="cases_open_hipotecario", n_repeats=20, random_state=SEED, n_jobs=-1)
#display(vif_summary)
#display(vif_explainability)



