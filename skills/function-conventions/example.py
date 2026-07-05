"""
Worked example for skills/function-conventions/.

Demonstrates: `df` as the standard DataFrame argument name, `seed` as the
standard argument name for randomness, docstring depth calibrated to
function complexity, and extracting only one helper where it's actually
warranted — not fragmenting further.
"""

import numpy as np
import pandas as pd


def spearman_filter(df: pd.DataFrame, threshold: float = 0.85) -> pd.DataFrame:
    """
    Drop one column from every pair of features with |Spearman correlation| above threshold.

    Args:
        df: Feature matrix, one column per candidate feature.
        threshold: Correlation above which one of the two columns is dropped.

    Returns:
        A copy of `df` with the correlated columns removed.
    """
    corr = df.corr(method="spearman").abs()
    to_drop = _columns_above_threshold(corr, threshold)
    return df.drop(columns=to_drop)


def _columns_above_threshold(corr: pd.DataFrame, threshold: float) -> list[str]:
    """Returns the second column name of each pair whose correlation exceeds threshold."""
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    return [col for col in upper.columns if any(upper[col] > threshold)]


def shuffle_rows(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """
    Shuffle the rows of a DataFrame reproducibly.

    Args:
        df: DataFrame to shuffle.
        seed: Random seed controlling the shuffle order.

    Returns:
        A new DataFrame with rows in randomized order.
    """
    # pandas' own parameter is called random_state — we keep our
    # signature's `seed` name and pass it through under pandas' name.
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)
