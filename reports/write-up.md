# Finding damp before it finds tenants: estimating damp and mould risk in England's social homes

[📊 Live dashboard](https://bhobbs-0.github.io/damp-risk/) · [Code](https://github.com/BHobbs-0/damp-risk)

## Summary

- An estimated **203,000 social homes in England (7.1%) have a damp problem**, consistent with the English Housing Survey's published 6.9%.
- **Building age and energy rating drive the risk.** Homes built before 1919 have 1.75× the odds of damp of a typical social home; homes rated EPC E–G 2.2×; homes built after 1990 less than half (0.45×). Estimated risk runs from **12.5% for pre-1919 homes to 2.7% for post-1990 homes**.
- **Risk is concentrated in specific homes more than specific places.** The riskiest 10% of homes hold **23% of expected cases**, but the riskiest 10% of neighbourhoods hold only 11%.
- **Recommendation:** landlords can get much more from proactive inspections by targeting homes by their *characteristics* (pre-1919, poorly rated, uninsulated) than by area. Inspecting the riskiest tenth of homes would find over twice as many damp cases as inspecting at random.

## 1. The problem

In 2020, two-year-old Awaab Ishak died from prolonged exposure to mould in his family's social rented home in Rochdale. **Awaab's Law** now requires social landlords in England to investigate and fix serious damp and mould hazards within fixed deadlines.

Most landlords still find damp **reactively**, when a tenant complains. Yet damp is common: surveyors found a damp problem in **7% of social rented homes in 2024**, up from 5% in 2022. With around four million social homes, inspecting every one isn't realistic.

**Question:** *can open data identify which social homes, and which neighbourhoods, are most at risk of damp, so inspections can be targeted before tenants are harmed?*

## 2. Data

| Dataset | What it gives | Role |
|---|---|---|
| English Housing Survey published damp tables (DA5101, DA5102) | Damp rates for social homes by building age, dwelling type, floor area, region and deprivation, recorded by trained surveyors | What the model learns from, and how it's tested |
| Energy Performance Certificates (EPC) | 2.86m social homes, each with age, type, floor area and energy rating, but **no damp information** | The homes the model scores |
| ONS postcode lookup and boundaries; Indices of Deprivation 2025 | Neighbourhood, council and deprivation for each home | Mapping and analysis |

**A change of plan.** The original design was to train a classifier on the English Housing Survey's home-level microdata. The UK Data Service declined my access request, so I rebuilt the approach around the survey's **published, open tables**. Everything here is reproducible from open data.

### Preparing the EPC data
- Took the **latest certificate for each home** across 30.5 million certificates (2008–2026), then kept homes whose latest certificate records social renting, so homes that have since been sold drop out.
- Placed **99.98%** of homes in a neighbourhood via their postcode.
- Turned free-text fields into survey-style categories, e.g. *"Solid brick, as built, no insulation (assumed)"* becomes wall type **solid**, insulation **none** (61 unit tests).

## 3. Method

### Fitting a model to published rates
The survey publishes damp rates for categories of homes (pre-1919 homes: 13%; post-1990: 3%; and so on), but not for individual homes. The obvious shortcut is to multiply risk ratios together, but that **double-counts**: old homes are also more often poorly rated, so their extra risk would be counted twice.

Instead I fitted an additive **logistic model**,

> logit P(damp) = intercept + effect(age) + effect(type) + effect(floor area) + effect(energy rating)

choosing the coefficients so that, applied to the **real mix of 2.86 million EPC homes**, it reproduces every published category rate at once. Because the EPC data shows how characteristics occur together, overlapping effects are separated properly. On synthetic data with a known answer, this recovers the true home-level risk, while multiplying ratios overstates risk for old, poorly rated homes (both are covered by unit tests).

The rates are the average of the 2023 and 2024 survey years (2022 was partly modelled during COVID). The energy-rating rates for social homes come from the survey's 2023-24 *Drivers and impacts* report.

### Validation
With no labelled homes, I tested the model in two honest ways:
1. **Leave one breakdown out:** refit without, say, building age, then predict the age rates it never saw.
2. **Breakdowns never used in fitting:** region and deprivation decile. Each published rate is itself an estimate from a few hundred surveyed homes, so I also calculated a **noise floor**: the error you'd expect even from a perfect model.

## 4. Findings

### 4.1 The model reproduces the survey and generalises to what it wasn't shown

| Check | Model error (points) | Baseline (points) |
|---|---|---|
| Fit to the 19 published rates | **0.2** | 1.7 |
| Leave out building age | **1.8** | 2.6 |
| Leave out dwelling type | **0.45** | 1.08 |
| Leave out floor area | **0.87** | 1.04 |
| Leave out energy rating | **1.4** | 2.1 |
| Deprivation decile (never seen) | 1.01 | 0.98 (noise floor 1.03) |
| Region (never seen) | 1.6 | 1.6 (noise floor about 1.0) |

*Baseline: predicting the national rate for every category.* Every leave-one-out check beats the baseline. On deprivation the model sits **at the noise floor**: the published figures can't distinguish it from a perfect model. On region it doesn't do better than the baseline, and the error is above the noise floor (section 4.4).

### 4.2 Old and inefficient homes carry the risk
Estimated risk falls steadily with building age: **12.5%** for pre-1919 homes, 9.1% for 1945–64, 5.9% for 1965–80 and **2.7%** after 1990. Net of the other characteristics, a pre-1919 home has **1.75×** the odds of damp of a typical home, and an E–G energy rating **2.2×**. Insulation is one likely mechanism: **74% of pre-1919 social homes have uninsulated walls**, against 22% overall.

### 4.3 Where risk is highest
Council averages range from **5.5%** (Milton Keynes, with newer stock) to **8.9%** (Barking and Dagenham). The highest-risk councils mix inner London (Barking and Dagenham, Hammersmith and Fulham, Kensington and Chelsea) with rural, off-gas areas (Forest of Dean, Melton) and port cities (Southampton). Barking and Dagenham's position reflects its stock: **34% of its social homes were built 1919–44**, more than twice the national share, consistent with the large interwar Becontree estate.

For planning, **numbers matter as much as rates**. Birmingham's risk is close to average, but its size means about **6,600 expected cases**, more than any other council, followed by Leeds and Manchester (about 3,700 each).

Deprivation shows a gentle gradient: **7.3%** in the most deprived tenth of neighbourhoods against **6.0%** in the least deprived.

### 4.4 What building data can't explain
The model doesn't reproduce the survey's **regional** differences. London's published rate is 10.0% against 7.6% predicted, and the East of England's is 3.1% against 6.7%. Those gaps are bigger than sampling noise alone explains, so they likely reflect factors the EPC doesn't record: overcrowding, ventilation, and the way homes are heated and repaired. This is the clearest limit of a buildings-only model.

### 4.5 Targeting: homes beat places
- The riskiest **10% of homes** (estimated risk 11.4% or more) hold **23% of expected cases**: 2.3× more efficient than inspecting at random.
- The riskiest **10% of neighbourhoods** hold only **11% of cases** (on 8% of homes).

Within any neighbourhood, homes vary a lot, so area-level targeting dilutes the signal.

## 5. What landlords could do with this

1. **Prioritise proactive inspections by stock characteristics:** pre-1919 and interwar homes, E–G ratings, uninsulated walls. Landlords already hold this information in their asset records.
2. **Use the area view for planning, not targeting:** expected case counts show where inspection and repair capacity is needed (e.g. the large urban councils).
3. **Fold it into retrofit plans:** wall insulation and energy-efficiency upgrades target the same homes that carry the highest damp risk.
4. **Refresh old certificates:** 10% of social homes' latest EPC pre-dates 2015 and may not reflect later improvements.

## 6. Limitations

- **A risk indicator, not a diagnosis.** The model sees building characteristics only. Overcrowding, ventilation habits, heating affordability, leaks and repair condition are strong drivers of damp that EPCs don't record (section 4.4).
- **Calibrated to averages.** The model reproduces published rates but assumes effects add on the log-odds scale with no interactions. Survey and EPC categories are matched approximately (e.g. floor-area definitions, age-band boundaries).
- **Energy-rating rates are derived** from report figures for council and housing association homes, combined by their approximate share of the stock.
- **Coverage.** Homes without an EPC, or whose latest certificate doesn't record tenure, are missing (roughly 70% of social homes are covered).
- **Ethics.** Results are published for areas only, never addresses; areas with fewer than 10 homes are hidden.

## 7. What I'd do next

- **Home-level validation:** if access to the survey microdata, or a landlord's stock condition and repairs data, becomes available, train and test against individual homes. The evaluation toolkit for that is already built.
- **Add non-building drivers:** overcrowding (Census 2021), climate and wind-driven rain, and landlord repair performance, to explain the regional gap.
- **Track change over time** as new survey years and certificates are published.

---
*Data: English Housing Survey live tables DA5101/DA5102 (MHCLG); EPC register (MHCLG); ONS Open Geography; English Indices of Deprivation 2025. Contains public sector information licensed under the Open Government Licence v3.0. Contains OS data © Crown copyright and database right.*
