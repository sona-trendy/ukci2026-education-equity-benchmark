# UKCI 2026 — Harmonised Open Panel Benchmark for Causal, Fairness-Aware, and Explainable Machine Learning in Educational Equity and SDG 4 Monitoring

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Data: WDI + WGI + UIS](https://img.shields.io/badge/Data-WDI%20%7C%20WGI%20%7C%20UIS-green.svg)](https://data.worldbank.org/)

A reproducible 12-country balanced panel dataset (2015–2024) and five-task benchmark suite supporting computational intelligence research on SDG 4 (Quality Education). The benchmark integrates data from the World Bank World Development Indicators (WDI), Worldwide Governance Indicators (WGI), and UNESCO Institute for Statistics (UIS) across 17 indicators spanning educational access, inequality, governance, and gender parity.

---

## Table of Contents

- [Overview](#overview)
- [Dataset](#dataset)
- [Benchmark Tasks](#benchmark-tasks)
- [Repository Structure](#repository-structure)
- [Installation](#installation)
- [Running the Pipeline](#running-the-pipeline)
- [Country Selection](#country-selection)
- [Data Sources](#data-sources)
- [Citation](#citation)
- [Licence](#licence)

---

## Overview

The benchmark provides:

- A **harmonised 12-country open panel** covering 2015–2024 with 17 indicators from three international sources
- **Five benchmark tasks** (A–E) covering outcome prediction, trajectory classification, fairness-aware learning, MNAR imputation, and causal machine learning
- **Documented MNAR structure**: structural missingness in inequality indicators follows an income-gradient mechanism, making this a principled stress-test for imputation and causal methods
- **Trajectory labels** assigning each country to one of four classes: Equity Expander (EE, n=7), Access Expander (AE, n=2), Inequality Reducer (IR, n=2), Data-Limited (DL, n=1)
- **Fully reproducible** pipeline from raw API calls to benchmark outputs

---

## Dataset

### Panel summary

| Property | Value |
|---|---|
| Countries | 12 |
| Years | 2015–2024 (10 years) |
| Observations | 120 country-year rows |
| Indicators | 17 |
| Overall completeness | 85.6% (post-interpolation) |
| Primary outcome Y | Lower-secondary completion rate (`sec_completion`) |
| Treatment W | Education expenditure % GDP (`edu_spend_gdp`) |
| Protected attribute A | Secondary school GPI (`gpi_sec`) |

### Country panel

| ISO | Country | Income tier | Trajectory |
|---|---|---|---|
| ESP | Spain | High income | EE |
| URY | Uruguay | High income | AE |
| CRI | Costa Rica | High income | EE |
| GEO | Georgia | Upper middle income | EE |
| IDN | Indonesia | Upper middle income | EE |
| THA | Thailand | Upper middle income | IR |
| KGZ | Kyrgyz Republic | Lower middle income | EE |
| UZB | Uzbekistan | Lower middle income | AE |
| BGD | Bangladesh | Lower middle income | EE |
| BFA | Burkina Faso | Low income | EE |
| BDI | Burundi | Low income | DL |
| RWA | Rwanda | Low income | IR |

EE=Equity Expander · AE=Access Expander · IR=Inequality Reducer · DL=Data-Limited

### Indicators

| Nice name | Description | Source | Role |
|---|---|---|---|
| `sec_completion` | Lower-secondary completion rate | UIS TRTP.1 | Y |
| `edu_spend_gdp` | Government education expenditure (% GDP) | WDI | W |
| `gpi_sec` | Gender parity index — secondary enrolment | UIS NERT.2.GPIA | A |
| `gpi_tert` | Gender parity index — tertiary enrolment | UIS GER.2.GPIA | A |
| `gini` | Gini index | WDI | X |
| `inc_share_low20` | Income share — lowest 20% | WDI | X |
| `poverty_215` | Poverty headcount ($2.15/day PPP) | WDI | X |
| `sec_enrol_gross` | Secondary net enrolment rate | UIS NERT.2.CP | X |
| `tert_enrol_gross` | Tertiary gross enrolment rate | WDI | X |
| `adult_literacy` | Adult literacy rate (15+) | UIS LR.AG15T99 | X |
| `youth_literacy` | Youth literacy rate (15–24) | UIS LR.AG15T24 | X |
| `gdp_pc_ppp` | GDP per capita (PPP 2017 USD) | WDI | X |
| `work_age_share` | Working-age population share (15–64) | WDI | X |
| `gov_effect` | Government effectiveness (WGI) | WGI | X |
| `voice_account` | Voice and accountability (WGI) | WGI | X |
| `ctrl_corrup` | Control of corruption (WGI) | WGI | X |
| `pop_total` | Total population | WDI | C |

Y=outcome · W=treatment · A=protected attribute · X=covariate · C=context

---

## Benchmark Tasks

### Task A — Outcome Prediction

Predict lower-secondary completion rate Y_it from lagged covariates X_{i,t-1}.
Models: Ridge, Random Forest, XGBoost, naïve baselines.
Protocols: temporal split (train 2015–2021 / test 2022–2024) and LOCO.

### Task B — Trajectory Classification

Classify countries into one of four trajectory classes (EE/AE/IR/DL)
from panel-level summary features. Evaluation: LOCO macro-F1.
Models: Logistic Regression, Linear SVC, Random Forest, k-NN.

### Task C — Fairness-Aware Prediction

Predict Y_it subject to group fairness constraints over gender parity (A_it).
Fairness metric: Δ-RMSE across GPI groups; ABROCA proxy.
Interventions: re-weighting, adversarial debiasing, threshold post-processing.

### Task D — MNAR Imputation

Benchmark imputation methods on the income-gradient MNAR structure
of inequality indicators (Gini, income share, poverty headcount).
Methods: Mean, Median, Forward-fill, Linear interpolation, KNN, MICE,
Income-group mean, GDP regression.

### Task E — Causal Machine Learning

Estimate the ATE and CATE of education expenditure W_it on completion Y_it,
controlling for confounders X_{i,t-1}.
Estimators: Naïve OLS, Fixed Effects, LinearDML, CausalForestDML (econml).
Subgroup CATEs by trajectory class and GPI group.

---

## Repository Structure

```
ukci2026-education-equity-benchmark/
│
├── configs/
│   ├── indicators.yml          # 17-indicator specification (source, role, clips)
│   └── pipeline.yml            # Runtime config (years, UIS mode, WB settings)
│
├── src/
│   ├── utils.py                # Shared fetch/load utilities (WDI, WGI, UIS)
│   ├── 01_download_sources.py  # Pull all sources, build coverage matrix
│   ├── 02_clean_merge_panel.py # Build 12-country panel, clip, interpolate
│   ├── 03_create_masks_and_labels.py  # Trajectory labels + train/test splits
│   ├── 04_descriptive_statistics.py   # Tables 1–3, figures
│   ├── 05_task_A_prediction.py        # Task A — outcome prediction
│   ├── 06_task_B_trajectory_classification.py  # Task B — classification
│   ├── 07_task_C_fairness_optimisation.py      # Task C — fairness
│   ├── 08_task_D_mnar_imputation.py            # Task D — imputation
│   └── 09_task_E_causal_ml.py                  # Task E — causal ML
│
├── data/
│   ├── raw/
│   │   └── uis/               
│   └── processed/
│       ├── panel_12countries_2015_2024.csv
│       ├── panel_12countries_imputed_2015_2024.csv
│       ├── interpolation_mask_2015_2024.csv
│       ├── trajectory_labels.csv
│       ├── trajectory_delta_summary.csv
│       └── train_test_splits/
│           ├── temporal_split.csv
│           └── loco_splits.csv
│
├── outputs/
│   ├── coverage_analytics/    # Step 1 coverage matrix and rankings
│   ├── results/               # Task A–E metrics and predictions
│   ├── tables/                # CSV and LaTeX tables for manuscript
│   └── figures/
│       └── panel_12/          # All figures
│
├── metadata/
│   └── country_selection_rationale.md
│
├── README.md
├── LICENSE
├── CITATION.cff
├── requirements.txt
└── environment.yml
```

---

## Installation

### Option 1 — pip

```bash
git clone https://github.com/your-org/ukci2026-education-equity-benchmark.git
cd ukci2026-education-equity-benchmark
pip install -r requirements.txt
```

### Option 2 — conda

```bash
conda env create -f environment.yml
conda activate ukci2026
```

### Requirements

```
python>=3.10
pandas>=2.0
numpy>=1.24
scikit-learn>=1.6
matplotlib>=3.7
seaborn>=0.12
requests>=2.28
pyyaml>=6.0
openpyxl>=3.1
econml>=0.15
xgboost>=1.7        # optional — Task A
pyarrow>=12.0       # optional — Parquet output
scipy>=1.10         # optional — LaTeX significance stars in Table 2
```

---

## Running the Pipeline

### UIS data access

The pipeline supports two modes for UNESCO UIS data. Set `uis.mode` in `configs/pipeline.yml`:

```yaml
uis:
  mode: "api"    # requires UIS_API_KEY environment variable
  # OR
  mode: "bdds"   # bulk download, no key required (~100 MB, cached locally)
```

Register for a UIS API key at [apiportal.uis.unesco.org](https://apiportal.uis.unesco.org/).

### Sequential execution

```bash
# Step 1 — Download from WDI, WGI, UIS (10–20 minutes)
python src/01_download_sources.py

# Step 2 — Build 12-country panel (2–5 minutes)
python src/02_clean_merge_panel.py

# Step 3 — Trajectory labels and splits (<1 minute)
python src/03_create_masks_and_labels.py

# Step 4 — Descriptive statistics (<1 minute)
python src/04_descriptive_statistics.py

# Tasks A–E (2–10 minutes each)
python src/05_task_A_prediction.py
python src/06_task_B_trajectory_classification.py
python src/07_task_C_fairness_optimisation.py
python src/08_task_D_mnar_imputation.py
python src/09_task_E_causal_ml.py
```

### Jupyter notebook

All scripts include a notebook-safe `__file__` guard and can be pasted or
`%run` directly from a notebook opened at the project root.

```python
# At the top of your notebook cell — add src/ to path
import sys
from pathlib import Path
_SRC = Path.cwd() / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
```

---

## Country Selection

Countries were selected via a two-stage procedure. Stage 1 computed a
coverage-maximising ranking across 217 World Bank non-aggregate economies
using the 17-indicator availability matrix (full matrix in
`outputs/coverage_analytics/`). Stage 2 applied three theory-driven
override criteria: regional diversity, outcome variation, and trajectory
class completeness.

Full justification for all substitutions is in
`metadata/country_selection_rationale.md`.

---

## Data Sources

| Source | Description | Access |
|---|---|---|
| World Bank WDI | World Development Indicators | [data.worldbank.org](https://data.worldbank.org/) — open API |
| World Bank WGI | Worldwide Governance Indicators (source=75) | [info.worldbank.org/governance/wgi](https://info.worldbank.org/governance/wgi/) — open API |
| UNESCO UIS | SDG 4 and OPRI indicators, February 2026 release | [uis.unesco.org](https://uis.unesco.org/) — API key or bulk download |

All source data is publicly available. No redistribution of raw World Bank
or UNESCO data is included in this repository. The processed panel CSV files
are derived works released under CC BY 4.0 (see Licence).

---

## Citation

If you use this benchmark, please cite:

```bibtex
@inproceedings{hashempour2026ukci,
  title     = {A Harmonised Open Panel Benchmark for Causal,
               Fairness-Aware, and Explainable Machine Learning
               in Educational Equity and {SDG} 4 Monitoring},
  author    = {Hashempour, Sona and Ratcliffe, Elizabeth and Coopman, Karen},
  booktitle = {Proceedings of the UK Workshop on Computational
               Intelligence (UKCI 2026)},
  year      = {2026},
}
```

A `CITATION.cff` file is also provided for GitHub citation integration.

---

## Licence

The code in this repository is released under the **MIT Licence**.
The processed dataset files (`data/processed/`) are released under
**Creative Commons Attribution 4.0 International (CC BY 4.0)**.

See [LICENSE](LICENSE) for full terms.