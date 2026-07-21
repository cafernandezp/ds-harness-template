def filter_outliers_continuas(
    df,
    outlier_config,
    bounds=None,
    dataset_name="train",
    debug=True,
):
    """
    outlier_config ejemplo:
    {
        "mora_deuda_principal_mora": ["low", "high"],
        "hermes_firsttit_avg_acc_maintained_12m_amount": ["low", "high"],
        "hermes_firsttit_unpaid_m_90_nc_24m_number": ["high"],
        "hermes_firsttit_debt_max_ant_d_12m_number": ["low"],
    }
    """
    outlier_config = {
        col: set(sides)
        for col, sides in outlier_config.items()
    }

    valid_sides = {"low", "high"}
    invalid_config = {
        col: sides - valid_sides
        for col, sides in outlier_config.items()
        if sides - valid_sides
    }

    if invalid_config:
        raise ValueError(f"Config outliers invalida: {invalid_config}")

    vars_outliers = list(outlier_config.keys())
    missing_cols = [col for col in vars_outliers if col not in df.columns]

    if missing_cols:
        raise ValueError(f"Columnas no encontradas en {dataset_name}: {missing_cols}")

    if bounds is None:
        bounds = (
            df[vars_outliers]
            .quantile([0.01, 0.99])
            .T
            .rename(columns={0.01: "p01", 0.99: "p99"})
        )
    else:
        bounds = pd.DataFrame(bounds).copy()

    bounds = bounds.loc[vars_outliers, ["p01", "p99"]]

    # Primero se identifican todos los outliers, sin filtrar todavia.
    mask_low_all = df[vars_outliers].lt(bounds["p01"], axis="columns")
    mask_high_all = df[vars_outliers].gt(bounds["p99"], axis="columns")

    mask_outlier = pd.DataFrame(
        False,
        index=df.index,
        columns=vars_outliers,
    )

    for col, sides in outlier_config.items():
        if "low" in sides:
            mask_outlier[col] = mask_outlier[col] | mask_low_all[col]

        if "high" in sides:
            mask_outlier[col] = mask_outlier[col] | mask_high_all[col]

    mask_outlier_any = mask_outlier.any(axis=1)

    n_total = len(df)
    n_remove = int(mask_outlier_any.sum())

    if debug:
        summary = pd.DataFrame({
            "min": df[vars_outliers].min(),
            "p01": bounds["p01"],
            "p99": bounds["p99"],
            "max": df[vars_outliers].max(),
            "regla": [
                "+".join(sorted(outlier_config[col]))
                for col in vars_outliers
            ],
        })

        reason_counts = pd.DataFrame({
            "n_casos_lt_p01": mask_low_all.sum(),
            "n_casos_gt_p99": mask_high_all.sum(),
            "n_casos_outlier_aplicado": mask_outlier.sum(),
            "regla": [
                "+".join(sorted(outlier_config[col]))
                for col in vars_outliers
            ],
        })

        print("=" * 80)
        print(f"P01 / P99 POR VARIABLE - {dataset_name.upper()}")
        print("=" * 80)
        display(summary)

        print("=" * 80)
        print(f"CONTEO OUTLIERS POR VARIABLE - {dataset_name.upper()}")
        print("=" * 80)
        display(reason_counts)

        print("=" * 80)
        print(f"COMBINACIONES DE OUTLIERS APLICADOS - {dataset_name.upper()}")
        print("=" * 80)
        result = (
            mask_outlier
            .add_prefix("outlier__")
            .groupby(
                list(mask_outlier.add_prefix("outlier__").columns),
                dropna=False,
            )
            .size()
            .reset_index(name="n")
            .sort_values("n", ascending=False)
        )
        result["pct"] = result["n"] / n_total
        display(result)

        print("=" * 80)
        print(f"IMPACTO DE ELIMINAR OUTLIERS - {dataset_name.upper()}")
        print("=" * 80)
        print(f"N total      : {n_total:,}")
        print(f"N eliminar   : {n_remove:,}")
        print(f"% eliminar   : {100 * n_remove / n_total:.2f}%")

        print("=" * 80)
        print(f"INTERSECCION ENTRE VARIABLES - {dataset_name.upper()}")
        print("=" * 80)
        n_vars_outlier = mask_outlier.sum(axis=1)
        for n_flags in range(2, len(vars_outliers) + 1):
            print(
                f"Casos con >={n_flags} variables outlier:",
                int((n_vars_outlier >= n_flags).sum()),
            )

    # Luego se filtra una sola vez.
    return df.loc[~mask_outlier_any].copy(), bounds.copy()
