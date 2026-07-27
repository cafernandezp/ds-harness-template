from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd


def _normalize_for_distinct(x: Any) -> Any:
    """Normalize list/tuple/ndarray values for distinct counting.

    Args:
        x: Input cell value.

    Returns:
        A hashable representation suitable for distinct counting.

    Examples:
        >>> _normalize_for_distinct([1, 2])
        '[1, 2]'
        >>> _normalize_for_distinct(np.array([1, 2]))
        '[1 2]'
        >>> _normalize_for_distinct("A")
        'A'
    """
    if isinstance(x, np.ndarray):
        return np.array2string(x)
    if isinstance(x, (list, tuple)):
        return str(x)
    return x


def describe_cols(
    df: pd.DataFrame,
    cols_to_analyze: Sequence[str] | None = None,
    return_df: bool = False,
) -> pd.DataFrame | None:
    """Describe selected DataFrame columns for exploratory analysis.

    For all selected columns, computes:
    - dtype
    - number of nulls

    For non-numeric columns, also computes:
    - number of distinct non-null values

    Args:
        df: Input pandas DataFrame.
        cols_to_analyze: Optional subset of columns to analyze. If None,
            all columns are analyzed.
        return_df: If True, returns a summary DataFrame. If False,
            prints the summary and returns None.

    Returns:
        A pandas DataFrame with the summary if ``return_df=True``.
        Otherwise, None.

    Raises:
        TypeError: If ``df`` is not a pandas DataFrame.
        KeyError: If any requested column is not present in ``df``.

    Examples:
        >>> sample_df = pd.DataFrame({
        ...     "num": [1, 2, None],
        ...     "obj": ["a", "b", "a"],
        ... })
        >>> result = describe_cols(sample_df, return_df=True)
        >>> list(result.columns)
        ['col', 'dtype', 'n_nulls', 'n_distinct_values']
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    cols: list[str] = (
        list(cols_to_analyze) if cols_to_analyze is not None else df.columns.tolist()
    )

    missing_cols: list[str] = [col for col in cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Columns not found in DataFrame: {missing_cols}")

    numeric_columns: list[str] = (
        df[cols].select_dtypes(include=["number"]).columns.tolist()
    )

    rows: list[dict[str, Any]] = []

    for col in sorted(cols):
        series: pd.Series = df[col]
        dtype: str = str(series.dtype)
        n_nulls: int = int(series.isna().sum())

        row: dict[str, Any] = {
            "col": col,
            "dtype": dtype,
            "n_nulls": n_nulls,
            "n_distinct_values": None,
        }

        if col not in numeric_columns:
            distinct_values: set[Any] = set()

            for x in series:
                if x is None:
                    continue

                if not isinstance(x, (list, tuple, np.ndarray)) and pd.isna(x):
                    continue

                distinct_values.add(_normalize_for_distinct(x))

            row["n_distinct_values"] = len(distinct_values)

        rows.append(row)

    result_df: pd.DataFrame = pd.DataFrame(rows)

    if return_df:
        return result_df
    # TODO: Mejorar el formato de salida para que quede mas alineado
    display_df: pd.DataFrame = (
        result_df.rename(
            columns={
                "col": "column",
                "n_distinct_values": "n_unique",
            }
        )
        .loc[:, ["column", "dtype", "n_nulls", "n_unique"]]
        .copy()
    )

    display_df["column"] = display_df["column"].astype(str)
    display_df["dtype"] = display_df["dtype"].astype(str)
    display_df["n_nulls"] = display_df["n_nulls"].map(lambda x: str(int(x)))
    display_df["n_unique"] = display_df["n_unique"].map(
        lambda x: "-" if pd.isna(x) else str(int(x))
    )

    column_width: int = (
        max(
            len("column"),
            display_df["column"].str.len().max(),
        )
        + 4
    )
    dtype_width: int = (
        max(
            len("dtype"),
            display_df["dtype"].str.len().max(),
        )
        + 4
    )
    n_nulls_width: int = (
        max(
            len("n_nulls"),
            display_df["n_nulls"].str.len().max(),
        )
        + 4
    )
    n_unique_width: int = (
        max(
            len("n_unique"),
            display_df["n_unique"].str.len().max(),
        )
        + 2
    )

    header: str = (
        f"{'column':<{column_width}}"
        f"{'dtype':<{dtype_width}}"
        f"{'n_nulls':>{n_nulls_width}}"
        f"{'n_unique':>{n_unique_width}}"
    )

    print(f"shape df: {df.shape}\n")
    print(header)
    print("-" * len(header))

    for _, row in display_df.iterrows():
        print(
            f"{row['column']:<{column_width}}"
            f"{row['dtype']:<{dtype_width}}"
            f"{row['n_nulls']:>{n_nulls_width}}"
            f"{row['n_unique']:>{n_unique_width}}"
        )

    return None
