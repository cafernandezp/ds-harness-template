# ============================================================
# Introducción al flujo de análisis PSI
# ============================================================
# Este conjunto de funciones realiza un análisis del Population Stability Index (PSI) para comparar distribuciones entre
# dos conjuntos de datos (referencia y actual). Proporciona herramientas para:
#
# 1. **Binning de datos**:
#    - Soporta variables numéricas y categóricas.
#    - Maneja valores NaN y valores especiales (`special_values`), agrupándolos en bins separados si corresponde.
#
# 2. **Cálculo del PSI**:
#    - Incluye flexibilidad para excluir valores especiales (`exclude_special_values`).
#    - Proporciona el PSI total y el PSI por bin.
#
# 3. **Resultados detallados**:
#    - `psi_results`: Resumen del PSI total por variable con su tipo de binning.
#    - `psi_stats`: Detalles de los bins para cada variable, incluyendo conteos, distribuciones y PSI por bin.
#
# Funciones principales:
# - `standardize_nan_values`: Estandariza valores "NaN" representados de manera inconsistente.
# - `calculate_bins`: Agrupa las observaciones en bins, calculando frecuencias y distribuciones.
# - `calculate_psi`: Calcula el PSI total y actualiza el DataFrame con valores de PSI por bin.
# - `analyze_variable`: Realiza el análisis de una sola variable.
# - `analyze_dataset`: Analiza múltiples variables y retorna resultados agregados.
# - `save_psi_plots_to_pdf`: Genera gráficos para cada variable y los guarda en un archivo PDF.
# ============================================================


# Opcionales recomendados
import logging  # para sustituir print() por logging.info(), etc.

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

# anotaciones de tipo disponibles via typing si se necesitan


def infer_objects_compatible(series):
    """
    Ejecuta infer_objects manteniendo compatibilidad entre versiones de pandas.

    pandas recientes soportan copy=False; pandas antiguas no.
    """
    try:
        return series.infer_objects(copy=False)
    except TypeError as exc:
        if "copy" not in str(exc):
            raise
        return series.infer_objects()


def standardize_nan_values(df, column, binning_type):
    """
    Standardizes NaN-like values in a DataFrame column.

    Args:
        df (DataFrame): Input DataFrame.
        column (str): Column name to standardize.
        binning_type (str): 'percentiles' o 'categorical'.

    Returns:
        pd.Series: Series with standardized NaN values (and for categoricals, as "nan").
    """
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found in DataFrame.")

    # patrones para detectar NaN-like
    patterns = [r"^\s*nan\s*$", r"^\s*Na\s*$", r"^\s*NAN\s*$", r"^\s*$"]

    # Verificar el tipo de datos de la columna
    if binning_type == "percentiles":
        # Para columnas numéricas, solo reemplazar valores NaN-like con np.nan
        return df[column].replace(to_replace=patterns, value=np.nan, regex=True)
    elif binning_type == "categorical":
        # Para columnas no numéricas, reemplazar valores NaN-like y llenar con "NaN"
        # convertimos a object antes de fillna para no chocar con Int32/EAs
        s = (
            df[column]
            .replace(to_replace=patterns, value=np.nan, regex=True)
            .astype("string")
        )

        return s.fillna("nan")

    else:
        raise ValueError(f"Unsupported binning_type: {binning_type}")


def calculate_bins(
    data, data_ref, column, binning_type, breaks=None, num_perc=10, special_values=None
):
    """
    Creates bins for a column and calculates frequencies in both datasets, including handling of NaN and special values.

    Args:
        data (pd.DataFrame): The actual dataset.
        data_ref (pd.DataFrame): The reference dataset.
        column (str): Name of the column to bin.
        binning_type (str): One of 'percentiles', 'breaks', or 'categorical'.
        breaks (Optional[List[float]]): Predefined breakpoints for 'breaks' binning (default: None).
        num_perc (int): Number of percentiles to use when binning by percentiles (default: 10).
        special_values (Optional[List]): List of values to treat as special and separate into their own bin (default: None).

    Returns:
        pd.DataFrame: A DataFrame with columns ['bin', 'count_ref', 'count_data', 'dist_ref', 'dist_data'] summarizing the bins.
    """

    # Estandarizar en ambos datasets
    data = data.copy()  # evita vistas
    data_ref = data_ref.copy()

    std_series = standardize_nan_values(data, column, binning_type)
    std_series_ref = standardize_nan_values(data_ref, column, binning_type)

    data = data.drop(columns=[column], errors="ignore")
    data_ref = data_ref.drop(columns=[column], errors="ignore")

    data.loc[:, column] = std_series
    data_ref.loc[:, column] = std_series_ref

    # data[column] = standardize_nan_values(data, column, binning_type)
    # data_ref[column] = standardize_nan_values(data_ref, column, binning_type)

    # Manejar valores especiales
    if special_values:
        data_ref = data_ref.drop(columns=["is_special"], errors="ignore")
        data = data.drop(columns=["is_special"], errors="ignore")

        data_ref["is_special"] = data_ref[column].isin(special_values).astype("boolean")
        data["is_special"] = data[column].isin(special_values).astype("boolean")

        special_data_ref = data_ref[data_ref["is_special"]]
        special_data = data[data["is_special"]]

        # normal_data_ref = data_ref[~data_ref["is_special"]]
        # normal_data = data[~data["is_special"]]
        normal_data_ref = data_ref.loc[~data_ref["is_special"]].copy()
        normal_data = data.loc[~data["is_special"]].copy()
    else:
        normal_data_ref = data_ref
        normal_data = data
        special_data_ref = special_data = pd.DataFrame()

    # Manejo de variables categóricas
    if binning_type == "categorical":
        # normal_data_ref["bin"] = normal_data_ref[column].astype(str).fillna("nan")
        # normal_data["bin"] = normal_data[column].astype(str).fillna("nan")
        tmp_ref = normal_data_ref[column].astype(str).fillna("nan")
        normal_data_ref.loc[:, "bin"] = infer_objects_compatible(tmp_ref)

        tmp = normal_data[column].astype(str).fillna("nan")
        normal_data.loc[:, "bin"] = infer_objects_compatible(tmp)

        # print(f"Data Type: categorical, Count: {len(normal_data_ref[column])}")

    elif binning_type == "percentiles":
        if breaks is None:
            try:
                # Filtrar solo valores numéricos y no nulos
                numeric_data = normal_data_ref[column].dropna()
                # print(f"Processing column: {column}")
                # print(f"Data Type: {numeric_data.dtype}, Count: {len(numeric_data)}")

                if len(numeric_data) == 0:
                    raise ValueError(f"No valid data in column '{column}' for binning.")

                if not np.issubdtype(numeric_data.dtype, np.number):
                    raise ValueError(f"Column '{column}' contains non-numeric data.")

                # Calcular percentiles
                breaks = np.percentile(numeric_data, np.linspace(0, 100, num_perc + 1))
                breaks = np.unique(breaks)  # Asegurar cortes únicos
                # print(f"Generated percentile breaks for '{column}'")
            except ValueError:
                raise ValueError(
                    f"Cannot calculate percentiles for column '{column}'. Check the data."
                )

        # normal_data_ref["bin"] = pd.cut(normal_data_ref[column], bins=breaks, right=False, include_lowest=True)
        # normal_data["bin"] = pd.cut(normal_data[column], bins=breaks, right=False, include_lowest=True)
        normal_data_ref.loc[:, "bin"] = pd.cut(
            normal_data_ref[column], bins=breaks, right=False, include_lowest=True
        )
        normal_data.loc[:, "bin"] = pd.cut(
            normal_data[column], bins=breaks, right=False, include_lowest=True
        )

        # Ordenamiento de bins por promedio del bin
        bin_means = (
            normal_data_ref.groupby("bin", observed=True)[column].mean().reset_index()
        )
        bin_means = bin_means.rename(columns={column: "bin_mean"})

        normal_data_ref = normal_data_ref.merge(bin_means, on="bin", how="left")
        normal_data_ref = normal_data_ref.sort_values("bin_mean").reset_index(drop=True)
        normal_data_ref = normal_data_ref.drop(columns=["bin_mean"])

        normal_data = normal_data.merge(bin_means, on="bin", how="left")
        normal_data = normal_data.sort_values("bin_mean").reset_index(drop=True)
        normal_data = normal_data.drop(columns=["bin_mean"])

    elif binning_type == "breaks" and breaks:
        breaks = [-np.inf] + breaks + [np.inf]
        normal_data_ref.loc[:, "bin"] = pd.cut(
            normal_data_ref[column], bins=breaks, right=False, include_lowest=True
        )
        normal_data.loc[:, "bin"] = pd.cut(
            normal_data[column], bins=breaks, right=False, include_lowest=True
        )

    else:
        raise ValueError(f"Unsupported binning_type: {binning_type}")

    # Calcular frecuencias para datos normales
    bin_ref = (
        normal_data_ref.groupby("bin", observed=True)
        .size()
        .reset_index(name="count_ref")
    )
    bin_data = (
        normal_data.groupby("bin", observed=True).size().reset_index(name="count_data")
    )

    # Normalizar la columna 'bin' como texto
    bin_ref["bin"] = bin_ref["bin"].astype(str)
    bin_data["bin"] = bin_data["bin"].astype(str)

    try:
        # Crear bin para valores especiales
        special_bin_ref = pd.DataFrame(
            {"bin": ["special_values"], "count_ref": [len(special_data_ref)]}
        )

        special_bin_data = pd.DataFrame(
            {"bin": ["special_values"], "count_data": [len(special_data)]}
        )

        # Crear bin para valores NaN
        # nan_count_ref = (data_ref[column] == "nan").sum()
        # nan_count_data = (data[column] == "nan").sum()
        nan_count_ref = (
            data_ref[column].isna().sum() + (data_ref[column] == "nan").sum()
        )
        nan_count_data = data[column].isna().sum() + (data[column] == "nan").sum()

        nan_bin_ref = pd.DataFrame({"bin": ["nan"], "count_ref": [nan_count_ref]})

        nan_bin_data = pd.DataFrame({"bin": ["nan"], "count_data": [nan_count_data]})

        # Concatenar bins especiales y NaN
        bin_ref = pd.concat([bin_ref, special_bin_ref, nan_bin_ref], ignore_index=True)
        bin_data = pd.concat(
            [bin_data, special_bin_data, nan_bin_data], ignore_index=True
        )

    except Exception as e:
        print(f"Error adding special or NaN bins: {e}")

    # Combinar usando 'pd.merge' y rellenar valores faltantes
    bins = pd.merge(bin_ref, bin_data, on="bin", how="outer").fillna(0)

    # Validar columnas esperadas
    if "count_ref" not in bins.columns or "count_data" not in bins.columns:
        raise KeyError(
            f"Missing required columns 'count_ref' or 'count_data' for column '{column}'."
        )

    bins["dist_ref"] = (
        bins["count_ref"] / bins["count_ref"].sum()
        if bins["count_ref"].sum() > 0
        else 0
    )
    bins["dist_data"] = (
        bins["count_data"] / bins["count_data"].sum()
        if bins["count_data"].sum() > 0
        else 0
    )

    # **Elimina duplicados**
    bins = bins.drop_duplicates(subset=["bin"], keep="first").reset_index(drop=True)

    return bins


def calculate_psi(bins, exclude_special_values=True):
    """
    Calculate the PSI for binned data and update the DataFrame with PSI values.

    Args:
        bins (DataFrame): DataFrame with columns 'dist_ref' and 'dist_data'.
        exclude_special_values (bool): Whether to exclude special values from the PSI calculation.

    Returns:
        DataFrame: Updated bins DataFrame with 'psi' column.
        float: Total PSI value.
    """
    # 1. Keep only bins to evaluate
    valid_bins = bins[bins["bin"] != "nan"].copy()

    if exclude_special_values:
        valid_bins = valid_bins[valid_bins["bin"] != "special_values"]

    # 2. Re-normalise distributions so they sum to 1 in the remaining bins
    total_ref = valid_bins["count_ref"].sum()
    total_data = valid_bins["count_data"].sum()
    # avoid division by zero
    eps = 1e-10
    valid_bins["dist_ref"] = valid_bins["count_ref"] / (total_ref or eps)
    valid_bins["dist_data"] = valid_bins["count_data"] / (total_data or eps)

    # 3. Replace zeros to prevent log issues
    valid_bins["dist_ref"] = valid_bins["dist_ref"].replace(0, eps)
    valid_bins["dist_data"] = valid_bins["dist_data"].replace(0, eps)

    # 4. PSI per bin
    valid_bins["psi"] = (valid_bins["dist_ref"] - valid_bins["dist_data"]) * np.log(
        valid_bins["dist_ref"] / valid_bins["dist_data"]
    )

    # 5. Merge back so every bin (even excluded ones) has a 'psi' column
    bins = bins.merge(valid_bins[["bin", "psi"]], on="bin", how="left")
    bins["psi"] = bins["psi"].fillna(0.0)

    # 6. Total PSI
    total_psi = valid_bins["psi"].sum()

    return bins, total_psi


def analyze_variable(
    data,
    data_ref,
    column,
    binning_type="percentiles",
    num_perc=10,
    breaks=None,
    special_values=None,
    exclude_special_values=True,
):
    """
    Perform PSI analysis for a single variable.

    Args:
        data (DataFrame): Actual data.
        data_ref (DataFrame): Reference data.
        column (str): Column name to analyze.
        binning_type (str): Type of binning ('percentiles', 'breaks', 'discrete', 'categorical').
        num_perc (int, optional): Number of percentiles. Defaults to 10.
        breaks (list, optional): Predefined breaks. Defaults to None.
        special_values (list, optional): Special values to handle. Defaults to None.
        exclude_special_values (bool, optional): Whether to exclude special values from the PSI calculation. Defaults to True.

    Returns:
        dict: Results with bins, PSI, and binning_type.
    """
    bins = calculate_bins(
        data, data_ref, column, binning_type, breaks, num_perc, special_values
    )
    bins, psi = calculate_psi(bins, exclude_special_values)
    bins["variable"] = column
    return {"bins": bins, "psi": psi, "binning_type": binning_type}


def get_mean_from_bin(bin_value):
    """
    Calcula el promedio de los límites de un bin si es un intervalo, si no devuelve NaN.

    Args:
        bin_value (str, float): El valor del bin, puede ser un string tipo '[a, b)' o un valor especial.

    Returns:
        float: El promedio de los límites si aplica, si no, np.nan.
    """
    try:
        if (
            isinstance(bin_value, str)
            and bin_value.startswith("[")
            and "," in bin_value
        ):
            left, right = bin_value.replace("[", "").replace(")", "").split(",")
            left = float(left.strip())
            right = float(right.strip())
            return (left + right) / 2
        else:
            return np.nan
    except Exception:
        return np.nan


def analyze_dataset(
    data,
    data_ref,
    columns,
    num_perc=10,
    breaks_list=None,
    categorical_columns=None,
    special_values=None,
    exclude_special_values=True,
):
    """
    Perform PSI analysis for a dataset.

    Args:
        data (DataFrame): Actual data.
        data_ref (DataFrame): Reference data.
        columns (list): List of columns to analyze.
        num_perc (int, optional): Number of percentiles. Defaults to 10.
        breaks_list (dict, optional): Predefined breaks for specific columns. Defaults to None.
        categorical_columns (list, optional): Columns to treat as categorical. Defaults to None.
        special_values (list, optional): List of special values to handle. Defaults to None.
        exclude_special_values (bool, optional): Whether to exclude special values from the PSI calculation. Defaults to True.

    Returns:
        tuple: DataFrames (psi_results, psi_stats).
    """
    psi_results = []
    psi_stats = []

    contador = 0
    print("N variables:", len(columns))

    for column in columns:
        contador = contador + 1
        print(f"{contador}-Processing variable: {column}")

        binning_type = (
            "categorical" if column in (categorical_columns or []) else "percentiles"
        )
        breaks = breaks_list.get(column) if breaks_list else None

        # Realizar análisis de una sola variable
        result = analyze_variable(
            data,
            data_ref,
            column,
            binning_type,
            num_perc,
            breaks,
            special_values,
            exclude_special_values,
        )

        # Agregar resultados del PSI con el tipo de binning
        psi_results.append(
            {
                "variable": column,
                "psi": result["psi"],
                "binning_type": result["binning_type"],
            }
        )

        # Agregar estadísticas detalladas
        stats = result["bins"][
            [
                "variable",
                "bin",
                "count_ref",
                "count_data",
                "dist_ref",
                "dist_data",
                "psi",
            ]
        ]
        stats.rename(
            columns={"count_ref": "n_ref", "count_data": "n_data"}, inplace=True
        )
        psi_stats.append(stats)

    psi_results_df = pd.DataFrame(psi_results)
    psi_stats_df = pd.concat(psi_stats, ignore_index=True)

    # Obtener solo variables de tipo percentiles
    percentile_vars = psi_results_df.loc[
        psi_results_df["binning_type"] == "percentiles", "variable"
    ].unique()

    # Agregar mean_bins solo a variables con binning percentiles
    psi_stats_df["mean_bins"] = psi_stats_df.apply(
        lambda row: (
            get_mean_from_bin(row["bin"])
            if row["variable"] in percentile_vars
            else np.nan
        ),
        axis=1,
    )

    psi_stats_df = psi_stats_df.sort_values(by=["variable", "mean_bins"]).drop(
        columns=["mean_bins"]
    )

    return psi_results_df, psi_stats_df


def save_psi_plots_to_pdf(psi_stats, psi_results, output_pdf):
    """
    Generate and save PSI bar plots for all variables into a single PDF file, ordered by PSI.

    Args:
        psi_stats (DataFrame): DataFrame with detailed PSI stats for all variables.
        psi_results (DataFrame): DataFrame with PSI summary for all variables.
        output_pdf (str): File path to save the PDF.
    """

    if psi_results.empty or psi_stats.empty:
        logging.warning("psi_results o psi_stats vacíos: no se genera PDF.")
        return None

    # Ordenar las variables por PSI en orden descendente
    psi_results_sorted = psi_results.sort_values(by="psi", ascending=False)

    with PdfPages(output_pdf) as pdf:
        for _, row in psi_results_sorted.iterrows():
            variable = row["variable"]
            psi_total = row["psi"]
            binning_type = row.get(
                "binning_type", "unknown"
            )  # Obtener binning_type si está disponible

            # Filtrar los datos para la variable seleccionada
            variable_data = psi_stats[psi_stats["variable"] == variable]

            if variable_data.empty:
                print(
                    f"Warning: No data available for variable '{variable}'. Skipping..."
                )
                continue

            # Crear el gráfico
            plt.figure(figsize=(8, 4))
            x = range(len(variable_data))
            bar_width = 0.4

            # Verificar si hay datos válidos
            if (
                variable_data["dist_ref"].sum() == 0
                and variable_data["dist_data"].sum() == 0
            ):
                print(
                    f"Warning: No meaningful data for variable '{variable}'. Skipping..."
                )
                continue

            # Crear las barras con colores personalizados
            plt.bar(
                x,
                variable_data["dist_ref"] * 100,
                width=bar_width,
                label="Referencia",
                color="#1f77b4",
                alpha=0.9,
            )
            plt.bar(
                [i + bar_width for i in x],
                variable_data["dist_data"] * 100,
                width=bar_width,
                label="Actual",
                color="#aec7e8",
                alpha=0.9,
            )

            # Personalizar el gráfico
            plt.xlabel("Bins", fontsize=10)  # Tamaño reducido para los bins
            plt.ylabel("Porcentaje (%)", fontsize=10)
            plt.title(
                f"{variable} - PSI: {psi_total:.4f}-Binning Type: {binning_type}",
                fontsize=8,
            )  # Incluir el tipo de binning en el título
            plt.xticks(
                [i + bar_width / 2 for i in x],
                variable_data["bin"].astype(str),
                rotation=45,
                ha="right",
                fontsize=8,
            )
            plt.legend(loc="upper right", fontsize=9)

            # Ajustar diseño
            plt.tight_layout()

            # Guardar la página en el PDF
            pdf.savefig()
            plt.close()

    print(f"PDF guardado en: {output_pdf}")
