# Finding damp before it finds tenants: estimating damp and mould risk in England's social homes

*Draft. Sections marked ⏳ are completed after modelling.*

## Summary

- ⏳ **Headline finding**: e.g. "The riskiest 10% of social homes contain X% of predicted damp cases."
- ⏳ **Main drivers**: which building characteristics matter most once the others are accounted for.
- **Building conditions linked to damp aren't evenly spread.** 22% of social homes with an EPC have uninsulated walls, and poor energy ratings (E–G) are concentrated in rural, off-gas areas: 19% in the Forest of Dean against 4% nationally.
- ⏳ **Recommendation**: how a landlord could use area-level risk to prioritise proactive inspections.

## 1. The problem

In 2020, two-year-old Awaab Ishak died from prolonged exposure to mould in his family's social rented home in Rochdale. **Awaab's Law** now requires social landlords in England to investigate and fix serious damp and mould hazards within fixed deadlines.

Most landlords still find damp **reactively**, when a tenant complains. Yet damp is common: surveyors found a damp problem in **7% of social rented homes in 2024**, up from 5% in 2022, and in 8% of council-owned homes. With around four million social homes, inspecting every one isn't realistic.

**Question:** *Can publicly available data identify which social homes, and which neighbourhoods, are most at risk of damp, so inspections can be targeted before tenants are harmed?*

## 2. Data

Two datasets each hold half of the answer:

| | English Housing Survey (EHS) | Energy Performance Certificates (EPC) |
|---|---|---|
| What it is | National survey; trained surveyors inspect a sample of homes | Register of energy assessments, required when a home is let or sold |
| Damp recorded? | ✅ Yes: penetrating, rising damp and serious condensation | ❌ No |
| Coverage | A few thousand homes per year | **2.86 million** social homes in England |
| Location | Region only | Postcode → neighbourhood |

The approach is to **learn the relationship between building characteristics and damp from the survey, then apply it to every home in the register**.

Supporting data: the ONS postcode lookup (to place each home in a neighbourhood), LSOA 2021 boundaries, and the English Indices of Deprivation 2025.

### Preparing the EPC data
- Took the **latest certificate for each home** across 30.5 million certificates (2008–2026), then kept homes whose latest certificate records social renting. Homes that have since been sold therefore drop out.
- Matched **99.98%** of homes to a neighbourhood via their postcode.
- Converted free-text fields into consistent categories, e.g. *"Solid brick, as built, no insulation (assumed)"* → wall type **solid**, insulation **none**. The rules are covered by 61 unit tests.
- Chose **MSOA neighbourhoods** (about 8,000 residents) for maps. Only 28 of 6,856 have fewer than 10 social homes, compared with 16% of the smaller LSOAs.

## 3. Method

⏳ *To complete in Week 2.*

1. **Harmonise** features recorded in both datasets: dwelling type, age band, wall and roof insulation, glazing, heating, energy efficiency (SAP), floor area, region.
2. **Train** models on surveyed homes, from a simple baseline to logistic regression to LightGBM, using stratified cross-validation and survey weights for evaluation.
3. **Evaluate** with PR-AUC rather than accuracy, because damp affects only ~7% of homes, so a model predicting "no damp" for everyone would be 93% accurate and useless.
4. **Calibrate** probabilities so area averages are meaningful, and **explain** predictions with SHAP values.
5. **Score** all 2.86 million homes, aggregate to neighbourhoods and councils, and **validate** against published survey rates.

## 4. Findings

### 4.1 Where are the building conditions linked to damp most common?
Published survey figures (EHS 2023) show damp is about **four times as common** in homes rated E–G as in homes rated A–C (12% vs 3%), and more than twice as common with uninsulated walls (8% vs 3%).

In the EPC data:
- **22%** of social homes have uninsulated walls; **4%** are rated E–G.
- Poor ratings cluster in **rural councils** (Forest of Dean 19%, Melton 17%, Cotswold 16% rated E–G), largely homes off the gas grid.
- Uninsulated walls are **somewhat more common in deprived neighbourhoods**: 20% in the most deprived tenth against 16% in the least deprived, peaking in the second and third most deprived tenths.

### 4.2 ⏳ What drives damp risk?
*SHAP importance and effect plots.*

### 4.3 ⏳ Where is predicted risk highest?
*Maps and the councils and neighbourhoods with the highest estimated risk, plus how concentrated predicted cases are.*

### 4.4 ⏳ How well does the model work?
*Comparison table, calibration, and agreement with published regional rates.*

## 5. What landlords could do with this

⏳ *For example: use neighbourhood risk to sequence proactive stock condition surveys; prioritise retrofit (wall insulation, heating upgrades) where risk and deprivation overlap; refresh certificates more than ten years old (10% pre-date 2015).*

## 6. Limitations

- **A risk indicator, not a diagnosis.** The model sees *building characteristics only*. Disrepair, overcrowding, ventilation habits and households' ability to heat their homes are strong drivers of damp that EPCs don't record.
- **Coverage.** Homes without an EPC, or whose latest certificate doesn't record tenure (22% of certificates), are missing, roughly 70% of the social stock is covered.
- **Stale certificates.** A home is described by its latest certificate, which may pre-date improvements.
- **Imperfect matching.** EPC and survey categories don't align exactly; for example, EPC age bands are assigned to survey bands by their midpoint year.
- **Ethics.** Results are published for areas only, never addresses, and areas with fewer than 10 homes are hidden.

## 7. What I'd do next

- Add **landlord repairs and complaints data** to capture disrepair and occupancy, the drivers EPCs miss.
- Add **local climate and exposure** (rainfall, wind-driven rain) for penetrating damp.
- **Validate over time**: train on earlier survey years and test on later ones.

---
*Data: English Housing Survey (UK Data Service, End User Licence); EPC register (MHCLG); ONS Open Geography; English Indices of Deprivation 2025. Contains public sector information licensed under the Open Government Licence v3.0.*
