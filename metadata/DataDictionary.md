# Data Dictionary
## UKCI 2026 Benchmark Panel — `panel_12countries_2015_2024.csv`

This document describes every variable in the processed panel file.
The panel contains 120 rows (12 countries × 10 years, 2015–2024)
and 21 columns (4 identifiers + 17 indicators).

For the raw indicator specification used by the pipeline, see
`configs/indicators.yml`. For missingness patterns and coverage
by income tier, see `outputs/tables/table1_completeness.csv`.

---

## Identifier columns

| Column | Type | Description |
|---|---|---|
| `iso3c` | string | ISO 3166-1 alpha-3 country code (e.g. `ESP`, `BGD`) |
| `country` | string | World Bank display name (e.g. `Spain`, `Bangladesh`) |
| `income_group` | string | World Bank income classification as of 2024: `High income`, `Upper middle income`, `Lower middle income`, `Low income` |
| `year` | integer | Reference year (2015–2024) |

---

## Indicator columns

### Primary outcome  (role: Y)

#### `sec_completion`
- **Label**: Lower-secondary completion rate
- **Unit**: Percent (0–100)
- **Source**: UNESCO UIS `TRTP.1` (SDG BDDS, February 2026). WDI `SE.SEC.CMPT.LO.ZS` fallback.
- **Definition**: Percentage of a cohort aged 3–5 years above the intended age for the last grade of lower-secondary who have completed that grade.
- **Clip**: [0, 100]
- **Missing**: 5 rows — BDI 2021–2024 structural gap; URY 2024 trailing lag.
- **Notes**: BDI values 2015–2019 are near 100%; the 2020 value (5.8%) reflects a structural break in the UIS series. Primary outcome variable Y_it.

---

### Policy treatment variable  (role: W)

#### `edu_spend_gdp`
- **Label**: Government education expenditure (% GDP)
- **Unit**: Percent of GDP
- **Source**: World Bank WDI `SE.XPD.TOTL.GD.ZS`
- **Definition**: General government expenditure on education as a percentage of GDP, including current, capital, and transfers.
- **Clip**: [0, 100]
- **Missing**: 12 rows — BDI (all years), BFA/CRI/ESP/IDN/KGZ (trailing years).
- **Notes**: Treatment variable W_it in Task E. Used contemporaneously (not lagged).

---

### Protected attributes  (role: A)

#### `gpi_sec`
- **Label**: Gender Parity Index — secondary net enrolment
- **Unit**: Ratio Female/Male. Values > 1 indicate female-majority enrolment.
- **Source**: UNESCO UIS `NERT.2.GPIA` (OPRI BDDS). WDI `SE.ENR.SECO.FM.ZS` fallback.
- **Definition**: Ratio of female to male net enrolment rate at secondary level.
- **Clip**: [0.7, 1.3]
- **Missing**: 11 rows — BDI structural; GEO/IDN/THA/URY boundary gaps.
- **Notes**: Primary protected attribute A_it in Task C. Training-set median = 1.014.

#### `gpi_tert`
- **Label**: Gender Parity Index — tertiary gross enrolment
- **Unit**: Ratio Female/Male
- **Source**: UNESCO UIS `GER.2.GPIA` (OPRI BDDS). WDI `SE.ENR.TERT.FM.ZS` fallback.
- **Definition**: Ratio of female to male gross enrolment rate at tertiary level.
- **Clip**: [0.7, 1.3]
- **Missing**: 4 rows — BDI structural; URY 2024 trailing lag.

---

### Covariates  (role: X)

#### `gini`
- **Label**: Gini index
- **Unit**: Index 0–100
- **Source**: World Bank WDI `SI.POV.GINI`
- **Definition**: Measures deviation of income distribution from perfect equality.
- **Clip**: [0, 100]
- **Missing**: 38 rows (31.7%) — BDI/BFA/BGD/ESP/RWA/UZB. **Income-gradient MNAR**: coverage 100% (upper-middle) → 23% (low income). See §4.1 and Task D.

#### `inc_share_low20`
- **Label**: Income share held by lowest 20%
- **Unit**: Percent of total income
- **Source**: World Bank WDI `SI.DST.FRST.20`
- **Definition**: Percentage of income accruing to the poorest 20% of population.
- **Clip**: [0, 100]
- **Missing**: 38 rows (31.7%) — same countries as `gini`; co-reported in household surveys.

#### `poverty_215`
- **Label**: Poverty headcount ratio at $2.15/day (2017 PPP)
- **Unit**: Percent of population
- **Source**: World Bank WDI `SI.POV.DDAY`
- **Definition**: Population living on less than $2.15/day at 2017 international prices.
- **Clip**: [0, 100]
- **Missing**: 38 rows (31.7%) — same as `gini`.

#### `sec_enrol_gross`
- **Label**: Secondary net enrolment rate
- **Unit**: Percent (0–100)
- **Source**: UNESCO UIS `NERT.2.CP` (OPRI BDDS). WDI `SE.SEC.ENRR` (gross rate) fallback.
- **Definition**: Secondary enrolment of official secondary age / total population of that age.
- **Clip**: [0, 100]
- **Missing**: 5 rows — BDI structural; URY 2024.
- **Notes**: UIS primary = net rate; WDI fallback = gross rate.

#### `tert_enrol_gross`
- **Label**: Tertiary gross enrolment rate
- **Unit**: Percent (0–100; can exceed 100 if enrolment spans outside official tertiary age)
- **Source**: World Bank WDI `SE.TER.ENRR`
- **Definition**: Total tertiary enrolment / total population of official tertiary age.
- **Clip**: [0, 100]
- **Missing**: 13 rows — BDI structural; CRI/GEO/IDN/URY partial.
- **Notes**: UZB shows +48.5 pp over 2015–2024, anchoring the Access Expander trajectory class.

#### `adult_literacy`
- **Label**: Adult literacy rate (15+)
- **Unit**: Percent (0–100)
- **Source**: UNESCO UIS `LR.AG15T99` (SDG BDDS). WDI `SE.ADT.LITR.ZS` fallback.
- **Definition**: Population aged 15+ who can read and write a short simple statement.
- **Clip**: [0, 100]
- **Missing**: 49 rows (40.8%) — structural UIS survey gap (surveys conducted every 5–10 years, not annually). MAR mechanism, not MNAR.

#### `youth_literacy`
- **Label**: Youth literacy rate (15–24)
- **Unit**: Percent (0–100)
- **Source**: UNESCO UIS `LR.AG15T24` (SDG BDDS). WDI `SE.ADT.1524.LT.ZS` fallback.
- **Definition**: Population aged 15–24 who can read and write a short simple statement.
- **Clip**: [0, 100]
- **Missing**: 44 rows (36.7%) — same survey-cycle gap as `adult_literacy`.

#### `gdp_pc_ppp`
- **Label**: GDP per capita (PPP, constant 2017 USD)
- **Unit**: USD (constant 2017 international PPP)
- **Source**: World Bank WDI `NY.GDP.PCAP.PP.KD`
- **Definition**: GDP divided by midyear population in constant 2017 PPP terms.
- **Clip**: [0, ∞)
- **Missing**: 0 rows — complete.
- **Notes**: Log-transformed internally in Task E causal model. Used as regressor in GDP-anchored Gini imputation (Task D).

#### `work_age_share`
- **Label**: Working-age population share (15–64)
- **Unit**: Percent of total population
- **Source**: World Bank WDI `SP.POP.1564.TO.ZS`
- **Definition**: Percentage of total population aged 15–64.
- **Clip**: [0, 100]
- **Missing**: 0 rows — complete.

#### `gov_effect`
- **Label**: Government effectiveness (WGI)
- **Unit**: z-score (approx. −2.5 to +2.5; higher = more effective)
- **Source**: World Bank WGI `GE.EST` (source=75)
- **Definition**: Perceptions of public service quality, civil service independence, policy quality, and credibility of government commitment.
- **Clip**: [−4, 4]
- **Missing**: 12 rows — WGI 2024 release lag (all 12 countries missing one year).

#### `voice_account`
- **Label**: Voice and accountability (WGI)
- **Unit**: z-score (approx. −2.5 to +2.5)
- **Source**: World Bank WGI `VA.EST` (source=75)
- **Definition**: Perceptions of citizens' participation in government selection, freedom of expression, association, and media.
- **Clip**: [−4, 4]
- **Missing**: 12 rows — same WGI 2024 lag.

#### `ctrl_corrup`
- **Label**: Control of corruption (WGI)
- **Unit**: z-score (approx. −2.5 to +2.5)
- **Source**: World Bank WGI `CC.EST` (source=75)
- **Definition**: Perceptions of public power exercised for private gain and state capture by elites.
- **Clip**: [−4, 4]
- **Missing**: 12 rows — same WGI 2024 lag.

---

### Context variable  (role: C)

#### `pop_total`
- **Label**: Total population
- **Unit**: Persons
- **Source**: World Bank WDI `SP.POP.TOTL`
- **Definition**: De facto population counting all residents regardless of legal status.
- **Clip**: [0, ∞)
- **Missing**: 0 rows — complete.
- **Notes**: Excluded from model feature sets (role=C). Included for population-weighted analysis.

---

## Preprocessing transformations

All applied in `src/02_clean_merge_panel.py`.
Recorded in `data/processed/interpolation_mask_2015_2024.csv`.

| Transformation | Rule | Indicators affected |
|---|---|---|
| Domain clipping | Values outside [clip_min, clip_max] replaced at boundary | All 17 |
| Linear interpolation | Gaps ≤ 2 consecutive years filled within country | All with short gaps |
| Long-gap preservation | Gaps > 2 years left as NaN | Gini (low-income), literacy |
| Structural MNAR imputation | Income-group mean + GDP regression for countries with all Gini values missing | `gini`, `inc_share_low20`, `poverty_215` in `panel_12countries_imputed_2015_2024.csv` only |

The interpolation mask `M_it = 1` means the value was **empirically
observed** in the source data. `M_it = 0` means interpolated or
still missing. Use the mask to distinguish observed from imputed
values in downstream analyses.

---

## Related files

| File | Description |
|---|---|
| `data/processed/panel_12countries_2015_2024.csv` | Main panel (this schema) |
| `data/processed/panel_12countries_imputed_2015_2024.csv` | Panel with structural MNAR gaps filled (Task D) |
| `data/processed/interpolation_mask_2015_2024.csv` | Binary M_it mask |
| `data/processed/trajectory_labels.csv` | Country trajectory classes with rationale |
| `configs/indicators.yml` | Machine-readable indicator spec (source codes, clips, roles) |
| `outputs/tables/table1_completeness.csv` | Coverage % per indicator pre/post-interpolation |
| `outputs/coverage_analytics/coverage_matrix_2015_2024.csv` | Coverage matrix for all 217 World Bank economies |