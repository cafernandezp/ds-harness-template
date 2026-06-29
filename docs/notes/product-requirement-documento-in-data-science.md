# Designing PRDs for Data Science & Machine Learning Projects
### A practical, opinionated guide using binary classification as the running example

> **Last updated:** 2026-06-03
> **Scope:** Binary classification as a running example; principles generalize to regression, ranking, generative, and multi-model systems.

---

## TL;DR

A DS/ML PRD is **not** a software PRD with a model bolted on. Because ML systems are data-dependent, probabilistic, and decay over time, the document must specify the *data contract, success metrics, validation strategy, and monitoring/retraining plan* up front. The absence of these is the single biggest reason most ML projects never reach or survive production.

This report provides a complete, copy-pasteable 12-section Markdown PRD template, a canonical ML repo layout showing where the PRD lives (`docs/prd.md`) and how it links to the README, model card, data card, and experiment log, and a full worked example for a **customer-churn binary classifier** (ChurnGuard). It also includes a critical analysis of **what level of detail actually belongs in a PRD vs. what belongs in design documents and experiment logs** — a distinction that most teams get wrong. Finally, it covers how to use the PRD as the foundational context document for AI coding agents (Claude Code and OpenAI Codex).

---

## Key Findings

**Problem framing is where ML projects die, not modeling.** Weak problem framing plus the prototype-to-production gap are recurring root causes of ML project failure. A PRD's job is to force these decisions early, when changing them is cheap.

**Metrics must be designed before the model exists.** Google's *Rules of Machine Learning* (Rule #2) explicitly says "make metrics design and implementation a priority." A DS/ML PRD must separate the *business KPI* from the *ML metric* and define the mapping between them before a single line of training code is written.

**The data contract is the heart of the document.** Training-serving skew and data leakage are the dominant silent failure modes. A PRD must specify schema, point-in-time correctness, labeling strategy, and the train/serve feature parity requirement.

**The PRD belongs in the repo as a living, version-controlled document** (`docs/prd.md`), not in a wiki that rots. It is the parent document from which the model card, data card, experiment log, and README all descend.

**AI coding agents work dramatically better from a structured spec** — but the spec they consume must be decomposed and concise. GitHub Spec Kit's `/specify → /plan → /tasks → /implement` and Anthropic's explore → plan → code → commit are the two workflows to anchor on.

---

## 1. Context and motivation: why DS/ML PRDs are different

A traditional software PRD describes deterministic behavior: given input X, the system must produce output Y, and you can write an acceptance test that passes or fails. Machine learning breaks every part of that assumption. As Chip Huyen argues in *Designing Machine Learning Systems*, ML systems are "complex because they consist of many different components and involve many different stakeholders" and "unique because they're data dependent, with data varying wildly from one use case to the next." Three structural differences drive everything about how the PRD must change.

**The behavior is learned from data, not specified in code.** You cannot write `assert predict(x) == y` for all x. The system's behavior is an emergent property of the training data, so the data itself becomes a first-class requirement. This is why the academic literature (Serban et al., *Adoption and Effects of Software Engineering Best Practices in Machine Learning*) distinguishes "traditional" practices, "modified" practices, and entirely "new" practices designed for ML — data versioning, training-serving skew tests, and model documentation have no analog in standard software engineering.

**The output is probabilistic and the success criterion is statistical.** A churn classifier does not "work" or "not work" — it has a precision-recall tradeoff that you tune to a business cost structure. The PRD must therefore encode *thresholds* and a *validation strategy*, not a binary pass/fail.

**The system decays.** Traditional software is static until you change it; ML models exist in a state of continuous silent degradation as the world drifts away from the training distribution. The PRD must specify monitoring and a retraining plan as launch requirements, not afterthoughts.

**Common failure modes when the PRD is absent or weak:**

The InfoQ analysis of why ML projects fail names "weak problem framing" and late changes to business goals as primary culprits: "Late changes to business goals require adjustments to data, objective functions, and pipelines, which may result in the loss of work." Beyond framing, *metric mismatch* is equally dangerous — optimizing accuracy on an imbalanced churn dataset yields a model that predicts "no churn" for everyone and scores 80%+ while being useless. Without a metric specification, this passes unnoticed. *Data leakage* is the classic silent killer: a model learns a feature that encodes the label (e.g., hospital identity predicts cancer because certain hospitals only treat cancer patients) and the inflated offline metrics only crash at deployment. *Training-serving skew* is the most common production failure mode: features computed one way in the training notebook and another way in the production service silently diverge and degrade model quality. Finally, the *prototype-to-production gap* means a notebook that scores 0.79 AUC never becomes a service because nobody specified latency, throughput, explainability, or rollback requirements.

> **Opinion:** The DS/ML PRD's highest-value function is not documentation — it is *forcing function*. It makes the team commit to a falsifiable business hypothesis, a data contract, and a kill criterion before burning GPU budget. If you only adopt one section from this guide, adopt the success-metrics section.

---

## 2. A concrete binary classification example: subscription churn prediction

We will use a single running example throughout this guide: **"ChurnGuard," a customer-churn prediction model for a B2C subscription business** (a meal-kit or streaming-style monthly subscription service).

**Business context.** The company has approximately 2 million active monthly subscribers. Monthly logo churn is around 5.5%. The retention team can run a targeted intervention — a discount offer plus concierge outreach — but the intervention has a cost of roughly $12 per contacted customer in discount plus labor, and there is limited capacity of approximately 40,000 outreach slots per month. The goal is to identify, each month, the subscribers most likely to cancel in the next 30 days so the retention team spends its fixed budget on the customers where intervention has the highest expected value.

**ML framing.** Binary classification. For each active subscriber at the start of a month, predict `P(churn within next 30 days)`. Positive class = churned. This is an imbalanced problem with a roughly 5.5% positive rate.

**Data landscape.** The project draws from four data sources: subscription and billing data in the warehouse (plan type, tenure, price, payment failures, contract type); product engagement events from the event stream transformed into the warehouse (logins, sessions, orders, skips, support tickets); customer profile data (acquisition channel, geography, demographics — handled carefully for fairness); and labels derived from billing records (did the subscriber cancel within the 30-day window?). Labels mature with a 30-day lag, which is a key timing constraint documented explicitly in the PRD.

**Success metrics.** The business KPI is a measurable reduction in 30-day churn within the contacted cohort versus a randomized holdout control group, combined with positive net revenue retained after accounting for the $12-per-contact cost. The ML metric is precision and recall at top-K (K = 40,000), with PR-AUC as the primary threshold-independent summary. Accuracy is explicitly rejected as a metric because of the class imbalance.

**Stakeholders.** The Retention/Marketing PM owns the business KPI and outreach budget. Data Science owns the model. ML/Platform Engineering owns the pipeline and serving infrastructure. Data Engineering owns the upstream tables. Legal and Privacy review the use of demographic data. Finance owns the cost model and revenue-retained definition.

This example is realistic. In a peer-reviewed study on churn prediction (PMC12929532), gradient boosting was the strongest model family — XGBoost attaining AUC-ROC of 0.932 — and threshold tuning mattered significantly: threshold optimization at 0.528 (not the default 0.5) balanced precision and recall while reducing false negatives by 15%. This grounds the targets we set later and is a reminder that the right operating threshold is rarely 0.5.

---

## 3. Model ML project repository structure

The layout below synthesizes the Cookiecutter Data Science standard from DrivenData, Goku Mohandas's Made With ML conventions, and patterns from Chip Huyen's work. The guiding principle, in DrivenData's words, is "a logical, reasonably standardized, but flexible project structure."

```
churnguard/
├── README.md                  # Entry point: what/why, quickstart, links to all docs
├── pyproject.toml             # Package metadata + tool config (ruff, black, pytest)
├── Makefile                   # `make data`, `make train`, `make test`, `make serve`
├── .pre-commit-config.yaml    # Linters/formatters run before commit
├── .gitignore
├── CLAUDE.md                  # AI-agent context (symlinked to AGENTS.md) — see §7
├── AGENTS.md
│
├── docs/
│   ├── prd.md                 # ⭐ THE PRD — source of truth for the project
│   ├── model_card.md          # Model documentation (Google model card format)
│   ├── data_card.md           # Dataset documentation (Google data card format)
│   ├── experiment_log.md      # Append-only log of experiments + decisions
│   └── adr/                   # Architecture Decision Records
│
├── data/
│   ├── raw/                   # Immutable source extracts (never edited)
│   ├── interim/               # Intermediate transformed data
│   ├── processed/             # Final feature sets for modeling
│   └── external/              # Third-party data
│
├── notebooks/                 # EXPLORATION ONLY. Naming: 1.0-jdoe-eda-churn.ipynb
│
├── src/churnguard/
│   ├── config.py              # Config dataclasses / Hydra configs
│   ├── data/                  # make_dataset.py, validate.py (schema/quality checks)
│   ├── features/              # build_features.py — SHARED by train AND serve
│   ├── models/                # train.py, predict.py, evaluate.py
│   └── serve/                 # FastAPI app, batch_inference.py
│
├── configs/                   # YAML: model params, thresholds, feature lists
├── models/                    # Serialized model artifacts + metadata (gitignored/DVC)
├── tests/                     # Unit + data tests + train/serve parity tests
├── reports/figures/           # Generated evaluation plots
└── .github/workflows/         # CI/CD: lint, test, train, deploy
```

**Why the PRD lives in `docs/prd.md` inside the repo.** The PRD must be version-controlled alongside the code it governs, so that a `git blame` on a threshold change in `configs/` can be traced to a PRD revision, and so that a pull request can update code and the spec atomically. A PRD in Confluence or Google Docs rots the moment the code diverges from it; a PRD in the repo can be enforced in code review.

**How the PRD connects to the other documents.** Think of this as a parent-to-child hierarchy of decreasing abstraction and increasing specificity. The README is the *front door* — a short orientation that links to the PRD and explains how to run things. The PRD is the *contract*, answering what we are building, for whom, with what data, to what bar. The data card (`docs/data_card.md`) is the *realized* description of the dataset that the PRD's data-requirements section asked for — Google's Data Cards Playbook defines these as "structured summaries of essential facts about various aspects of ML datasets needed by stakeholders." The model card (`docs/model_card.md`) is the *realized* description of the trained model that the PRD's model-requirements section asked for, introduced by Mitchell et al. (2019) and documenting intended use, evaluation metrics sliced across groups, limitations, and ethical considerations. The experiment log is the *audit trail* connecting the two. The mental model is: **PRD = specification (forward-looking) → experiment log = process (the journey) → model card + data card = realized documentation (backward-looking).**

---

## 4. The DS/ML PRD template (full Markdown)

Below is the complete 12-section template. Each section is preceded by a short note on *why it exists*. Copy this into `docs/prd.md` and fill it in. Section 5 of this guide (the critical analysis) discusses in depth which implementation details belong here and which do not — read that section before filling in the template.

````markdown
# PRD: [Project Name] — [One-line description]

| Field | Value |
|---|---|
| Status | Draft / In Review / Approved / In Production |
| Author(s) | |
| Reviewers | DS lead, ML eng, Product, Legal |
| Last updated | YYYY-MM-DD |
| Target launch | |

## 1. Project overview & business context
<!--
Why this section exists: anchors the whole project to a business reason and a "why now."
Prevents ML-for-ML's-sake. Per Google Rule #1, justify ML over a simple baseline first.
-->
- **Problem statement:** What business problem are we solving? Who has it?
- **Why now / why ML:** Why is a heuristic or rule-based system insufficient?
- **Business hypothesis:** "We believe that [predicting X] will let us [take action Y] to achieve [outcome Z]."
- **Stakeholders & RACI:** Who owns the KPI, the model, the pipeline, the data, sign-off.

## 2. Problem framing (ML task definition)
<!--
Why: the same business problem can be framed many ways; this fixes the framing so
data collection and metric design follow correctly.
-->
- **ML task type:** (e.g., binary classification.)
- **Unit of prediction:** What entity, at what point in time?
- **Input (X):** Feature space at a high level + the point-in-time at which features are available.
- **Output (y):** Label definition and prediction horizon.
- **Label definition & maturation lag:** Exactly how the label is computed and how long until it's known.
- **Baseline:** The non-ML heuristic we must beat. Be specific enough to make this falsifiable.

## 3. Success metrics
<!--
Why: per Google Rule #2, design metrics first. This section separates business value
from model math and defines "done." It is the single most important section.
-->
- **Business KPI(s):** The metric the business cares about + how it's measured
  (ideally a controlled experiment vs. a randomized holdout group).
- **ML metric(s):** The offline metric(s) optimized, chosen to reflect the operating point
  (e.g., precision@K, recall@K, PR-AUC). State explicitly why accuracy is or is not appropriate.
- **Operating point / threshold:** The decision threshold and the cost rationale
  (false-positive cost vs. false-negative cost — formalize this as a cost matrix if possible).
- **Launch bar:** Minimum metric values required to ship.
- **Kill criteria:** Metric values below which we stop the project without further iteration.
- **Validation strategy:** Data split type and rationale (prefer temporal split for time-dependent data);
  cross-validation scheme if applicable; the holdout / golden evaluation set.

## 4. Data requirements
<!--
Why: the data contract is the core of an ML PRD. Most production failures originate here.
This section becomes the source for automated data tests in tests/data/.
-->
- **Sources & owners:** Each source table or stream, its owner, freshness, and SLA.
- **Schema:** Key fields, types, and the entity/timestamp keys for point-in-time joins.
- **Volume & history:** How much data, over what period.
- **Quality requirements:** Null-rate ceilings, allowed ranges, expected distributions, referential integrity.
- **Labeling strategy:** Where labels come from, label lag, label noise, and class balance.
- **Leakage controls:** Explicit list of features that must use only pre-prediction-time information;
  point-in-time correctness requirement stated as a testable constraint.
- **Privacy / compliance:** PII handling, consent, retention policy, which sensitive attributes
  may or may not be used.

## 5. Feature engineering requirements
<!--
Why: defines the feature contract and — critically — the train/serve parity requirement.
This section does NOT specify which feature selection method to use (see §5 of the guide).
-->
- **Feature groups:** Categories of features and business rationale for each group.
- **Train/serve parity:** Requirement that training and serving compute features from the
  same code path (e.g., a shared transform module or feature store). This is a system requirement.
- **Freshness:** How current each feature must be at serving time.
- **Forbidden features:** Anything that leaks the label or is unavailable at inference time.
  This list must be exhaustive and reviewed by the team.

## 6. Model requirements
<!--
Why: constrains the solution space against real-world deployment limits.
Does NOT specify the algorithm — that is an implementation decision (see §5 of the guide).
-->
- **Algorithm constraints:** Any hard restrictions (e.g., must be deployable as ONNX,
  must be interpretable by a regulator). Include a start-simple mandate: the first candidate
  must be a simple, explainable baseline.
- **Latency / throughput:** p99 latency requirement for online; batch window size for batch.
- **Explainability:** Required level and format (e.g., per-prediction SHAP values for
  human-facing use, global feature importance for stakeholder reporting).
- **Fairness:** Protected groups, the chosen fairness metric and its rationale (e.g.,
  equal opportunity for lending decisions; demographic-parity ratio for outreach targeting),
  and the acceptable disparity bound (e.g., the four-fifths / 80% rule from employment law).
- **Calibration:** Whether probability calibration is required and why
  (important when probabilities drive expected-value calculations).

## 7. Training & evaluation pipeline requirements
<!--
Why: makes reproducibility and evaluation rigor a launch requirement, not a hope.
-->
- **Reproducibility:** Versioning requirements for code, data, and config; seeds; experiment tracking tool.
- **Evaluation protocol:** Offline metrics, sliced evaluation (by segment, tenure, geography),
  and required sanity checks (e.g., model must beat baseline; predictions must be calibrated).
- **Retraining cadence (design):** How often models are retrained and on what data window.
- **Acceptance gate:** Automated checks a candidate model must pass before promotion to production.

## 8. Deployment & serving requirements
<!--
Why: closes the prototype-to-production gap that kills most ML projects.
-->
- **Serving mode:** Batch vs. online vs. streaming; integration points with downstream systems.
- **Infrastructure:** Where it runs; scaling and availability expectations.
- **Rollout strategy:** Shadow mode → canary → full rollout; A/B test or holdout control structure.
- **Rollback:** How to revert to the previous model; the fallback behavior.

## 9. Monitoring & maintenance plan
<!--
Why: ML decays. Monitoring and retraining are launch requirements, not post-launch concerns.
-->
- **Operational monitoring:** Latency, error rates, throughput.
- **Data/feature monitoring:** Drift detection (e.g., PSI thresholds), train/serve skew checks,
  null spikes.
- **Model-quality monitoring:** Live metric tracking once labels mature; prediction-distribution
  monitoring before labels arrive.
- **Retraining triggers:** Time-based and/or drift-based thresholds; escalation path and on-call ownership.

## 10. Risks, assumptions & out-of-scope
<!--
Why: surfaces blind spots early and prevents scope creep.
-->
- **Assumptions:** What must be true for this project to succeed (e.g., label lag is stable,
  upstream tables are maintained, business intervention capacity stays at 40K/month).
- **Risks & mitigations:** Data risks, model risks, ethical risks, operational risks.
- **Out of scope (non-goals):** Explicitly list what this project will NOT do. This is as
  important as the scope itself.

## 11. Milestones & timeline
<!--
Prefer stages of 2–3 weeks each, where each stage delivers end-to-end utility.
The first milestone should always be an end-to-end pipeline with a simple baseline, not
a best-possible model. Reference Google Rule #4.
-->

## 12. Revision history
<!--
Why: the PRD is a living document; track how requirements evolved and why.
-->
| Date | Author | Change | Reason |
|---|---|---|---|
````

**Worked snippets for ChurnGuard (selected critical sections filled in):**

To make the template concrete, here are the two most decision-heavy sections completed for our running example.

**§3 Success metrics (ChurnGuard):**
The business KPI is a measurable reduction in 30-day churn within the contacted cohort versus a randomized holdout control, combined with positive net revenue retained after the $12-per-contact cost (Finance must validate the cost model before this section is approved). The ML metric is **precision@40K and recall@40K** — because the team's monthly capacity is exactly 40,000 contacts — with **PR-AUC** as the primary threshold-independent summary. Accuracy is explicitly rejected because the base rate is approximately 5.5% and a naive "predict no churn" model would achieve above 90% accuracy. The launch bar is precision@40K ≥ 0.30 and recall@40K ≥ 0.25 on the temporal holdout, meaning of 40,000 contacts, at least 12,000 are true churners capturing at least 25% of all monthly churners. The kill criterion is: if PR-AUC does not exceed the engagement-decile baseline by more than 0.03 after two full modeling iterations, the project stops. Validation uses a **temporal split** — train on months t-18 through t-2, validate on t-1, test on t — with no random splits because random splits would leak future information.

**§6 Fairness (ChurnGuard):**
Protected attributes are age band and geography. The fairness metric is **equal opportunity** (equal true-positive rate across groups), so that eligible churners are equally likely to receive a retention offer regardless of their demographic group. The acceptable bound is TPR disparity within the four-fifths (80%) rule, implemented via the demographic-parity ratio in Fairlearn. Demographic attributes are used for *auditing only* and may not be model features until Legal provides written sign-off. This requirement must be validated in the evaluation protocol (§7) before any production promotion.

---

## 5. What level of detail belongs in a PRD? (Critical analysis)

This section is intentionally critical. Most DS/ML PRDs get the level of detail wrong in one of two ways: they either under-specify and leave stakeholders without a real contract, or they over-specify implementation details that the data scientist should own. Understanding this distinction is the skill that makes the difference between a PRD that drives a project and a PRD that nobody reads.

### The fundamental principle: PRDs are requirements documents, not design documents

A requirements document answers three questions: what does success look like, what constraints must be respected, and what are the non-negotiable limits? A design document answers a different question: how will we achieve it? When a PRD specifies "use L1 regularization for feature selection" or "split the data 80/20" or "use logistic regression as your baseline," it has crossed from requirements into design — and that is a category error with three concrete consequences.

**You are making decisions you do not yet have data to make.** The choice of feature selection method depends on the feature correlation structure, the cardinality of categorical variables, and the model family ultimately chosen. You cannot know the right method before seeing the data in detail. If you lock it in the PRD, you either constrain the team unnecessarily or the team ignores the PRD — both outcomes undermine the document's authority.

**You are doing the ML scientist's job for them, and doing it worse.** The ML scientist's job is to find the best solution within the constraints given. If the PRD specifies the method, the requirement document has substituted its judgment for the expert's — before the expert has seen the data. A good PRD specifies the performance bar and the constraints; it does not specify the path to the bar.

**You are creating a document that becomes stale immediately.** Every implementation detail you add is something that will need to be updated when the project evolves, when the data turns out to be different from expectations, or when a first attempt fails and requires a different approach. A PRD that is full of implementation details is outdated by the second week and evolves into a document nobody reads — which defeats its entire purpose.

### The blurry middle ground: when implementation decisions are actually requirements in disguise

The real skill is recognizing that some decisions look like "how" decisions but are actually "what" decisions because they have business, system-level, or ethical implications that go beyond the data scientist's discretion. These belong in the PRD, and getting them out of the document by calling them "implementation details" is equally dangerous.

**Temporal split vs. random split.** Requiring a temporal split is NOT a data scientist's implementation preference — it is a REQUIREMENT that follows from the time-series nature of the deployment scenario. A random split on temporal data leaks future information into training and produces inflated offline metrics that do not translate to production performance. A PM or ML lead who discovers post-launch that evaluation used random splits on time-indexed data would rightly invalidate the entire evaluation history. This belongs in the PRD. What the exact split ratios are (80/20 vs. 70/15/15 vs. rolling-window) does NOT belong in the PRD.

**Train/serve feature parity.** Requiring that features be computed from a shared code path is a SYSTEM ARCHITECTURE requirement with implications for engineering scope, platform design, and operational risk. It is not a data scientist's preference — it is a constraint that prevents the leading cause of silent production degradation. This belongs in the PRD. Which specific framework implements the shared path (Feast, Tecton, a shared Python module, a custom service) does NOT belong in the PRD.

**"Start with a simple, interpretable baseline."** This is a PROCESS requirement driven by stakeholder communication needs, risk management, and the practical wisdom encoded in Google's Rule #4. It does not say "use logistic regression"; it says "demonstrate progress against a baseline that stakeholders can understand and that can serve as a fallback." This belongs in the PRD. The specific algorithm that implements the baseline — logistic regression, a decision tree, a threshold rule on a single feature — does NOT belong in the PRD.

**Fairness metric selection.** Which fairness metric to compute (equal opportunity vs. demographic parity vs. predictive parity) is an ethical and sometimes a legal requirement. The choice encodes a value judgment about which kind of discrimination is most harmful in the given context — this is a decision for the organization's leadership, legal counsel, and affected stakeholders, not for the data scientist to make unilaterally. This belongs in the PRD. The specific library used to compute the metric (Fairlearn, AIF360, a custom implementation) does NOT belong in the PRD.

### The practical test: a heuristic for every line

Before adding any line to the PRD, ask yourself two questions. First: "Would the Product Manager, Finance lead, or Legal team need to review and approve this decision?" If yes, it belongs in the PRD. If it is purely a technical judgment call, it belongs in the technical design document, the experiment log, or a config file. Second: "Can this requirement be expressed as a test that a non-ML-expert could run and get a binary pass/fail result?" The requirement "PR-AUC ≥ 0.45 on the temporal holdout" passes this test. The requirement "use gradient boosted trees with max_depth ≤ 6" does not — a non-expert cannot evaluate whether max_depth of 6 is the right choice. The requirement "the model must return a prediction in ≤ 200ms at the 99th percentile" passes this test. "Use ONNX runtime for inference" does not.

### Where implementation details actually belong

Feature selection strategy and rationale belong in a **Technical Design Document** (a separate `docs/design.md` or an Architecture Decision Record in `docs/adr/`). Exact train/validation/test ratios belong in `configs/experiment.yaml` and documented in an **experiment log entry**. Which specific baseline model was chosen and why belongs in **experiment log entry #001**, the baseline run. Hyperparameters and their tuning history belong in `configs/` and tracked in the **MLflow or Weights & Biases experiment tracker**. The specific feature engineering pipeline implementation belongs in `src/churnguard/features/` with inline documentation.

### The two failure modes and where they lead

**PRD inflation** — the more dangerous failure mode — happens when data scientists write the PRD without PM involvement and produce what is effectively a research plan. Every methodological decision, every tool choice, every algorithm variant goes into the document. The result is exhausting to read (typically running to 30–50 pages), becomes stale by the second week, contains decisions that are wrong because they were made before seeing the data, and undermines the team's confidence in the document as an authoritative source. When nobody trusts the PRD, the project loses its contract and devolves to informal decisions that leave no audit trail.

**PRD imprecision** — the opposite failure — produces a document so high-level that it says nothing testable. "The model should be accurate and fair" is not a requirement. "The model must achieve PR-AUC ≥ 0.45 on the temporal holdout, with equal-opportunity TPR disparity within the 80% rule for age bands, within a 30-day label window, evaluated on the held-out month" IS a requirement. The skill is specificity at the right level of abstraction: specific enough to be falsifiable, abstract enough to leave implementation decisions to the people qualified to make them.

### What this means for the template in section 4

Re-reading the template in section 4 with this lens, you will notice that the feature engineering section (§5 of the template) is deliberately at the contract level — it specifies the parity requirement and the forbidden features list, not the selection algorithm. The model requirements section (§6 of the template) specifies explainability format and fairness metric, not the model family. The validation strategy in the success metrics section (§3 of the template) specifies temporal split as a requirement, not the split ratios. If you find yourself filling in the template with sentences like "we will use Lasso to select features" or "we will use an 80/20 split" or "the baseline will be logistic regression," that is a signal you have drifted from requirements into design — move those decisions to the appropriate technical document, not the PRD.

---

## 6. How the PRD maps to the ML workflow

Each PRD section is the specification for a phase of the ML lifecycle. The lifecycle is iterative — data, model, and monitoring loops feed back into each other — but the mapping from PRD section to lifecycle phase is clean and worth making explicit.

| ML lifecycle phase | Driven by PRD section(s) | What the PRD pre-commits |
|---|---|---|
| **Problem definition** | §1 Overview, §2 Framing | Business hypothesis, task type, baseline to beat |
| **Data collection** | §4 Data requirements | Sources, schema, quality bars, labeling, leakage controls |
| **Feature engineering** | §5 Feature requirements | Feature groups, train/serve parity, forbidden features |
| **Model training** | §6 Model req., §7 Pipeline | Algorithm constraints, reproducibility, retraining design |
| **Evaluation** | §3 Metrics, §7 Pipeline | Metrics, thresholds, sliced eval, validation split, acceptance gate |
| **Deployment** | §8 Serving | Serving mode, rollout, rollback |
| **Monitoring** | §9 Monitoring, §3 Metrics | Drift/skew checks, live metric tracking, retraining triggers |

The key insight is that the **metrics section (§3) appears twice** — at evaluation and at monitoring — because the same metric that gates the launch must be tracked in production. Similarly, the **data and feature sections (§4–§5) are the contract that both training and serving must honor**, which is precisely how you prevent training-serving skew: by writing the parity requirement once in the PRD and enforcing it in both code paths.

A practical sequencing rule from Google's *Rules of ML* and Made With ML: build the **end-to-end pipeline with a dumb baseline first** (Rule #4: "Keep the first model simple and get the infrastructure right"), prove the plumbing and the metric instrumentation, then iterate on the model. The PRD's milestones section (§11) should reflect this — milestone 1 is "end-to-end pipeline with an interpretable baseline model," not "best possible model."

---

## 7. Using the PRD with Claude Code, Codex, and Spec Kit

The PRD is the ideal foundational context document for AI coding agents — but you must use it correctly, because **dumping the whole PRD into the agent's always-on context file is counterproductive.**

### The two-file pattern: persistent context vs. the spec

AI coding agents read a small **persistent context file** at the start of every session — `CLAUDE.md` for Claude Code, `AGENTS.md` for OpenAI Codex. This file is loaded into every prompt, so it must be short. The PRD is a long reference document the agent should read on demand when planning specific tasks.

The correct pattern keeps `CLAUDE.md` / `AGENTS.md` short and points to the PRD rather than inlining it:

```markdown
# CLAUDE.md
This is ChurnGuard, a subscription churn binary classifier.
The authoritative spec is docs/prd.md — read it before planning any task.

Key constraints (non-negotiable):
- Features MUST be computed via src/churnguard/features/build_features.py (shared train+serve path).
- Use temporal splits only; never random splits (see prd.md §3 for rationale).
- Run `make test` (includes train/serve parity tests) before any commit.
- Demographic attributes (age, geography) must not appear as model features; use for auditing only.
```

**Why short matters — the evidence.** Anthropic's own guidance is that "CLAUDE.md is loaded every session, so only include things that apply broadly." Practitioner analysis from HumanLayer estimates frontier models follow roughly 150 to 200 instructions with reasonable consistency — with the caveat that Claude Code's system prompt already contains approximately 50 individual instructions, leaving roughly 100 to 150 usable slots. HumanLayer keeps its own root CLAUDE.md under 60 lines. On the Codex side, the file is silently truncated past 32 KiB by default. More importantly, a controlled study from ETH Zurich's SRI Lab (Gloaguen et al., *Evaluating AGENTS.md*, arXiv:2602.11988, 2026) found that LLM-generated context files *reduce* task success rates while increasing inference cost by over 20% on average. Developer-written files gave only about a 4% gain at up to 19% cost increase. The study concludes that context files should include only minimal requirements. The practical lesson: the context file should be minimal and *point to* the PRD; the PRD itself should be read deliberately during agent planning, not pasted wholesale into `CLAUDE.md`.

### Decomposing the PRD into agent tasks

Three converging workflows show how to turn the PRD into executable agent work.

**GitHub Spec Kit** formalizes spec-driven development with the chain `/specify → /plan → /tasks → /implement`. It scaffolds `spec.md`, `plan.md`, and a `tasks/` folder, decomposing the plan into tasks with dependency ordering, parallel-execution markers, exact file paths per task, and optional test-first structure. Your `docs/prd.md` is the `spec.md`; you run `/plan` and `/tasks` against it. Spec Kit's philosophy aligns with this guide's: "Specifications don't serve code — code serves specifications."

**Anthropic's Claude Code workflow** is explore → plan → code → commit. Enter plan mode (the agent reads files and answers questions without making changes), have it produce a detailed implementation plan you can edit, then switch to implementation, then commit. Anthropic's rule for when to skip planning is memorable: "If you could describe the diff in one sentence, skip the plan." For ChurnGuard, you would point Claude at `docs/prd.md` §4–§5 in plan mode and ask it to plan the data-validation and feature-build modules before writing any code. The critical discipline is giving the agent a verifiable check — tests, a build, a parity assertion — which maps directly to the PRD's acceptance gate.

**Amazon Kiro** uses a three-document spec workflow (requirements, design, and tasks) and lets developers trigger tasks one step at a time. This mirrors the PRD → plan → tasks decomposition and shows the pattern is converging across the industry.

A concrete task decomposition for ChurnGuard, derived section-by-section from the PRD:

```
Task 1 [PRD §4]: Implement src/churnguard/data/validate.py enforcing schema and quality bars;
                  write pytest tests for each quality constraint. [depends on: none]

Task 2 [PRD §5]: Implement src/churnguard/features/build_features.py as the single shared
                  transform; write a train/serve parity test that imports and runs the same
                  function in both contexts. [depends on: 1]

Task 3 [PRD §3, §7]: Implement temporal-split training + evaluate.py computing precision@40K,
                       recall@40K, PR-AUC, sliced by age band and geography. [depends on: 2]

Task 4 [PRD §8]: Wrap the model in a FastAPI service + batch inference module, calling the
                  same feature module as Task 2. Write an integration test. [depends on: 2, 3]

Task 5 [PRD §9]: Add PSI-based drift monitoring and train/serve skew checks with alerts. [depends on: 4]
```

Each task references the PRD section that generated it, maps to a falsifiable acceptance criterion already written in the PRD, and respects the dependency ordering that Spec Kit recommends.

### How the PRD evolves with the project

The PRD is a living document governed by its revision-history section. As experiments resolve open questions — for example, the temporal split reveals that label lag is actually 45 days rather than 30 — you update the PRD in the same pull request that changes the code, bump the revision table, and let the agent re-read the updated spec on its next planning pass. This keeps the spec and the implementation in lockstep.

---

## Recommendations

**Stage 1 (Week 0–1): Business contract.** Write `docs/prd.md` §1–§3 only, and get explicit sign-off on the business hypothesis, the baseline to beat, and the success metric with its threshold and kill criterion. Do not proceed until the PM and Finance agree on the cost model. If you cannot define a business KPI measurable via a controlled holdout, stop — this is not yet ready to be an ML project.

**Stage 2 (Week 1–2): Data contract.** Complete §4–§5. Stand up the data card and automated data-quality tests before feature engineering begins. Implement the shared feature module and a train/serve parity test on day one. If leakage controls or point-in-time joins cannot be guaranteed from the available tables, escalate to Data Engineering before any modeling — leakage discovered post-launch invalidates everything.

**Stage 3 (Week 2–3): End-to-end baseline.** Per Google Rule #4, ship the full pipeline (data → features → simple interpretable baseline → evaluation → shadow-mode serving) before optimizing the model. Populate the first rows of the experiment log. If the baseline already clears the launch bar, consider shipping it — you may not need a more complex model.

**Stage 4 (Week 3+): Model iteration.** Move to gradient-boosted trees (XGBoost or LightGBM are the empirically strong choice for tabular churn). Tune the threshold to the precision@K operating point using the cost matrix, run sliced evaluation and the fairness audit, and produce the model card. Promote only if the acceptance gate and fairness bound both pass.

**Stage 5 (Ongoing): Deploy and monitor.** Roll out shadow → canary → full rollout with a holdout control to measure the *business* KPI, not just the ML metric. Wire up drift and skew monitoring and retraining triggers. A PSI above approximately 0.2 on a critical feature or a sustained live-metric drop triggers retraining or rollback.

**For AI-agent-driven builds:** Keep `CLAUDE.md`/`AGENTS.md` short (under 60–100 lines, pointing to the PRD rather than inlining it). Decompose the PRD with Spec Kit's `/plan` and `/tasks` (or Claude Code's plan mode) into dependency-ordered tasks with explicit file paths and the PRD's acceptance criteria as the agent's verifiable checks.

---

## Caveats

**The "85% of AI projects fail" statistic is widely repeated but is frequently misquoted.** Gartner's original 2018 forecast was that "through 2022, 85% of AI projects will deliver erroneous outcomes due to bias in data, algorithms, or the teams managing them" — a prediction about *erroneous outcomes*, not wholesale project failure. A separate figure holds that only approximately 53% of AI prototypes reach production. Use these to motivate rigor, not as precise measured benchmarks. The trustworthy claim is that weak problem framing and the prototype-to-production gap are leading causes of ML project failure.

**The ChurnGuard numbers are illustrative.** The 2M subscribers, 5.5% churn, $12-per-contact, and 40K-slot capacity are constructed to make the metric and cost tradeoffs concrete. The XGBoost performance figures (AUC-ROC 0.932, threshold 0.528) are from one published Telco-churn study (PMC12929532) and will not transfer directly to a different dataset or business context.

**There is no single canonical ML PRD template.** Eugene Yan explicitly warns that templates followed blindly lead to fill-in-the-blanks thinking. Treat the 12-section structure as a checklist to provoke thinking, prune sections that don't apply, and add ones that do.

**AI-agent tooling is moving fast.** Command names, default limits, and model versions change frequently. The ETH Zurich finding that context files can reduce agent performance is from a 2026 controlled study with strong corroborating practitioner consensus, but the field is young.

**Fairness metrics are mutually incompatible in general.** You usually cannot satisfy demographic parity and equalized odds simultaneously (a well-established impossibility result in the fairness-in-ML literature). The PRD must pick the metric that matches the harm being prevented and document the tradeoff explicitly.

---

## References

### Foundational ML engineering and systems

1. Huyen, C. (2022). *Designing Machine Learning Systems: An Iterative Process for Production-Ready Applications*. O'Reilly Media. — The most comprehensive practitioner reference on end-to-end ML systems, covering data pipelines, training, deployment, and monitoring.

2. Zinkevich, M. (2019). *Rules of Machine Learning: Best Practices for ML Engineering*. Google. Available at: [martin.zinkevich.org/rules_of_ml](https://martin.zinkevich.org/rules_of_ml/rules_of_ml.pdf). — Google's canonical 43-rule guide; Rules #1, #2, and #4 are directly cited in this report.

3. Yan, E. (2020). *How to Write Design Docs for Machine Learning Systems*. Available at: [eugeneyan.com](https://eugeneyan.com/writing/ml-design-docs/). — Practical guide on ML design documents; source of the Why/What/How framework and the warning against template-driven thinking.

4. Mohandas, G. *Made With ML: Machine Learning Systems Design*. Anyscale. Available at: [madewithml.com](https://madewithml.com/courses/mlops/systems-design/). — Industry-practitioner curriculum on MLOps and systems design; source of the "every iteration should deliver end-to-end utility" and "manual before ML" principles.

### Model and data documentation standards

5. Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B., Spitzer, E., Raji, I. D., & Gebru, T. (2019). *Model Cards for Model Reporting*. Proceedings of the ACM Conference on Fairness, Accountability, and Transparency (FAccT), pp. 220–229. — Introduced the model card format referenced in §3 of this report.

6. Gebru, T., Morgenstern, J., Vecchione, B., Vaughan, J. W., Wallach, H., Daumé III, H., & Crawford, K. (2021). *Datasheets for Datasets*. Communications of the ACM, 64(12), 86–92. — The foundational reference for dataset documentation; companion to model cards.

7. Google PAIR. (2022). *Data Cards Playbook*. Google Research. Available at: [sites.research.google/datacardsplaybook](https://sites.research.google/datacardsplaybook/). — Operational guide for creating data cards as referenced in §3.

### Repository structure and project conventions

8. DrivenData. *Cookiecutter Data Science: A logical, reasonably standardized, but flexible project structure for doing and sharing data science work*. Available at: [cookiecutter-data-science.drivendata.org](https://cookiecutter-data-science.drivendata.org/). — Source of the repo layout conventions used in §3.

### Fairness in machine learning

9. Fairlearn Team. (2024). *Common Fairness Metrics: Demographic Parity and Equalized Odds*. Microsoft Research. Available at: [fairlearn.org](https://fairlearn.org/main/user_guide/assessment/common_fairness_metrics.html). — Reference implementation and documentation for the fairness metrics specified in §4 (template §6) and used in the ChurnGuard example.

10. Afrænkel, D. (2023). *Parity Measures in Fairness and Algorithmic Decision Making*. UC San Diego. Available at: [afraenkel.github.io/fairness-book](https://afraenkel.github.io/fairness-book/content/05-parity-measures.html). — Academic treatment of parity-based fairness metrics and the impossibility of simultaneous satisfaction of multiple fairness criteria.

### ML project failures and production challenges

11. Shankar, S., et al. (2022). *Why Most Machine Learning Projects Fail to Reach Production*. InfoQ. Available at: [infoq.com](https://www.infoq.com/articles/why-ml-projects-fail-production/). — Industry analysis of ML failure modes; source of the framing and prototype-to-production gap discussion in §1.

### Empirical ML research (ChurnGuard example grounding)

12. Al-Naami, B., et al. (2025). *Explainable AI-Driven Customer Churn Prediction: A Multi-Model Ensemble Approach with SHAP-Based Feature Analysis*. PubMed Central, PMC12929532. — Peer-reviewed study grounding the ChurnGuard performance targets (XGBoost AUC-ROC 0.932, threshold 0.528).

### AI coding agents and spec-driven development

13. Gloaguen, A., Pujar, S., Cirik, V., & Eichberg, M. (2026). *Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?* ETH Zurich SRI Lab. arXiv:2602.11988. — The controlled empirical study on AGENTS.md effectiveness cited in §7; key finding that auto-generated context files reduce agent success rates.

14. GitHub. (2025). *Spec Kit: A Toolkit to Help You Get Started with Spec-Driven Development*. Available at: [github.com/github/spec-kit](https://github.com/github/spec-kit). — The spec-driven development framework and `/specify → /plan → /tasks → /implement` workflow described in §7.

15. Anthropic. (2025–2026). *Claude Code Best Practices*. Available at: [code.claude.com/docs](https://code.claude.com/docs/en/best-practices). — Anthropic's official guidance on the explore → plan → code → commit workflow, CLAUDE.md design, and agentic task decomposition.

16. HumanLayer. (2025). *Writing a Good CLAUDE.md*. Available at: [humanlayer.dev/blog](https://www.humanlayer.dev/blog/writing-a-good-claude-md). — Practitioner analysis of CLAUDE.md instruction limits and the 60-line heuristic referenced in §7.

---

*Tags: `mlops`, `data-science`, `prd`, `product-requirements`, `binary-classification`, `ml-workflow`, `ai-agents`, `claude-code`, `feature-engineering`, `model-evaluation`*
