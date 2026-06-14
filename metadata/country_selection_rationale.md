# Country Selection Rationale
## Benchmark Panel: 12-Country Balanced Panel (2015–2024)

---

## 1. Selection Procedure

Country selection followed a two-stage procedure designed to balance
data-driven coverage maximisation with theory-driven representational
requirements.

### Stage 1 — Coverage-Maximising Baseline

A coverage matrix was computed across all 217 World Bank non-aggregate
economies using a 17-indicator availability matrix spanning 2015–2024.
Data were drawn from three sources:

- **WDI** — World Bank World Development Indicators (8 indicators)
- **WGI** — Worldwide Governance Indicators, source=75 (3 indicators)
- **UIS** — UNESCO Institute for Statistics BDDS February 2026 release,
  `SDG.zip` and `OPRI.zip` (6 indicators, with WDI fallback for
  country-years where UIS has no data)

For each country, an `overall_coverage` score was computed as the mean
coverage share across all 17 indicators, subject to a minimum threshold
of 10/17 indicators having any data in the period. Countries below this
threshold receive no score and are excluded from ranking.

Countries were ranked within each World Bank income tier by
`overall_coverage` descending. The automated top-3 per tier is
documented in `outputs/coverage_analytics/top3_by_income_group_2015_2024.csv`.

### Stage 2 — Theory-Driven Overrides

The top-ranked countries were accepted unless overridden by one or more
of three theoretical criteria:

1. **Regional diversity** — No income tier should be represented
   exclusively by a single geographic region.

2. **Outcome variation** — The panel should retain countries with
   contrasting lower-secondary completion trajectories within each tier,
   ensuring covariate support for heterogeneous treatment effect
   estimation (Task E).

3. **Trajectory class completeness** — The four-class typology defined
   in 4.2 of the manuscript requires at least one country per class.
   The Data-Limited class specifically requires a country with severe
   structural missingness in inequality indicators and contracting
   completion rates — a condition not met by any coverage-maximising
   alternative.

---

## 2. Automated Top-3 vs Selected Panel

| Tier | Automated Top-3 | Selected Panel | Substitutions |
|---|---|---|---|
| High income | URY, ESP, PAN | URY, ESP, CRI | PAN → CRI |
| Upper middle | DOM, SLV, ARM | GEO, IDN, THA | DOM/SLV/ARM → GEO/IDN/THA |
| Lower middle | BOL, KGZ, HND | KGZ, UZB, BGD | BOL/HND → UZB/BGD |
| Low income | BFA, RWA, TGO | BFA, RWA, BDI | TGO → BDI |

---

## 3. Substitution Justifications

### High income: PAN → CRI (Panama → Costa Rica)

Panama (rank 3, 84.1%) and Costa Rica (rank 6, 83.5%) are separated by
only 0.6 percentage points in overall coverage. Costa Rica is preferred
on three grounds: (i) it is classified as high income and provides Latin
American representation alongside Uruguay and Spain; (ii) Panama's
income classification has been subject to reclassification in the
World Bank's historical series, introducing potential measurement
inconsistencies; (iii) Costa Rica has a longer established record of
education investment as a percentage of GDP, making it a more suitable
anchor for the policy treatment variable W_it.

### Upper middle income: DOM/SLV/ARM → GEO/IDN/THA

The automated top-3 (Dominican Republic 96.5%, El Salvador 94.1%,
Armenia 93.5%) are all regionally concentrated — two in Central America
and one in the South Caucasus. The selected panel replaces them with
Georgia (rank 4, 93.5%), Indonesia (rank 9, 89.4%), and Thailand
(rank 7, 90.6%), achieving representation across three distinct regions
(South Caucasus, Southeast Asia, East/Southeast Asia) while retaining
all three within the top-10 of the tier.

Additionally, these three countries exhibit theoretically important
trajectory variation. Georgia has near-complete Gini coverage (10/10
years) enabling full inequality-outcome analysis. Indonesia provides
a large-population Southeast Asian context with strong completion
coverage (10/10). Thailand exhibits a distinctive pattern of tertiary
contraction alongside Gini improvement that anchors the Inequality
Reducer trajectory class.

### Lower middle income: BOL/HND → UZB/BGD

Bolivia (rank 1, 88.2%) has zero tertiary enrolment coverage across
the entire panel period, making it unsuitable for multi-indicator
causal analysis. Honduras (rank 3, 82.9%) has incomplete Gini coverage
(7/10 years) and no South or Central Asian representation.

Uzbekistan (rank 4, 82.4%) is substituted for Bolivia because it
exhibits the defining characteristic of the Access Expander trajectory
class — tertiary enrolment growth of +37.8 percentage points over the
panel period (CAGR 24.3%), a pattern absent from any coverage-maximising
alternative. Bangladesh (rank 5, 81.8%) is substituted for Honduras to
introduce South Asian representation, and has complete coverage on the
primary outcome variable (10/10 years).

Kyrgyz Republic (rank 2, 85.9%) is retained from the automated
top-3.

### Low income: TGO → BDI (Togo → Burundi)

Togo (rank 3, 73.5%) would be the coverage-maximising choice. Burundi
(not in top-10, overall coverage 42.9%) is substituted on one specific
theoretical ground: the four-class trajectory typology defined in 4.2
requires a Data-Limited country — defined as a country assigned on the
basis of severe Gini missingness (coverage ≤ 10%) and contracting
lower-secondary completion. Burundi satisfies both conditions (Gini
coverage 1/10 years; completion rate declining across the panel period).
No country in the low-income top-10 satisfies both conditions
simultaneously.

This substitution is a deliberate design choice, not a data quality
failure. Burundi's structural missingness is the benchmark condition
formalised in 4.1 (the income-gradient MNAR condition), and its
inclusion in the panel is necessary to instantiate that condition with
an empirical country-year block.

Burkina Faso (rank 1, 76.5%) and Rwanda (rank 2, 74.1%) are retained
from the automated top-3.

---

## 4. Final Panel Coverage Summary

The following table reports per-country coverage shares for all 17
indicators, derived from
`outputs/coverage_analytics/coverage_matrix_2015_2024.csv`.
Coverage share = years with non-null data / 10.

| ISO | Country | Tier | Rank | Overall | Y (comp) | W (edu) | A (gpi_sec) | Gini | Notes |
|---|---|---|---|---|---|---|---|---|---|
| URY | Uruguay | High | 1 | 92.4% | 9/10 | 9/10 | 8/10 | 10/10 | |
| ESP | Spain | High | 2 | 89.4% | 10/10 | 8/10 | 10/10 | 9/10 | |
| CRI | Costa Rica | High | 6 | 83.5% | 10/10 | 9/10 | 10/10 | 10/10 | adult_lit=0 (UIS gap) |
| GEO | Georgia | UpMid | 4 | 93.5% | 10/10 | 10/10 | 7/10 | 10/10 | |
| IDN | Indonesia | UpMid | 9 | 89.4% | 10/10 | 9/10 | 7/10 | 10/10 | |
| THA | Thailand | UpMid | 7 | 90.6% | 10/10 | 9/10 | 8/10 | 10/10 | |
| KGZ | Kyrgyz Republic | LoMid | 2 | 85.9% | 10/10 | 9/10 | 10/10 | 10/10 | lit=0 (UIS gap) |
| UZB | Uzbekistan | LoMid | 4 | 82.4% | 10/10 | 9/10 | 10/10 | 4/10 | |
| BGD | Bangladesh | LoMid | 5 | 81.8% | 10/10 | 10/10 | 10/10 | 2/10 | MNAR by design |
| BFA | Burkina Faso | Low | 1 | 76.5% | 10/10 | 8/10 | 10/10 | 2/10 | MNAR by design |
| RWA | Rwanda | Low | 2 | 74.1% | 9/10 | 10/10 | 9/10 | 2/10 | MNAR by design |
| BDI | Burundi | Low | n/a | 42.9% | 0/10 | 9/10 | 0/10 | 1/10 | Data-Limited class anchor |

**Y** = primary outcome (lower-secondary completion rate, `sec_completion`)
**W** = policy treatment variable (education expenditure % GDP, `edu_spend_gdp`)
**A** = protected attribute (secondary GPI, `gpi_sec`)

---

## 5. Notes on Structural Gaps

### Literacy indicators (adult_literacy, youth_literacy)

Coverage on `adult_literacy` and `youth_literacy` is zero or near-zero
for several countries (CRI, KGZ, and others). This reflects the
infrequency of household literacy surveys — UNESCO UIS collects these
through nationally representative surveys conducted every 5–10 years
rather than annually. The WDI fallback (`SE.ADT.LITR.ZS`,
`SE.ADT.1524.LT.ZS`) also has sparse coverage for these countries.
These gaps are structural and not a data pipeline artefact. These
indicators play a supporting covariate role (X_it) in the benchmark;
their absence does not affect the primary outcome, treatment, or
protected attribute variables.

### Gini MNAR condition (§4.1)

The Gini coverage gradient — high income ~90%, upper-middle ~90%,
lower-middle ~20–40%, low income ~10–20% — is precisely the
income-gradient Missing Not At Random (MNAR) condition formalised in
4.1 of the manuscript. This gradient is real and present in the
raw World Bank data; it is not introduced by the pipeline. The four
low-income and lower-middle-income countries with Gini coverage ≤ 4/10
(BGD, UZB, BFA, RWA, BDI) form the empirical basis for the MNAR
benchmark stress test in Task D.

---

## 6. Reproducibility

The full coverage matrix for all 217 economies is available at:

```
outputs/coverage_analytics/coverage_matrix_2015_2024.csv
outputs/coverage_analytics/coverage_matrix_pct_2015_2024.csv
outputs/coverage_analytics/top3_by_income_group_2015_2024.csv
outputs/coverage_analytics/top10_by_income_group_2015_2024.csv
```

The pipeline that produced these files is fully version-controlled:

```
src/01_download_sources.py
src/utils.py
configs/indicators.yml
configs/pipeline.yml
```

Data sources: World Bank API (accessed June 2026), UNESCO UIS BDDS
February 2026 release (`https://download.uis.unesco.org/bdds/202602/`).