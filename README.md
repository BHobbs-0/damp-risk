# Damp Risk Atlas: Predicting damp & mould risk in England's social housing

> **Status:** 🚧 In progress (Week 1 of 4). Findings below are placeholders until the analysis is complete.

**Key finding (placeholder):** _e.g. "Pre-1919 solid-wall flats with an EPC band of E or worse are X times more likely to have damp; the 10% highest-risk areas contain Y% of predicted cases."_

[📊 Live dashboard](#) · [📄 Full write-up](reports/) · [🧪 Modelling notebook](notebooks/)

---

## Why this matters

Damp and mould in social housing is a serious health risk. In 2020, two-year-old Awaab Ishak died from prolonged exposure to mould in his family's social rented home. **Awaab's Law** now requires social landlords in England to investigate and fix serious hazards within fixed deadlines.

Landlords mostly react to complaints. This project asks:

> **Which social homes in England are most at risk of damp and mould, and why?**

The aim is to support **proactive** inspection, so landlords can focus surveys and retrofit spending where risk is highest before tenants are harmed.

## Approach

```
 English Housing Survey (EHS)         EPC Register
 ~thousands of surveyed homes          millions of homes
 ✅ damp recorded by surveyors         ❌ no damp data
 ❌ region-level location only         ✅ postcode / LSOA location
            │                                   │
            └──── harmonise shared features ────┘
                 (age, built form, walls,
                  heating, SAP score, floor area…)
            │                                   │
      train + calibrate model  ───────────▶  score social rented homes
                                                │
                                   aggregate to LSOA / local authority
                                                │
                                 + Indices of Deprivation 2025
                                                │
                                   maps · drivers · dashboard
```

1. **Harmonise** features that exist in both the EHS and the EPC register.
2. **Train** a classifier on EHS surveyed homes (target: damp or mould present). Logistic regression is the baseline, LightGBM the main model, and survey weights are used in evaluation.
3. **Calibrate** probabilities so that area-level averages are meaningful.
4. **Explain** risk drivers with SHAP.
5. **Score** every social rented home in the EPC register (latest certificate per property), then **aggregate** to areas.
6. **Analyse** the results against deprivation, and **validate** them against weighted EHS regional prevalence.

## Data sources

| Dataset | Publisher | Use | Licence / access |
|---|---|---|---|
| English Housing Survey – Housing Stock Data (EUL) | MHCLG via UK Data Service | Training labels & features | End User Licence (free registration). **Not redistributed.** |
| Domestic Energy Performance Certificates | MHCLG / DESNZ | Homes to score | Open data (see publisher terms) |
| English Indices of Deprivation 2025 | MHCLG | Area context | Open Government Licence |
| LSOA 2021 boundaries | ONS Open Geography Portal | Mapping | Open Government Licence |
| Postcode → OA/LSOA/MSOA lookup (May 2026) | ONS Open Geography Portal | Linking EPC homes to areas | Open Government Licence |

Raw data is **not included** in this repository. See [Getting the data](#getting-the-data).

## Results

_To be completed._

| Model | PR-AUC | ROC-AUC | Brier score |
|---|---|---|---|
| Baseline (prevalence) | – | 0.50 | – |
| Logistic regression | – | – | – |
| LightGBM (calibrated) | – | – | – |

<!-- Add: SHAP summary plot, calibration curve, headline map -->

## Getting started

### Prerequisites
- Python 3.11+ (developed on 3.13)
- ~10 GB free disk space for the raw EPC data

### Setup (Windows / PowerShell)
```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Getting the data
1. **EHS:** register at the UK Data Service and download the *English Housing Survey: Housing Stock Data* (End User Licence) for the chosen survey years. Place the files in `data/raw/ehs/`.
2. **EPC:** download domestic certificates for England (start with one region) into `data/raw/epc/`.
3. **IMD 2025:** download the LSOA-level file into `data/raw/imd/`.
4. **Boundaries:** download LSOA 2021 boundaries (generalised) into `data/raw/boundaries/`.
5. **Postcode lookup:** download the ONS *Postcode to OA (2021) to LSOA to MSOA to LAD* best-fit lookup zip into `data/raw/postcodes/`.

Full links, file names and profiling notes are in [docs/data-sources.md](docs/data-sources.md).

### Run the pipeline
```powershell
python -m src.ingest.epc         # EPC zip -> data/interim/epc/*.parquet (~4 min)
python -m src.ingest.postcodes   # postcode lookup -> data/interim/postcode_lookup.parquet
python -m src.features.epc       # social homes + harmonised features -> data/processed/epc_social.parquet (~6 min)
python -m src.geo.boundaries     # LSOA -> MSOA / LA boundaries -> data/processed/geo/
# (to be added) src.ingest.ehs -> src.models -> src.score
streamlit run app/app.py
```

## Repository structure

```
damp-risk/
├── data/              # raw/ interim/ processed/ (git-ignored)
├── notebooks/         # 01_eda · 02_modelling · 03_spatial
├── src/
│   ├── ingest/        # EHS + EPC loaders
│   ├── features/      # EHS ↔ EPC harmonisation
│   ├── models/        # train, calibrate, explain
│   └── score/         # apply to EPC, aggregate to areas
├── app/               # Streamlit dashboard
├── reports/           # write-up + figures
├── docs/              # design notes
└── tests/
```

## Limitations & ethics

- **Risk indicator, not a diagnosis.** Predictions estimate likelihood from property characteristics only. They do not capture occupancy, ventilation habits, leaks or repair history.
- **Feature harmonisation loss.** Only features available in both the EHS and EPC data are used, and some are recorded differently in each.
- **EPC coverage and age.** Not every home has a certificate, and some are years old. Coverage is reported per area.
- **Area-level outputs only.** No address-level risk scores are published.
- **Survey data licensing.** EHS microdata is used under the UK Data Service End User Licence and is not shared here.

## Roadmap

- [ ] **Week 1:** Data acquisition, cleaning, EHS ↔ EPC feature mapping
  - [x] EPC: 2.86m social homes cleaned, harmonised features, unit-tested parsers
  - [x] Geography: postcode → LSOA/MSOA (99.98% matched), MSOA & LA boundaries
  - [ ] EHS: load, confirm damp variables, map to EPC features
- [ ] **Week 2:** EDA, baseline & LightGBM models, calibration, SHAP
- [ ] **Week 3:** Score EPC social homes, aggregate, deprivation analysis, validation
- [ ] **Week 4:** Streamlit dashboard, write-up, tests, polish

## Author

**Ben Hobbs:** Data Analyst · [LinkedIn](#) · [GitHub](https://github.com/BHobbs-0)
