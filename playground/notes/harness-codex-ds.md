# Harness Engineering — Codex + Data Science

> Harness structure for DS projects with Codex.
> Core principle: **state lives on disk, not in chat.**
> Full traceability: from a line of code you can trace back to the original question.

---

## 4-Layer Documentation Model

```
One-off question          → ephemeral chat response (nothing saved)
Broad technical topic     → docs/research-reports/<slug>.md
Concrete project decision → docs/adr/adr-YYYY-MM-DD-<slug>.md
Execution plan            → docs/memory/plans/PLAN-XXX-<slug>.md
```

| Layer | Question it answers | Trigger | Who writes |
|---|---|---|---|
| **Research Report** | "What options exist for X?" | Non-trivial technical decision arises | ADVISOR (uses skill `ds-research-report`) |
| **ADR** | "Why does this project use X and not Y?" | Research report concludes → you choose an option | LEAD |
| **Exec Plan** | "How are we going to implement this?" | Decision is made, execution is missing | LEAD |
| **Feature** (backlog) | "What concrete task enters the sprint?" | Plan approved | LEAD |

**Full natural flow:**

```
Technical question arises
  └── ADVISOR writes docs/research-reports/cv-strategies.md
        └── You discuss options with LEAD
              └── LEAD writes docs/adr/adr-2026-06-18-stratified-kfold.md
                    └── LEAD writes docs/memory/plans/PLAN-012-cv-refactor.md
                          └── Plan approved → FEAT-012 in backlog.json
                                └── IMPLEMENTER executes → docs/memory/progress/impl_feat-012.md
                                      └── REVIEWER approves → docs/memory/progress/review_feat-012.md
```

---

## Folder Structure

```
repo-root/
├── AGENTS.md                                  ← Codex entry point
├── CHECKPOINTS.md                             ← verifiable "done" criteria
├── agents/                                    ← detailed instructions per agent
│   ├── leader.md
│   ├── implementer.md
│   ├── reviewer.md
│   └── advisor.md
├── skills/                                    ← skills invocable by agents
│   ├── function-conventions/
│   │   ├── SKILL.md                           ← naming, docstring, arg limit rules
│   │   ├── example.py                         ← reference function from the codebase
│   │   └── bad_example.py                     ← explicit violations to avoid
│   ├── create-adr/
│   │   ├── SKILL.md                           ← sections, frontmatter, when to write
│   │   └── example.md                         ← completed ADR as format reference
│   └── ds-research-report/
│       ├── SKILL.md                           ← structure, depth, neutrality rule
│       └── example.md                         ← completed research report as reference
├── docs/
│   ├── architecture.md                        ← NOT optional (see dedicated section)
│   ├── conventions.md
│   ├── research-reports/
│   │   ├── cv-strategies.md
│   │   ├── correlation-measures.md
│   │   └── target-encoding-leakage.md
│   └── adr/
│       ├── adr-2026-05-10-tech-stack.md
│       ├── adr-2026-06-01-train-val-test-split.md
│       └── adr-2026-06-18-stratified-kfold.md
├── docs/memory/
│   ├── backlog.json
│   ├── plans/
│   │   ├── PLAN-001-feature-selection-pipeline.md
│   │   └── PLAN-012-cv-refactor.md
│   └── progress/
│       ├── current.md
│       ├── history.md
│       ├── impl_<feature>.md
│       └── review_<feature>.md
├── src/
│   ├── data/
│   ├── features/
│   ├── models/
│   └── evaluation/
└── tests/
```

---

## File Reference Table

| File | Owner | Type | Purpose | Example content |
|---|---|---|---|---|
| `AGENTS.md` | LEAD | Map | Codex entry point. Describes four agents, points to `agents/`. No detailed rules — just the map. | `"Implementer instructions → agents/implementer.md"` |
| `CHECKPOINTS.md` | LEAD / REVIEWER | Criteria | Defines "done" in a verifiable way. Codex reads it before marking any task `done`. | `"[ ] Imputer fit on train fold only"`, `"[ ] VIF < 10 for all surviving predictors"` |
| `agents/leader.md` | — | Instructions | LEAD role: when to delegate, how to update `current.md`, how to close a session. | `"At session start: read current.md + backlog.json → decompose task → assign sub-tasks"` |
| `agents/implementer.md` | — | Instructions | IMPLEMENTER role. Output contract, prohibitions, how to report blockers. | `"Write result to progress/impl_<feature>.md. Return only the reference."` |
| `agents/reviewer.md` | — | Instructions | REVIEWER role. DS checklist: leakage, metrics, reproducibility, coverage. | `"If leakage found → REVISION NEEDED: exact line number."` |
| `agents/advisor.md` | — | Instructions | ADVISOR role (senior DS/ML profile). When to answer in chat vs when to write a research report. **Never modifies code or state.** | `"Technical decision with pipeline impact → docs/research-reports/<slug>.md using skill ds-research-report"` |
| `skills/function-conventions/SKILL.md` | — | Skill | Rules for writing functions: naming, docstring style, arg limits, side effects. | `"Functions must have a single responsibility. Max 3 arguments. Use verb-noun naming."` |
| `skills/function-conventions/example.py` | — | Skill asset | Real function from the codebase showing correct style. Agent matches this output. | A complete `compute_nadeau_bengio_se()` function with docstring and type hints |
| `skills/function-conventions/bad_example.py` | — | Skill asset | Same function with explicit violations annotated. Collapses ambiguity on what to avoid. | Same function with missing docstring, 6 args, unclear name, commented-out code |
| `skills/create-adr/SKILL.md` | — | Skill | Sections, frontmatter schema, when an ADR is required vs optional. | `"Required sections: Context / Alternatives / Decision / Consequences / Advice"` |
| `skills/create-adr/example.md` | — | Skill asset | Completed ADR as format reference. Agent matches structure and depth. | The 1-SE conservative rule ADR (see Example 2) |
| `skills/ds-research-report/SKILL.md` | — | Skill | Report structure, required depth, neutrality rule (no project decision), length. | `"Must present ≥2 alternatives with concrete tradeoffs. Must NOT recommend for this project."` |
| `skills/ds-research-report/example.md` | — | Skill asset | Completed research report as format reference. | The backward selection 1-SE report (see Example 1) |
| `docs/architecture.md` | LEAD | Critical reference | **Not optional.** Read before implementing any feature. Defines pipeline order, stack, split strategy, `src/` structure. | See dedicated section and full example below |
| `docs/conventions.md` | LEAD | Reference | Code style, variable naming, primary/secondary metrics, import rules. | `"Primary metric: MAE. Naming: X_train, y_train, X_val, y_val, X_test, y_test."` |
| `docs/research-reports/<slug>.md` | ADVISOR | Technical exploration | Deep report: theory, formulas, options, tradeoffs. **Neutral**: no project decision. Generated with skill `ds-research-report`. | See Example 1 |
| `docs/adr/adr-YYYY-MM-DD-<slug>.md` | LEAD | Binding decision | Format: Context / Alternatives / Decision / Consequences / Advice. Cites research report if one exists. | See Example 2 |
| `docs/memory/backlog.json` | LEAD | State | Features with `id`, `title`, `status`, `priority`, `depends_on`, `plan`, `adr`. **Only one feature `in_progress` at a time.** | See Example 4 |
| `docs/memory/plans/PLAN-XXX-<slug>.md` | LEAD | Tactical plan | How to implement a decision. States: `draft` → `approved` → `rejected`. Cites the ADR it derives from. | See Example 3 |
| `docs/memory/progress/current.md` | LEAD | Live state | Active session: current feature, sub-tasks, notes. Rewritten each session. | See Example 5 |
| `docs/memory/progress/history.md` | LEAD | Logbook | Append-only. Never edited. Survives context window resets. | `"## Session #008 — 2026-06-18 / Completed: FEAT-012 / Carry-forward: FEAT-013"` |
| `docs/memory/progress/impl_<feature>.md` | IMPLEMENTER | Trace | Files touched, test output, minor decisions. IMPLEMENTER returns **only the reference** to LEAD. | `"src/features/spearman_filter.py — 4 tests passed — threshold parametrizable"` |
| `docs/memory/progress/review_<feature>.md` | REVIEWER | Trace | Completed checklist, verdict (`APPROVED` / `REVISION NEEDED`), issues with exact line. | `"[x] No leakage / [ ] FAIL line 34 → REVISION NEEDED"` |

---

## Skills Design — Template vs Example vs Bad Example

| File | Purpose | When to include |
|---|---|---|
| `SKILL.md` | Rules and instructions | Always — it is the skill |
| `example.py / example.md` | Completed real output for the agent to match | Always — collapses format ambiguity |
| `template.py / template.md` | Skeleton with placeholders | When the agent must fill a fixed structure |
| `bad_example.py` | Explicit violations, annotated | For style skills where the gap between "understood" and "correct" is large |

**Why examples matter:** an agent reading only instructions will interpret them with its own defaults. An example collapses ambiguity — the agent pattern-matches the output format rather than inferring it. For `create-adr` and `ds-research-report`, the gap between "understanding the rule" and "producing the right artifact" is large enough that an example is not optional.

---

## `docs/architecture.md` — Why It Is Not Optional

Without this file the IMPLEMENTER operates without system context: it may write correct code in isolation but incompatible with the pipeline — wrong step order, different classes than established, unapproved libraries, or a split strategy that contradicts the active ADR. The REVIEWER cannot detect these inconsistencies without a reference for what "should be."

### Required sections

| Section | What it answers | Why the agent needs it |
|---|---|---|
| **Model objective** | What it predicts, problem type, audience | REVIEWER validates that the metric in code matches |
| **Data sources** | Origin, format, update frequency | IMPLEMENTER knows what to assume in the loader |
| **Transformation pipeline** | Step order, concrete sklearn class per step | Prevents reordering or duplicating steps |
| **Split strategy** | Ratios, strategy, `random_state` | REVIEWER checks leakage against this reference |
| **Library stack** | Approved libraries with pinned versions | IMPLEMENTER does not introduce unapproved deps |
| **`src/` structure** | Which module does what | IMPLEMENTER knows where to put new code |
| **Active ADRs** | List with links to `docs/adr/` | Prevents the agent from reopening closed decisions |

### Full example — Judicial Progress Score

```markdown
# architecture.md — Judicial Progress Score

last_updated: 2026-06-18

## Model Objective
Predict the progress of judicial cases (continuous score [0,1]).
Type: regression. Primary metric: MAE. Secondary: R².
Audience: legal business team — the score is communicated directly.

## Data Sources
- `data/raw/expedientes.parquet` — monthly snapshot from the judicial system
- `data/raw/variables_macro.csv` — external indicators, weekly update
- Final input format to the pipeline: pandas DataFrame with explicit dtypes

## Transformation Pipeline (mandatory order)

| Step | Class | Module | Fit on |
|---|---|---|---|
| 1. Numeric imputation | `SimpleImputer(strategy="median")` | `src/features/imputer.py` | train |
| 2. Categorical imputation | `SimpleImputer(strategy="most_frequent")` | `src/features/imputer.py` | train |
| 3. Ordinal encoding | `OrdinalEncoder` | `src/features/encoders.py` | train |
| 4. Nominal encoding | `TargetEncoder` (out-of-fold) | `src/features/encoders.py` | train |
| 5. NZV filter | `VarianceThreshold` | `src/features/selection.py` | train |
| 6. Spearman pairwise filter | `SpearmanFilter(threshold=0.85)` | `src/features/selection.py` | train |
| 7. VIF filter | `VIFFilter(threshold=10)` | `src/features/selection.py` | train |
| 8. Backward feature selection | `BackwardSelector` (conservative 1-SE rule) | `src/features/selection.py` | train |
| 9. Model | `XGBRegressor` | `src/models/xgb_model.py` | train |

All steps encapsulated in a `sklearn.Pipeline` serializable with `joblib`.

## Split Strategy
- Train: 70% / Val: 15% / Test: 15%
- Strategy: `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`
  (stratified by historical score decile)
- `random_state=42` across the entire project
- ADR: `docs/adr/adr-2026-06-18-stratified-kfold.md`

## Approved Library Stack

| Library | Version | Use |
|---|---|---|
| pandas | 2.2.2 | Data manipulation |
| numpy | 1.26.4 | Numerical operations |
| scikit-learn | 1.5.0 | Pipeline, transformers, CV |
| xgboost | 2.0.3 | Primary model |
| lightgbm | 4.3.0 | Available, not active in current pipeline |
| shap | 0.45.1 | Feature importance (out-of-fold) |
| scipy | 1.13.0 | Statistical tests, correlations |
| pingouin | 0.5.4 | ANOVA, partial correlations |
| statsmodels | 0.14.2 | VIF, auxiliary regression |
| joblib | 1.4.2 | Pipeline serialization |

Adding unlisted libraries requires a prior ADR.

## `src/` Structure

```
src/
├── data/
│   ├── loader.py          # loads and validates parquet schema
│   └── splitter.py        # reproducible train/val/test split
├── features/
│   ├── imputer.py         # SimpleImputer wrappers
│   ├── encoders.py        # OrdinalEncoder + out-of-fold TargetEncoder
│   └── selection.py       # NZV, SpearmanFilter, VIFFilter, BackwardSelector
├── models/
│   ├── xgb_model.py       # XGBRegressor with base hyperparameters
│   └── pipeline.py        # assembles the full sklearn Pipeline
└── evaluation/
    ├── metrics.py          # MAE, R², Nadeau-Bengio SE
    └── shap_analysis.py    # SHAP values + out-of-fold importance
```

## Active ADRs

| ADR | Decision |
|---|---|
| `adr-2026-05-10-tech-stack.md` | XGBoost as primary model, sklearn as pipeline framework |
| `adr-2026-06-01-train-val-test-split.md` | 70/15/15 ratios, random_state=42 |
| `adr-2026-06-12-spearman-pairwise-filter.md` | Spearman threshold=0.85, drop by % missing |
| `adr-2026-06-15-backward-selection-1se.md` | Conservative 1-SE rule with Nadeau-Bengio SE |
| `adr-2026-06-18-stratified-kfold.md` | StratifiedKFold n_splits=5 by score decile |
```

---

## Granularity — When to Write What

| Situation | Document |
|---|---|
| "What is bootstrap?" | Nothing (chat response) |
| "What is the best CV strategy for time-series data?" | **research-report** |
| "For this project we will use StratifiedKFold with 5 folds because…" | **ADR** (may cite research-report) |
| "To implement StratifiedKFold in FEAT-012 we will do the following steps…" | **exec-plan** (cites ADR) |
| Edge case inside an implementation | comment in `impl_<feature>.md` |

**Practical rule:** if the decision persists **beyond the current feature** and future developers inherit it → **ADR**. If it is tactical for this feature only → **exec plan**.

---

## The Fourth Agent: ADVISOR

| Aspect | LEAD / IMPLEMENTER / REVIEWER | ADVISOR |
|---|---|---|
| Invocation | Orchestrated (LEAD launches) | On-demand (you or LEAD invokes) |
| When used | Every backlog feature | When a DS/stats question arises |
| Disk output | Always | Only if the question is a relevant decision |
| Modifies code | IMPLEMENTER yes | ❌ never |
| Modifies harness state | LEAD yes | ❌ never |

### When ADVISOR writes vs only answers in chat

| Question type | Action |
|---|---|
| Conceptual ("what is heteroscedasticity?") | Chat, no file |
| Technical comparison with pipeline impact | **research-report** using `skills/ds-research-report/` |
| Synthesis of an already-written research report | Summary in chat → LEAD writes ADR |
| Tactical question inside IMPLEMENTER's work | Chat; if it requires a decision, escalates to LEAD |

ADVISOR **does not write ADRs** — that is a project decision and belongs to LEAD.

---

## Cross-Referencing Between Documents

Each document references the previous ones in its frontmatter. Full traceability.

```markdown
# research-report: cv-strategies.md
date: 2026-06-15
related-features: FEAT-012
```

```markdown
# ADR — StratifiedKFold as CV strategy
date: 2026-06-18
status: accepted
research-report: docs/research-reports/cv-strategies.md
```

```markdown
# PLAN-012 — Refactor CV strategy
status: approved
adr: docs/adr/adr-2026-06-18-stratified-kfold.md
estimated-features: FEAT-012
```

```json
{
  "id": "FEAT-012",
  "title": "Migrate CV to StratifiedKFold",
  "plan": "PLAN-012",
  "adr": "adr-2026-06-18-stratified-kfold"
}
```

---

## Anti-Telephone Rule

Subagents **write to disk** and return only a lightweight reference to LEAD.

```
# BAD — implementer returns full code in chat:
"Here is the code: def stratified_split(df, target, n_splits=5): ..."

# GOOD — implementer returns only a reference:
"done → docs/memory/progress/impl_feat-012.md"
```

---

## Full Session Flow

```
Session start
  └── LEAD reads current.md + backlog.json
        └── LEAD decomposes active feature → updates current.md
              ├── IMPLEMENTER executes sub-task
              │     └── writes impl_<feature>.md → returns reference
              │           └── REVIEWER reads impl_<feature>.md
              │                 └── writes review_<feature>.md → APPROVED or REVISION
              │                       └── (loop until APPROVED)
              └── Technical question arises → ADVISOR answers in chat
                    └── If relevant decision → ADVISOR writes research-report
                          └── LEAD writes ADR → plan → feature in backlog
Session end
  └── LEAD appends session to history.md
```

---

## Usage Examples

### Example 1 — Research Report (ADVISOR)

`docs/research-reports/backward-selection-1se-rule.md`:

```markdown
# Selection Criteria for the Final Subset in Backward Feature Selection

date: 2026-06-14
type: research-report
related-features: FEAT-008
author: ADVISOR

## Problem Context
In backward selection by out-of-fold SHAP elimination, each step produces a
cv_score_mean and a cv_score_se (Nadeau-Bengio corrected). We need a criterion
to choose the final subset, balancing performance and parsimony.

## Options Considered

### Alternative 1: Standard 1-SE Rule
Condition: `cv_score_mean ≤ threshold` (threshold = best_mean + best_se)
- Breiman's formulation; default in sklearn, caret, tidymodels
- More permissive: accepts more candidates → smaller models
- Ignores the uncertainty of each candidate's own estimate

### Alternative 2: Conservative 1-SE Rule
Condition: `cv_score_mean + cv_score_se ≤ threshold`
- Acknowledges that each candidate's mean also carries uncertainty
- Only accepts candidates where evidence is strong on both sides
- More restrictive: final model will retain more features

## Numerical Comparison

| Step | n_features | mean | se | upper | Standard | Conservative |
|---|---|---|---|---|---|---|
| 0 (best) | 12 | 0.2324 | 0.0013 | 0.2337 | ✓ | ✓ |
| 1 | 11 | 0.2325 | 0.0012 | 0.2337 | ✓ | ✓ ← chosen |
| 2 | 10 | 0.2335 | 0.0013 | 0.2348 | ✓ | ✗ |
| 3 | 9 | 0.2336 | 0.0014 | 0.2350 | ✓ ← chosen | ✗ |

## Neutral Recommendation
Maximum parsimony goal: standard rule.
Robustness under estimation uncertainty: conservative rule.
Choice depends on business context and risk tolerance.
```

---

### Example 2 — ADR (LEAD, from the research report)

`docs/adr/adr-2026-06-15-backward-selection-1se.md`:

```markdown
# Conservative 1-SE Rule for Backward Feature Selection

date: 2026-06-15
status: accepted
research-report: docs/research-reports/backward-selection-1se-rule.md

## Context
During backward selection for the Judicial Progress Score, the feature with
lowest out-of-fold SHAP importance is eliminated at each step. We need a
criterion to choose the final subset. The SE is Nadeau-Bengio corrected
(compensates for fold correlation in repeated CV).

## Alternatives
- **Standard 1-SE:** `cv_score_mean ≤ threshold` — more parsimony, ignores
  each candidate's own uncertainty
- **Conservative 1-SE:** `cv_score_mean + cv_score_se ≤ threshold` — accounts
  for uncertainty on both sides

## Decision
Conservative 1-SE rule is implemented (`cv_score_upper ≤ threshold`).
The score represents judicial progress, communicated directly to business.
We prefer to eliminate features only when evidence is robust even under
estimation uncertainty. Incorporating the SE in each candidate's condition
is coherent with the Nadeau-Bengio correction: explicitly acknowledging
uncertainty in all estimates, not only in the best step's.

## Consequences
Positive:
- Higher confidence that eliminated features contribute no real performance
- More stable selection across different seeds and partitions
- Methodological coherence with Nadeau-Bengio SE

Negative:
- Final model will have more features than with the standard rule
- Not directly comparable with standard literature implementations

## Advice
- Avoid switching to the standard rule to increase parsimony without documenting
  it: the change would alter the selected subset and make cross-version comparisons
  non-equivalent
- If sample size changes significantly, revisit whether Nadeau-Bengio SE remains
  appropriate or whether raw std is a more conservative bound
```

---

### Example 3 — Exec Plan (LEAD)

`docs/memory/plans/PLAN-008-backward-selection.md`:

```markdown
# PLAN-008 — Implement Backward Feature Selection with Conservative 1-SE Rule

status: approved
adr: docs/adr/adr-2026-06-15-backward-selection-1se.md
estimated-features: FEAT-008

## Problem
Build BackwardSelector that eliminates features by out-of-fold SHAP and
selects the final subset using the conservative 1-SE rule.

## Estimated Sub-tasks
1. `BackwardSelector` class in `src/features/selection.py`
   - Parameters: `model`, `n_folds`, `random_state`, `metric`
   - Nadeau-Bengio corrected SE
   - Log each step: n_features, mean, se, upper, within
2. Unit tests with synthetic data (n=200, 10 features with 3 irrelevant)
3. Integrate into Pipeline in `src/models/pipeline.py`
4. Save step history to `reports/backward_selection_steps.csv`

## Risks
- Compute cost: model is retrained with CV at each step
  → prototype with `n_folds=3` and reduced sample first
- Confirm BackwardSelector receives post-VIF DataFrame
  (see architecture.md step order)
```

---

### Example 4 — Backlog Entry

```json
{
  "id": "FEAT-008",
  "title": "Backward Feature Selection with conservative 1-SE rule",
  "status": "in_progress",
  "priority": "high",
  "plan": "PLAN-008",
  "adr": "adr-2026-06-15-backward-selection-1se",
  "depends_on": ["FEAT-007"],
  "acceptance_criteria": [
    "Conservative 1-SE rule implemented (cv_score_upper <= threshold)",
    "Nadeau-Bengio corrected SE",
    "Step log saved to reports/",
    "Unit test with 3 irrelevant features passes",
    "Integrated into sklearn Pipeline"
  ]
}
```

---

### Example 5 — Active Session in current.md

```markdown
## Session #011 — 2026-06-18

**Active feature:** FEAT-008 Backward Selection
**Plan:** PLAN-008
**ADR:** adr-2026-06-15-backward-selection-1se

| Sub-task | Assigned | Status | Review |
|---|---|---|---|
| ST-008-a: BackwardSelector class | IMPLEMENTER | done ✅ | APPROVED |
| ST-008-b: unit tests | IMPLEMENTER | done ✅ | APPROVED |
| ST-008-c: integrate into Pipeline | IMPLEMENTER | in-progress | — |
| ST-008-d: save log to reports/ | IMPLEMENTER | todo | — |

## Session Notes
- ADVISOR consulted on Nadeau-Bengio vs bootstrap SE → answered in chat,
  no research report needed (one-off question)
- Confirm with architecture.md that BackwardSelector comes after VIF filter
  before starting ST-008-c
```

---

### Example 6 — Blocker Detected by REVIEWER

`docs/memory/progress/review_feat-005.md`:

```markdown
## review — FEAT-005 Target encoding

**Checklist:**
- [x] Encoding implemented
- [ ] FAIL — leakage detected

**Issue:** src/features/encoders.py line 42:
  `encoder.fit(df[col], df[target])`
  `df` includes validation fold. Must be:
  `encoder.fit(X_train[col], y_train)`

**Verdict:** REVISION NEEDED
Action: IMPLEMENTER fix line 42, re-run tests, update impl_feat-005.md
```

---

### Example 7 — CHECKPOINTS.md

```markdown
# CHECKPOINTS.md

## CP-001: Environment
- [ ] `pip install -r requirements.txt` without errors
- [ ] `pytest tests/ -q` → 0 failed

## CP-002: Data
- [ ] `src/data/loader.py` raises ValueError if target column is missing
- [ ] 70/15/15 split reproducible with random_state=42
- [ ] No test set rows in train or val

## CP-003: Feature Engineering
- [ ] Imputer fit on train fold only
- [ ] TargetEncoder uses out-of-fold (no leakage)
- [ ] sklearn Pipeline serializable with joblib

## CP-004: Feature Selection
- [ ] NZV filter removes constant columns
- [ ] Spearman filter: no surviving pair with |rho| > 0.85
- [ ] VIF < 10 for all surviving predictors
- [ ] BackwardSelector uses conservative 1-SE rule (cv_score_upper ≤ threshold)
- [ ] Nadeau-Bengio corrected SE

## CP-005: Baseline Model
- [ ] MAE on validation set reported (not on test)
- [ ] Test set untouched until CP-006

## CP-006: Final Evaluation
- [ ] Single execution on test set
- [ ] Metrics: MAE (primary) + R² (secondary)
- [ ] SHAP values saved to reports/
```

---

## Anti-Patterns

| Anti-pattern | Why it fails | Solution |
|---|---|---|
| IMPLEMENTER edits `backlog.json` | Mixes roles, LEAD loses state control | Only LEAD edits backlog |
| REVIEWER rewrites code | Nobody reviewed the rewrite | `REVISION NEEDED` → IMPLEMENTER fixes |
| ADVISOR writes the ADR | Confuses "technical options" with "project decision" | ADVISOR writes research-report. LEAD writes ADR. |
| Two features `in_progress` at once | Fragmented context, traces overlap | One active feature at a time |
| IMPLEMENTER output goes to chat | Bloats context, no disk traceability | Always write `impl_<feature>.md`, return only reference |
| LEAD skips the ADR ("we decided this in chat") | Decision lost for future developers and agents | If it persists beyond the current feature → ADR required |
| Research report includes a decision | Mixes neutral exploration with project decision | Research report = options. ADR = decision. |
| Agent implements without reading `architecture.md` | Introduces out-of-order steps or unapproved libraries | `architecture.md` is mandatory reading before every feature |
| LEAD does not update `history.md` on session close | Next session starts without context | Mandatory close: append to `history.md` |
