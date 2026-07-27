from __future__ import annotations

import math
from typing import Literal, Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure

AggFunc = Literal["sum", "mean", "avg", "median", "min", "max"]


def plot_exploratory_timeseries(
    *,
    df: pd.DataFrame,
    date_col: str,
    value_col: Optional[str] = None,
    agg: Literal["count", "sum", "avg", "median"] = "count",
    legend_col: Optional[str] = None,
    title: Optional[str] = None,
    figsize: tuple[int, int] = (14, 5),
    ax: Optional[Axes] = None,
) -> None:
    """Plot a simple exploratory time series with explicit x-axis labels.

    Args:
        df: Input dataframe.
        date_col: Column used as time axis.
        value_col: Column used for aggregation. Optional for ``agg="count"``.
        agg: Aggregation operation. Supported values: ``"count"``, ``"sum"``,
            ``"avg"`` (mean), and ``"median"``.
        legend_col: Optional column used to split the lines.
        title: Optional chart title.
        figsize: Matplotlib figure size if `ax` is not provided.
        ax: Optional existing matplotlib axes.

    Raises:
        KeyError: If required columns are missing.
        ValueError: If `agg` is not ``"count"`` and `value_col` is None.

    Examples:
        >>> sample = pd.DataFrame(
        ...     {
        ...         "date": ["2024-01", "2024-01", "2024-02"],
        ...         "agency": ["A", "A", "B"],
        ...         "value": [1, 2, 3],
        ...     }
        ... )
        >>> plot_exploratory(
        ...     df=sample,
        ...     date_col="date",
        ...     value_col="value",
        ...     agg="sum",
        ...     legend_col="agency",
        ...     title="Example",
        ... )
    """
    if agg != "count" and value_col is None:
        raise ValueError(f"`value_col` is required when `agg='{agg}'`.")

    required_cols: list[str] = [date_col]
    if legend_col is not None:
        required_cols.append(legend_col)
    if value_col is not None:
        required_cols.append(value_col)

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing columns: {missing_cols}")

    work = df.loc[:, required_cols].copy()
    work["_date_label"] = work[date_col].astype(str)
    work["_date_sort"] = pd.to_datetime(work[date_col], errors="coerce")
    work = work.dropna(subset=["_date_sort"])

    date_labels = (
        work[["_date_sort", "_date_label"]]
        .drop_duplicates(subset=["_date_sort"])
        .sort_values("_date_sort")
        .set_index("_date_sort")
    )

    group_cols = ["_date_sort"]
    if legend_col is not None:
        group_cols.append(legend_col)

    if agg == "count":
        if value_col is None:
            grouped = work.groupby(group_cols).size()
        else:
            grouped = work.groupby(group_cols)[value_col].count()
    elif agg == "sum":
        grouped = work.groupby(group_cols)[value_col].sum()
    elif agg == "avg":
        grouped = work.groupby(group_cols)[value_col].mean()
    else:  # agg == "median"
        grouped = work.groupby(group_cols)[value_col].median()

    if legend_col is None:
        plot_df = grouped.rename("value").to_frame()
    else:
        plot_df = grouped.unstack(fill_value=0)

    plot_df = plot_df.sort_index()

    x_positions = list(range(len(plot_df)))
    fallback_labels = pd.Series(
        plot_df.index.astype(str),
        index=plot_df.index,
    )
    x_labels = (
        date_labels.reindex(plot_df.index)["_date_label"]
        .fillna(fallback_labels)
        .tolist()
    )

    if ax is None:
        _, ax = plt.subplots(figsize=figsize)

    for column in plot_df.columns:
        label = str(column) if legend_col is not None else None
        ax.plot(
            x_positions,
            plot_df[column].to_numpy(),
            linestyle="--",
            marker="o",
            label=label,
        )

    if title is not None:
        ax.set_title(title)

    ax.set_xlabel(date_col)
    ax.set_ylabel(agg)

    ax.set_xticks(x_positions[::2])
    ax.set_xticklabels(x_labels[::2], rotation=45, ha="right", fontsize=8)

    ax.grid(axis="y", linestyle="--", alpha=0.6)
    ax.set_axisbelow(True)

    if legend_col is not None:
        ax.legend()

    plt.tight_layout()
    plt.show()


def plot_category_panels(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    legend_col: str,
    n_per_page: int,
    aggfunc: AggFunc = "sum",
    ncols: int = 3,
    ylim_lower: float | None = None,
    ylim_upper: float | None = None,
    page_title: str | None = None,
    figsize_per_subplot: tuple[float, float] = (5.0, 3.0),
) -> list[Figure]:
    """Plot paginated time-series panels by category using a shared y-axis scale.

    Each unique value in `legend_col` is plotted in its own subplot panel. Panels
    are split across pages according to `n_per_page`. All panels share the same
    y-axis range so categories can be compared visually on the same scale.

    If `ylim_lower` and `ylim_upper` are not provided, they are inferred from the
    aggregated `value_col` values and expanded by a 5% margin below the minimum
    and above the maximum.

    Args:
        df: Input dataframe.
        date_col: Column containing date-like values for the x-axis.
        value_col: Column containing numeric values for the y-axis.
        legend_col: Column whose unique values define one panel each.
        n_per_page: Maximum number of panels per page.
        aggfunc: Aggregation used when repeated `(legend_col, date_col)` pairs
            exist.
        ncols: Number of subplot columns per page.
        ylim_lower: Optional lower y-axis bound applied to all panels.
        ylim_upper: Optional upper y-axis bound applied to all panels.
        page_title: Optional page title. If `None`, `legend_col` is used.
        figsize_per_subplot: Base `(width, height)` size per subplot.

    Returns:
        A list of matplotlib figures, one per page.

    Raises:
        TypeError: If `df` is not a pandas DataFrame.
        ValueError: If required columns are missing or arguments are invalid.

    Examples:
        >>> import pandas as pd
        >>> sample_df = pd.DataFrame(
        ...     {
        ...         "fecha": ["2025-01-01", "2025-01-02", "2025-01-01"],
        ...         "valor": [10, 20, 15],
        ...         "agencia": ["A", "A", "B"],
        ...     }
        ... )
        >>> figs = plot_category_panels(
        ...     df=sample_df,
        ...     date_col="fecha",
        ...     value_col="valor",
        ...     legend_col="agencia",
        ...     n_per_page=2,
        ... )
        >>> len(figs)
        1
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")

    required_cols: set[str] = {date_col, value_col, legend_col}
    missing_cols: set[str] = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {sorted(missing_cols)}.")

    if n_per_page <= 0:
        raise ValueError("n_per_page must be greater than 0.")

    if ncols <= 0:
        raise ValueError("ncols must be greater than 0.")

    data: pd.DataFrame = df[[date_col, value_col, legend_col]].dropna().copy()
    if data.empty:
        return []

    try:
        data[date_col] = pd.to_datetime(data[date_col], errors="raise")
    except Exception as exc:
        raise ValueError(
            f"Column '{date_col}' could not be converted to datetime."
        ) from exc

    try:
        data[value_col] = pd.to_numeric(data[value_col], errors="raise")
    except Exception as exc:
        raise ValueError(
            f"Column '{value_col}' could not be converted to numeric."
        ) from exc

    pandas_aggfunc: str = "mean" if aggfunc == "avg" else aggfunc
    data = (
        data.groupby([legend_col, date_col], as_index=False)[value_col]
        .agg(pandas_aggfunc)
        .sort_values([legend_col, date_col])
    )

    if data.empty:
        return []

    value_min: float = float(data[value_col].min())
    value_max: float = float(data[value_col].max())

    if ylim_lower is None or ylim_upper is None:
        value_range: float = value_max - value_min
        margin: float = (
            value_range * 0.05 if value_range > 0 else max(abs(value_max) * 0.05, 1.0)
        )
        computed_lower: float = value_min - margin
        computed_upper: float = value_max + margin

        if ylim_lower is None:
            ylim_lower = computed_lower
        if ylim_upper is None:
            ylim_upper = computed_upper

    if ylim_lower >= ylim_upper:
        raise ValueError("ylim_lower must be strictly smaller than ylim_upper.")

    grouped_data: dict[str, pd.DataFrame] = {
        str(category): group.sort_values(date_col)
        for category, group in data.groupby(legend_col)
    }
    categories: list[str] = sorted(grouped_data.keys())

    total_pages: int = math.ceil(len(categories) / n_per_page)
    title_prefix: str = page_title or f"{aggfunc} of {value_col} by {legend_col}"
    figures: list[Figure] = []

    for page_idx in range(total_pages):
        start: int = page_idx * n_per_page
        end: int = start + n_per_page
        page_categories: list[str] = categories[start:end]

        n_panels: int = len(page_categories)
        page_ncols: int = min(ncols, n_panels)
        nrows: int = math.ceil(n_panels / page_ncols)

        fig, axes = plt.subplots(
            nrows=nrows,
            ncols=page_ncols,
            figsize=(
                figsize_per_subplot[0] * page_ncols,
                figsize_per_subplot[1] * nrows,
            ),
            sharex=True,
            sharey=True,
            squeeze=False,
        )

        flat_axes = axes.ravel()

        for ax, category in zip(flat_axes, page_categories):
            subset: pd.DataFrame = grouped_data[category]
            ax.plot(subset[date_col], subset[value_col], linewidth=1.8)
            ax.set_title(category, fontsize=11)
            ax.set_ylim(ylim_lower, ylim_upper)
            ax.grid(True, alpha=0.6)

        for ax in flat_axes[n_panels:]:
            ax.set_visible(False)

        fig.suptitle(
            f"{title_prefix} — página {page_idx + 1}/{total_pages}",
            fontsize=16,
        )
        fig.supxlabel(date_col)
        fig.supylabel(value_col)
        fig.autofmt_xdate(rotation=45, ha="right")
        fig.tight_layout(rect=(0.02, 0.03, 1.0, 0.95))

        figures.append(fig)
        plt.show()

    return figures


def plot_hist_grid_by_category(
    *,
    df: pd.DataFrame,
    value_col: str,
    legend_col: str,
    title: Optional[str] = None,
    figsize: tuple[int, int] = (15, 10),
) -> None:
    """
    Grafica una grilla de histogramas de `value_col`, un subplot por cada categoría de `legend_col`.

    Supuestos de diseño:
    - 3 columnas fijas en la grilla
    - sharex=True y sharey=True
    - kde=True
    - stat="density"
    - se excluyen nulos en `value_col` y `legend_col`
    """
    if value_col not in df.columns:
        raise KeyError(f"La columna `{value_col}` no existe en el DataFrame.")
    if legend_col not in df.columns:
        raise KeyError(f"La columna `{legend_col}` no existe en el DataFrame.")

    df_plot = df[[value_col, legend_col]].dropna().copy()

    if df_plot.empty:
        raise ValueError("No hay datos disponibles para graficar tras eliminar nulos.")

    categories = sorted(df_plot[legend_col].unique())

    if len(categories) == 0:
        raise ValueError(f"No hay categorías válidas en `{legend_col}` para graficar.")

    n_cols = 3
    n_rows = math.ceil(len(categories) / n_cols)

    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=figsize,
        sharex=True,
        sharey=True,
    )
    axes = axes.flatten() if hasattr(axes, "flatten") else [axes]

    xmin = df_plot[value_col].min()
    xmax = df_plot[value_col].max()

    for ax_i, category in zip(axes, categories):
        tmp = df_plot.loc[df_plot[legend_col] == category, value_col]

        sns.histplot(
            tmp,
            ax=ax_i,
            kde=True,
            stat="density",
        )

        ax_i.set_xlim(xmin, xmax)
        ax_i.set_title(f"{legend_col}: {category}")
        ax_i.set_xlabel(value_col)
        ax_i.set_ylabel("Densidad")

    for ax_i in axes[len(categories) :]:
        ax_i.axis("off")

    if title is None:
        title = f"Distribución de {value_col} por {legend_col}"

    fig.suptitle(title, fontsize=14)
    plt.tight_layout()
    plt.show()


def plot_kde_grid_vs_reference(
    *,
    df: pd.DataFrame,
    value_col: str,
    legend_col: str,
    label_name_reference: str,
    title: Optional[str] = None,
    n_cols: int = 3,
    figsize: tuple[int, int] = (15, 10),
) -> None:
    """
    Grafica una grilla de curvas KDE de `value_col`, comparando una categoría
    de referencia contra cada una de las demás categorías de `legend_col`.

    Supuestos de diseño:
    - `sharex=True` y `sharey=True`
    - `fill=True`
    - `common_norm=False` para comparar la forma de la distribución y no el tamaño muestral
    - `common_grid=True` para evaluar ambas curvas sobre la misma malla
    - `cut=0` para no extender la KDE fuera del rango observado
    - se excluyen nulos en `value_col` y `legend_col`

    Args:
        df: DataFrame de entrada.
        value_col: Columna numérica cuya distribución se quiere comparar.
        legend_col: Columna categórica que define los grupos a comparar.
        label_name_reference: Categoría de referencia dentro de `legend_col`.
        title: Título general del gráfico. Si es `None`, se genera automáticamente.
        n_cols: Número de columnas de la grilla. Por defecto, 3.
        figsize: Tamaño total de la figura.

    Raises:
        KeyError: Si `value_col` o `legend_col` no existen en el DataFrame.
        ValueError: Si no hay datos tras eliminar nulos, si la categoría de referencia
            no existe, si no hay categorías para comparar, si `n_cols < 1`,
            o si `value_col` tiene un único valor.

    Example:
        plot_kde_grid_vs_reference(
            df=df,
            value_col=target_name,
            legend_col="target_stages_considered",
            label_name_reference="HIPOTECARIO",
            title=f"{target_name} - HIPOTECARIO vs resto",
        )
    """

    if value_col not in df.columns:
        raise KeyError(f"La columna `{value_col}` no existe en el DataFrame.")
    if legend_col not in df.columns:
        raise KeyError(f"La columna `{legend_col}` no existe en el DataFrame.")
    if n_cols < 1:
        raise ValueError("`n_cols` debe ser mayor o igual a 1.")

    df_plot = df[[value_col, legend_col]].dropna().copy()

    if df_plot.empty:
        raise ValueError("No hay datos disponibles para graficar tras eliminar nulos.")

    categories = sorted(df_plot[legend_col].unique())

    if label_name_reference not in categories:
        raise ValueError(
            f"`label_name_reference={label_name_reference}` no existe en `{legend_col}`."
        )

    categories_compare = [cat for cat in categories if cat != label_name_reference]

    if len(categories_compare) == 0:
        raise ValueError(
            f"No hay categorías distintas de `{label_name_reference}` para comparar."
        )

    xmin = df_plot[value_col].min()
    xmax = df_plot[value_col].max()

    if xmin == xmax:
        raise ValueError(
            f"`{value_col}` tiene un único valor. No es posible graficar KDE."
        )

    n_rows = math.ceil(len(categories_compare) / n_cols)

    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=figsize,
        sharex=True,
        sharey=True,
    )
    axes = axes.flatten() if hasattr(axes, "flatten") else [axes]

    for ax_i, category in zip(axes, categories_compare):
        tmp = df_plot.loc[
            df_plot[legend_col].isin([label_name_reference, category])
        ].copy()

        ref_values = tmp.loc[tmp[legend_col] == label_name_reference, value_col]
        comp_values = tmp.loc[tmp[legend_col] == category, value_col]

        n_ref = ref_values.shape[0]
        n_comp = comp_values.shape[0]

        # Fallback robusto si alguna de las dos series no tiene variación suficiente
        if ref_values.nunique() < 2 or comp_values.nunique() < 2:
            sns.histplot(
                data=tmp,
                x=value_col,
                hue=legend_col,
                hue_order=[label_name_reference, category],
                ax=ax_i,
                kde=False,
                stat="density",
                common_norm=False,
                element="step",
            )
        else:
            sns.kdeplot(
                data=tmp,
                x=value_col,
                hue=legend_col,
                hue_order=[label_name_reference, category],
                ax=ax_i,
                fill=True,
                common_norm=False,
                common_grid=True,
                cut=0,
                clip=(xmin, xmax),
            )

        legend = ax_i.get_legend()
        if legend is not None:
            legend.set_title(None)
            for text in legend.get_texts():
                text.set_fontsize(8)

        ax_i.set_xlim(xmin, xmax)
        ax_i.set_title(
            f"{label_name_reference} vs {category}\n(n_ref={n_ref}, n_comp={n_comp})"
        )
        ax_i.set_xlabel(value_col)
        ax_i.set_ylabel("Densidad")

    for ax_i in axes[len(categories_compare) :]:
        ax_i.axis("off")

    if title is None:
        title = f"Distribución de {value_col}: {label_name_reference} vs resto"

    fig.suptitle(title, fontsize=14)
    plt.tight_layout(rect=(0, 0, 1, 0.96))
    plt.show()
