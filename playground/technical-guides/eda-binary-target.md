# EDA Template — Binary Target

Source: `playground/scripts/eda/eda_binary_target.ipynb` (German Credit dataset).
Reuse this section order for any new binary-classification project. Owner-only
(`playground/`) — not read by LEAD/IMPLEMENTER/REVIEWER/ADVISOR.

---

## 1. Imports

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import inspection      # describe_cols
import visualization   # plot_hist_grid_by_category, plot_kde_grid_vs_reference, ...
```

## 2. Env

Define once, top of notebook:
- `target_col` — name of target column
- `FONTSIZE` — shared plot title font size

## 3. Load data

Read raw source. Print `df.shape` right after load — cheap sanity check.

## 4. Decode categorical codes (if applicable)

If source uses coded categories (e.g. `A11`, `A30`), map to human-readable
labels via a `category_maps` dict + `df[col] = df[col].map(mapping)`. Leave
target column in its original encoding — decode explanatory features only.
Re-print `df.shape` after mapping (catches accidental row loss from a bad map).

## 5. Inspect columns

```python
inspection.describe_cols(df)
```

Check `n_nulls` per column before anything else. No missing values doesn't
mean skip this step — it means confirm it. A real null-handling decision
belongs in `src/etl/features`, never resolved silently inside a playground
notebook.

## 6. Split

```python
features = df.columns.drop(target_col)
X = df[features]
y = df[target_col]
```

## 7. Target

- Print unique values + mean.
- Build count/pct distribution table.
- Derive **majority_class** / **minority_class** generically (`counts.idxmax()`
  / `idxmin()`) — works regardless of target encoding (0/1, 1/2, strings).
  Build a `class_palette` dict keyed by class value, reused in every later plot.
- Bar chart of class counts with pct labels.

Flag class imbalance here explicitly — it changes which metric is valid later
(plain accuracy misleads under imbalance).

## 8. Feature distributions

Split columns once:

```python
numeric_features = X.select_dtypes(include="number").columns
categorical_features = X.select_dtypes(exclude="number").columns
```

### 8a. Numeric features

- Decile table: `.describe(percentiles=[.01,.05,.10,...,.95,.99])` — clip
  plot x-limits to the 1%/99% percentiles, not raw min/max, so outliers don't
  flatten the distribution shape.
- Per feature, 3-panel figure:
  1. Histogram + KDE, title annotated with n, avg, median, %zeros, %nulls,
     target avg.
  2. Boxplot by target class, title annotated with median per class.
  3. KDE by target class (`common_norm=False` so each class's density
     integrates to 1 independently — makes shape comparison fair regardless
     of class size).

### 8b. Numeric feature correlations

Spearman correlation heatmap (`method="spearman"` — robust to non-linear
monotonic relationships and doesn't assume normality, unlike Pearson).

### 8c. Categorical features

Derive a **target_flag** generically:

```python
target_flag = (y == minority_class).astype(int)
baseline_target_rate = target_flag.mean()
```

Per feature, dual-axis chart: bar = category counts, line = target rate per
category, dashed horizontal = baseline rate. One glance shows both category
volume and whether that category swings target rate away from baseline.

## 9. Feature relationships (toolkit showcase, optional)

Only if a date column or a natural grouping axis exists:
- `visualization.plot_hist_grid_by_category(df, value_col, legend_col, title, figsize)`
  — value distribution split by a categorical legend.
- `visualization.plot_kde_grid_vs_reference(df, value_col, legend_col, label_name_reference, title, n_cols)`
  — compare one reference category's KDE against all others.
- `visualization.plot_exploratory_timeseries` / `plot_category_panels` — skip
  if no date column; state explicitly in a markdown cell why they're skipped
  rather than deleting them silently, so the next reader knows they were
  considered.

## 10. Takeaways

Close with a markdown cell, bullet list:
- Class imbalance figure and what it implies for metric choice.
- Which numeric features correlate most/least with target (with actual corr
  values).
- Which categorical features swing target rate most/least (with spread).
- Any counter-intuitive finding, stated plainly with a plausible caveat
  (sampling quirk, confound) — not overclaimed as causal.
- Explicit note: anything worth acting on graduates to an ADR or research
  report — it does not stay decided inside this notebook.

---

## Reusable patterns worth copying verbatim

- **Generic majority/minority derivation** — never hardcode target encoding:
  ```python
  counts = y.value_counts()
  majority_class = counts.idxmax()
  minority_class = counts.idxmin()
  class_palette = {majority_class: "tab:blue", minority_class: "tab:red"}
  ```
- **Percentile-clipped x-limits** for numeric plots (`p01, p99` from the
  decile table) instead of raw min/max.
- **Dual-axis count+rate chart** for every categorical feature — same shape,
  loop over `categorical_features`.
- **`common_norm=False`** on any cross-class KDE comparison.
