# Feature-vs-Feature Association Measures — Method Selection Guide

> **Context.**
> Picking the correct association measure for any feature pair given their data types,
> to detect redundancy in a predictive-modeling pipeline.
> Stack: `pandas`, `scipy`, `sklearn` (standard Python). Target type: agnostic (measures
> are feature–feature, not feature–target). Scope: EDA / redundancy filtering stage;
> results feed downstream VIF check and wrapper methods.
>
> **Assumption:** features have already been typed (binary, continuous, nominal, ordinal).
> If typing is unclear, use the definitions table in §Type definitions before proceeding.

---

## TL;DR / Recommendation

- **Continuous ↔ Continuous → Spearman** (robust default); Pearson only when linear +
  symmetric + outlier-free and you need r².
- **Binary ↔ Binary → φ** (= `df.corr(method="pearson")` on 0/1 columns).
- **Binary ↔ Continuous → Spearman** (default) or point-biserial (= Pearson) if symmetric.
- **Categorical ↔ Continuous → η² (ANOVA)**; ε² (Kruskal–Wallis) if the distribution is skewed.
- **Categorical ↔ {Categorical / Binary} → Cramér's V** (bias-corrected for high cardinality).
- **Anything involving Ordinal → Spearman / Kendall τ** (respects order, ignores spacing).
- `df.corr()` is **invalid for any nominal categorical** — label codes have no real order.
- **Mutual information works for every combination** but is a secondary screen, not a default.

---

## Type definitions (read first)

| Type | Definition | Order? | Simple example |
|---|---|---|---|
| **Binary** | Two categories, coded 0/1 | No (trivial) | `has_purchased` ∈ {0, 1} |
| **Continuous** | Real-valued, numeric scale | Yes (full) | `income` = 42 350.75 |
| **Categorical (nominal)** | ≥ 3 categories, no inherent order | No | `province` ∈ {Madrid, Sevilla, …} |
| **Ordinal** | Categories with meaningful order, unknown spacing | Rank only | `satisfaction` ∈ {low < medium < high} |

Key distinctions: `province` is nominal (Madrid is not "more" than Sevilla); `satisfaction`
is ordinal (high > low). Ordinal spacing is unknown, so only ranks are valid — use
Spearman/Kendall, not Pearson. Binary is a 2-level categorical.

---

## Comparison table

| Pair | Primary measure | Secondary / fallback | Invalid |
|---|---|---|---|
| Continuous ↔ Continuous | **Spearman ρ** | Pearson r (linear only); Kendall τ (small n) | — |
| Binary ↔ Binary | **φ** (= Pearson on 0/1) | — | — |
| Binary ↔ Continuous | **Spearman** | Point-biserial (= Pearson, if symmetric) | — |
| Categorical ↔ Continuous | **η² (ANOVA)** | ε² (Kruskal–Wallis) if skewed | `df.corr()` |
| Categorical ↔ Categorical | **Cramér's V** (Bergsma-corrected) | — | `df.corr()` |
| Categorical ↔ Binary | **Cramér's V** | — | `df.corr()` |
| Ordinal ↔ anything | **Spearman / Kendall τ** | Cramér's V (loses order) | Pearson if unequal spacing |
| Any pair (non-monotonic) | **Mutual information** (secondary) | — | — |

---

## Continuous ↔ Continuous

**What.** Two real-valued features. Home turf of Pearson and Spearman.

**Pros.**
- Spearman captures any monotonic relation (`y = exp(x)` → ρ ≈ 1.0, Pearson ≈ 0.7) and is
  robust to outliers.
- Pearson provides r² (shared variance) — useful when linearity is confirmed.
- Both available via `df.corr()` with no extra dependencies.

**Risks.**
- Pearson: a single outlier can shift r by 0.5+; returns ≈ 0 for a perfect non-linear
  relationship like `y = x²`.
- Spearman misses non-monotonic shapes (`y = sin(x)` over [0, 2π] → ρ ≈ 0).
- Both return 0 for a U-shaped dependency — use mutual information as a secondary screen.
- Always plot: Anscombe's quartet shows four datasets with identical r = 0.816 but radically
  different shapes.

**How / verify.**

```python
import numpy as np, pandas as pd

rng = np.random.default_rng(42)
x = rng.normal(size=500)
y = np.exp(x) + rng.normal(scale=0.1, size=500)   # monotonic but non-linear
df = pd.DataFrame({"x": x, "y": y})

print("Pearson :", round(df.corr(method="pearson").loc["x", "y"], 3))   # ~0.70
print("Spearman:", round(df.corr(method="spearman").loc["x", "y"], 3))  # ~1.00
```

Redundancy threshold: |ρ| > 0.85 (project default; adjust to context).

---

## Binary ↔ Binary

**What.** Two 0/1 columns. φ (phi) is Pearson applied to binary variables — identical formula,
exact result.

**Pros.**
- No extra library; `df.corr(method="pearson")` on 0/1 columns gives φ directly.
- Ranges in [−1, 1] and equals 0 iff the 2×2 table is independent.
- For unordered binary features, |φ| is equivalent to Cramér's V on the 2×2 table.

**Risks.**
- |φ| = 1 only when the marginal distributions match exactly; asymmetric base rates cap the
  maximum reachable |φ| below 1.
- Labels must actually be 0/1 integers, not arbitrary codes.

**How / verify.**

```python
import pandas as pd
from scipy.stats import contingency

s1 = pd.Series([1,0,1,1,0,0,1,0], name="a")
s2 = pd.Series([1,0,1,0,0,1,1,0], name="b")
df = pd.DataFrame({"a": s1, "b": s2})

phi = df.corr(method="pearson").loc["a", "b"]
print("φ:", round(phi, 3))  # equivalent to Cramér's V for a 2×2 table
```

---

## Binary ↔ Continuous

**What.** One binary column (0/1), one continuous column.

**Pros.**
- Spearman is safe and parameter-free: treats the binary column as ranks 0/1.
- Point-biserial (= Pearson on 0/1 + continuous) gives r² when distributions within each group
  are symmetric and similar in spread.

**Risks.**
- Pearson/point-biserial is sensitive to outliers in the continuous column.
- Neither detects non-linear group differences; consider a Mann–Whitney U test or η² if the
  binary column defines groups with very different spread.

**How / verify.**

```python
import pandas as pd
from scipy.stats import pointbiserialr

binary = pd.Series([1,0,1,1,0,0,1,0], name="purchased")
cont   = pd.Series([5.2, 1.1, 4.8, 6.3, 0.9, 2.1, 5.9, 1.4], name="income")

r_pb, p = pointbiserialr(binary, cont)
print("Point-biserial r:", round(r_pb, 3), "| p:", round(p, 3))

# Spearman (robust alternative)
print("Spearman:", round(pd.Series(binary).corr(cont, method="spearman"), 3))
```

---

## Categorical ↔ Continuous

**What.** One nominal column (≥ 3 levels), one continuous column. η² (eta-squared) from
one-way ANOVA measures the proportion of variance in the continuous variable explained by
group membership.

**Pros.**
- η² ∈ [0, 1] and has a natural "variance explained" interpretation.
- ε² (epsilon-squared from Kruskal–Wallis) is the rank-based alternative — robust to skew and
  outliers; use it when the continuous variable is non-normal or has outliers.

**Risks.**
- η² is biased upward in small samples (prefer ω² for n < 50 per group).
- High-cardinality categoricals inflate η² — collapse rare levels first.
- Both assume groups are independent; violations (repeated measures, nested structures) require
  different tests.

**How / verify.**

```python
import pandas as pd
import numpy as np
from scipy.stats import f_oneway, kruskal

cat  = pd.Series(["A","B","C","A","B","C","A","B"], name="region")
cont = pd.Series([5.2, 1.1, 4.8, 6.3, 0.9, 2.1, 5.9, 1.4], name="income")

groups = [cont[cat == lvl].values for lvl in cat.unique()]

# η² (ANOVA)
f_stat, p_anova = f_oneway(*groups)
ss_between = sum(len(g) * (g.mean() - cont.mean())**2 for g in groups)
ss_total   = ((cont - cont.mean())**2).sum()
eta2 = ss_between / ss_total
print("η²:", round(eta2, 3), "| p_anova:", round(p_anova, 3))

# ε² (Kruskal–Wallis, robust)
h_stat, p_kw = kruskal(*groups)
n = len(cont)
eps2 = (h_stat - len(groups) + 1) / (n - len(groups))   # ε²
print("ε²:", round(eps2, 3), "| p_kw:", round(p_kw, 3))
```

---

## Categorical ↔ Categorical (and Categorical ↔ Binary)

**What.** Two nominal columns (or one nominal + one binary). Cramér's V is the normalized
χ²-based association, ranging in [0, 1].

**Pros.**
- Symmetric and bounded in [0, 1]; 0 means independence.
- The bias-corrected (Bergsma) variant removes the upward bias at high cardinality.
- `scipy.stats.contingency.association(table, method="cramer")` computes it directly.

**Risks.**
- Standard V is inflated when k (levels) is large or n is small — always use the bias-corrected
  version.
- `df.corr()` on label-encoded nominal columns is meaningless (result changes with relabeling).
- Cramér's V ignores any ordering; for ordinal × ordinal, use Spearman instead.

**How / verify.**

```python
import pandas as pd
from scipy.stats import contingency

s1 = pd.Series(["A","B","A","C","B","C","A","B"], name="region")
s2 = pd.Series(["X","Y","X","X","Y","Y","X","Y"], name="channel")

table = pd.crosstab(s1, s2)
v = contingency.association(table.values, method="cramer", correction=True)
print("Cramér's V (bias-corrected):", round(v, 3))
```

---

## Ordinal ↔ Anything

**What.** When one or both features are ordinal, only the rank ordering is meaningful — the
spacing between levels is unknown and may be unequal. Use Spearman ρ or Kendall τ.

**Pros.**
- Spearman and Kendall respect the order while ignoring arbitrary numeric spacing.
- Kendall τ is more robust than Spearman for small n (< 30) or data with many ties.

**Risks.**
- Pearson on ordinal codes (e.g., low=1, medium=2, high=3) assumes equal spacing — invalid
  unless spacing is explicitly justified.
- Cramér's V can be used as a fallback but discards the ordering — prefer Spearman.

**How / verify.**

```python
import pandas as pd
from scipy.stats import kendalltau

ordinal_codes = pd.Series([1, 3, 2, 3, 1, 2, 3, 1], name="satisfaction")  # low=1,mid=2,high=3
cont          = pd.Series([5.2, 1.1, 4.8, 6.3, 0.9, 2.1, 5.9, 1.4], name="income")

print("Spearman:", round(ordinal_codes.corr(cont, method="spearman"), 3))
tau, p = kendalltau(ordinal_codes, cont)
print("Kendall τ:", round(tau, 3), "| p:", round(p, 3))
```

---

## Mutual information — when and why (critique)

**What.** MI measures the reduction in uncertainty about one variable from knowing the other.
It makes no assumption about order, linearity, or monotonicity, so it applies to any type pair.

**When to use.** MI is a secondary, general-purpose screen — specifically when non-monotonic
dependence is suspected (U-shapes, variance-only differences) or when mixing very different
types and one consistent (if coarse) number is needed across all pairs.

**Why it is not the universal default despite working everywhere.**

| Drawback | Consequence |
|---|---|
| No natural [0,1] scale | Raw MI is in nats/bits; thresholds are not comparable across pairs unless normalized (NMI). |
| No sign | Cannot tell positive from negative association. |
| Estimation variance | k-NN / binning estimates are sensitive to sample size, `n_neighbors`, and dimensionality. |
| Discrete-flag dependency | Wrong `discrete_features` flag silently produces a wrong estimate. |
| Cost | Heavier than vectorized `df.corr()` across a full matrix. |

**How / verify.**

```python
from sklearn.feature_selection import mutual_info_regression
import numpy as np

rng = np.random.default_rng(42)
X = rng.normal(size=(300, 3))
y = np.sin(X[:, 0]) + rng.normal(scale=0.1, size=300)  # non-monotonic relationship

# discrete_features: flag True for binary/ordinal/nominal columns
mi = mutual_info_regression(X, y, discrete_features=[False, False, False], random_state=42)
print("MI scores:", mi.round(3))   # X[:,0] should score highest despite low Spearman
```

**Verdict.** The specialized measures in the matrix (φ, Spearman, η², Cramér's V) are cheaper,
signed, and better-calibrated for their respective pairs. MI is the safety net for non-monotonic
or mixed-type situations — use it as a second pass, not the first tool.

---

## Problem-specific considerations

- **VIF after pairwise filtering.** Pairwise association is not multivariate: two features with
  low pairwise association can still be jointly collinear with a third. Run VIF after pair-based
  pruning.
- **High-cardinality categoricals.** η² and Cramér's V inflate with many levels. Collapse rare
  levels first (e.g., levels with < 1% frequency → `"Other"`); use bias-corrected Cramér's V.
- **Target-aware measures.** Any association measure computed between a feature and the target
  (not covered here) must be computed inside CV folds to avoid leakage.
- **Continuous target in regression.** Spearman (feature ↔ target, monotonic), η² (categorical
  feature ↔ continuous target), and MI (non-monotonic) all apply; the matrix above covers the
  feature–feature case only.

---

## Diagnostics & pitfalls

- **Always plot before dropping.** Scatter / box / violin reveals shapes a single coefficient
  hides (Anscombe's quartet).
- **Pearson–Spearman gap is a diagnostic.** A large gap signals skew or outliers; trust Spearman.
- **`df.corr()` on nominal label codes is meaningless.** The value changes if you relabel.
- **r = 0 ≠ independence.** Only zero *linear* (Pearson) or *monotonic* (Spearman) association;
  MI = 0 is the real independence test.
- **Pairwise ≠ multivariate.** Check VIF after pair-based pruning.

---

## Decision rule

1. Identify each feature's type using the definitions table.
2. Look up the pair in the comparison table → use the listed measure.
3. Continuous involved + skew / outliers / unknown shape → prefer the **rank-based** option
   (Spearman / ε²).
4. Nominal involved → **never** `df.corr()`; use Cramér's V or η² / ε².
5. Ordinal involved → **Spearman / Kendall τ**.
6. Suspect non-monotonic dependence → add **mutual information** as a second pass.
7. After pairwise pruning → check **VIF** for residual multicollinearity.

---

## References

1. Kuhn, M. & Johnson, K. (2019). *Feature Engineering and Selection*. CRC Press.
   https://feat.engineering/
2. pandas — `DataFrame.corr` (pearson / spearman / kendall).
   https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.corr.html
3. SciPy — `pearsonr`, `spearmanr`, `kendalltau`, `f_oneway`, `kruskal`.
   https://docs.scipy.org/doc/scipy/reference/stats.html
4. SciPy — `contingency.association` (Cramér's V, bias-corrected).
   https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.contingency.association.html
5. scikit-learn — `mutual_info_regression` / `mutual_info_classif`.
   https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.mutual_info_regression.html
6. Anscombe, F. J. (1973). "Graphs in Statistical Analysis." *The American Statistician*, 27(1).
