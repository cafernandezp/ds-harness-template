---
title: "Feature Selection: Conservative 1-SE Rule for Backward Selection"
date: 2026-06-08
status: accepted
author: LEAD
research_report: "docs/research-reports/rr-backward-selection-1se.md"
supersedes: ""
related_features: ["FEAT-008"]
---

# Feature Selection: Conservative 1-SE Rule for Backward Selection

## Context

During backward feature selection for the Judicial Progress Score model, the algorithm
eliminates the feature with the lowest out-of-fold SHAP importance at each step.
Each step produces a `cv_score_mean` and a `cv_score_se` (Nadeau-Bengio corrected,
to compensate for fold correlation in repeated CV). A selection criterion is needed
to identify the final feature subset from the step history, balancing predictive
performance against parsimony. The model output — a judicial progress score — is
communicated directly to the business team, which raises the bar for methodological
robustness.

## Alternatives

### Alternative 1: Standard 1-SE Rule

Compares only the mean of each candidate against the threshold.

**Condition:** `cv_score_mean ≤ threshold`  
where `threshold = best_mean + best_se`

**Pros:**
- Classical Breiman formulation; default in sklearn, caret, and tidymodels.
- More permissive: accepts more candidates, tends to select smaller subsets.
- Directly comparable with implementations in the literature.

**Cons:**
- Ignores each candidate's own uncertainty: two models with the same mean but
  different SE receive identical treatment.
- May select a candidate whose true MAE, with meaningful probability, exceeds the best.

**Example outcome with project data:**

| Step | n_features | mean   | se     | within |
|------|------------|--------|--------|--------|
| 0    | 12         | 0.2324 | 0.0013 | ✓ (best) |
| 1    | 11         | 0.2325 | 0.0012 | ✓ |
| 2    | 10         | 0.2335 | 0.0013 | ✓ |
| 3    | 9          | 0.2336 | 0.0014 | ✓ ← chosen |
| 4    | 8          | 0.2338 | 0.0014 | ✗ |

→ Selects **9 features**.

---

### Alternative 2: Conservative 1-SE Rule

Compares the pessimistic bound of each candidate against the threshold.

**Condition:** `cv_score_mean + cv_score_se ≤ threshold`  
where `threshold = best_mean + best_se`

**Pros:**
- Acknowledges that each candidate's mean also carries uncertainty, not only the best's.
- Accepts only candidates where evidence is strong on both sides of the estimate.
- Coherent with the Nadeau-Bengio correction: recognizes uncertainty in all estimates.
- Features that are eliminated are discarded with higher confidence.

**Cons:**
- More restrictive: accepts fewer candidates; final model retains more features than
  the standard rule.
- Not the standard formulation in the literature; direct comparisons require care.

**Example outcome with project data:**

| Step | n_features | mean   | se     | upper  | within |
|------|------------|--------|--------|--------|--------|
| 0    | 12         | 0.2324 | 0.0013 | 0.2337 | ✓ (best) |
| 1    | 11         | 0.2325 | 0.0012 | 0.2337 | ✓ ← chosen |
| 2    | 10         | 0.2335 | 0.0013 | 0.2348 | ✗ |
| 3    | 9          | 0.2336 | 0.0014 | 0.2350 | ✗ |

→ Selects **11 features**.

---

## Decision

The **conservative 1-SE rule** is implemented: a candidate is accepted only if
`cv_score_mean + cv_score_se ≤ threshold`.

The primary reason is that the model score represents judicial progress and is
communicated directly to the business team. In that context, features are removed
only when the evidence is robust even under estimation uncertainty — a candidate
that is acceptable at its point estimate but not at its pessimistic bound does not
offer sufficient confidence that the discarded features are truly dispensable.

Additionally, the SE in this implementation is already Nadeau-Bengio corrected,
which compensates for fold correlation in repeated CV. Incorporating that SE into
each candidate's acceptance condition is consistent with the spirit of the
correction: explicitly recognizing uncertainty in all estimates, not only in
the best step's.

## Consequences

### Positive
- Higher confidence that eliminated features do not contribute real predictive value.
- More stable feature selection across different seeds and data partitions.
- Methodological coherence: the same uncertainty correction (Nadeau-Bengio) governs
  both the threshold and each candidate's acceptance.

### Negative
- The final model retains more features than with the standard rule.
- If maximum dimensionality reduction is the primary goal, this rule is suboptimal.
- Not directly comparable with standard literature implementations without explicitly
  noting the difference.

## Advice

- Do not switch to the standard rule to increase parsimony without documenting the
  change in a new ADR: the switch alters the selected subset and makes cross-version
  metric comparisons non-equivalent.
- If the sample size changes significantly (new segments, additional data sources),
  revisit whether the Nadeau-Bengio SE remains appropriate or whether raw standard
  deviation provides a more conservative bound.
- When reporting results externally, note that the conservative variant is used;
  include the `cv_score_upper` column in any published step table so reviewers
  can reproduce the selection logic.
- This decision should be revisited if the business requirement shifts from
  robustness toward maximum parsimony (e.g., regulatory constraint on number
  of features in the scoring model).
