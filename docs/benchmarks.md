# Published damp benchmarks (English Housing Survey)

These are official, published EHS figures, used for **EDA context**, to check that the training data reproduces known rates, and to **validate** model predictions. Collected 2026-11-09.

## How the EHS defines damp
- **Surveyor-observed**, not self-reported: a dwelling has a damp problem if the surveyor records penetrating damp, rising damp, or serious condensation/mould **significant enough to count in the HHSRS hazard assessment**. Minor damp isn't recorded.
- Three types: **serious condensation/mould** (most common), **penetrating damp**, **rising damp**. A dwelling can have more than one.
- Self-reported damp is **far higher** (30% of households report damp, condensation or mould, compared with 5% observed by surveyors). Our target is the surveyor-observed measure, so don't mix the two.

## 1. Prevalence by tenure

| Group | 2023 (dwellings) | 2024 (dwellings) |
|---|---|---|
| **All dwellings** | 5% (1.3m) | 5% (1.4m) |
| Owner occupied | 4% | 4% |
| Private rented | 9% | 10% |
| **Social rented** | – | **7%** (up from 5% in 2022, a significant rise) |
| Local authority | 9% | 8% |
| Housing association | 5% | 6% |

**Damp type, 2024 (social rented):** serious condensation 5%, penetrating 2%, rising 1%.

> **Modelling implication:** expect roughly **5–9% positive cases** among social homes in the training data (class imbalance), so use PR-AUC, not accuracy. Predicted mean risk across EPC social homes should land near **7%**. LA-owned stock should come out somewhat higher than housing association stock.

## 2. Prevalence by dwelling characteristics (2023, all tenures unless stated)

These are bivariate comparisons (no controls), but they show which EPC features should matter:

| Characteristic | Damp rate | Comparison | EPC feature |
|---|---|---|---|
| Energy rating E–G | **12%** | D: 7%, A–C: 3% | `epc_band`, `sap_score` |
| – Local authority, E–G | **29%** | LA A–C: 8% | |
| – Housing association, E–G | 16% | HA A–C: 4% | |
| Uninsulated walls | 8% | Insulated: 3% | `wall_insulation` |
| – Local authority, uninsulated | 15% | LA insulated: 7% | |
| Loft insulation < 200mm | 7% | ≥ 200mm: 3% | `roof_insulation` |
| – Local authority, < 200mm | 14% | LA ≥ 200mm: 5% | |
| Not fully double glazed | 10% | Fully double glazed: 5% | `glazing` |
| Inadequate ventilation | ~60% | Adequate: 5% (only ~1% of stock) | `mechanical_ventilation` (weak proxy) |
| Internal disrepair | 19% | – | not in EPC |
| Overcrowded household | 14% | Not overcrowded: 4% | not in EPC (occupancy) |
| Household can't keep warm | 12% | Can: 4% | not in EPC (behaviour/income) |

**Not published in these reports:** damp by dwelling **age**, **type** (flat/terrace etc.) or **region**. Those will come from our own weighted EHS analysis.

> **Modelling implications**
> - Energy efficiency and insulation are strong signals and are available in both datasets. 👍
> - **Disrepair, overcrowding and under-heating** are major drivers that the EPC doesn't record. The model can only capture *building-related* risk, so name this clearly in the limitations: "the model estimates risk from building characteristics only; occupancy, heating behaviour and repair condition aren't captured."
> - The EHS reports are bivariate and don't claim causation. Our SHAP analysis adds value by showing each feature's effect while accounting for the others.

## 3. Sources
- [EHS 2024 to 2025: headline findings on housing quality and energy efficiency, Chapter 1](https://www.gov.uk/government/statistics/chapters-for-english-housing-survey-2024-to-2025-headline-findings-on-housing-quality-and-energy-efficiency/chapter-1-housing-quality) (Annex Tables 1.9, 1.10, 1.11)
- [EHS 2024 to 2025 headline report (PDF)](https://assets.publishing.service.gov.uk/media/697a0f35005d288bf850deb2/2024-25_EHS_Headline_Report_on_Housing_Quality_and_Energy_Efficiency.pdf)
- [EHS 2023 to 2024: drivers and impacts of housing quality](https://www.gov.uk/government/statistics/english-housing-survey-2023-to-2024-drivers-and-impacts-of-housing-quality/english-housing-survey-2023-to-2024-drivers-and-impacts-of-housing-quality)
- [EHS live tables (DA5101–DA5103: damp and mould time series)](https://www.gov.uk/government/collections/english-housing-survey-live-tables)

Contains public sector information licensed under the Open Government Licence v3.0.
