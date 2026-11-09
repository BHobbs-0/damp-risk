# Design & Layout

This covers three outputs: the **dashboard**, the **written report**, and the **visual style** they share.

> ## Current design (2026-11-09): Observable Framework, soft bento
> After trying several Streamlit styles, the dashboard was rebuilt as a custom **Observable Framework** site (`dashboard/`). Sections 2–4 below describe the earlier Streamlit plan; the **page list, audience and data rules still apply**, but layout and styling follow this box.
>
> - **One screen per page** (fits 1440×900 without scrolling): icon rail on the left; header with title, an **indicator switch** (pills), council search and a status pill; a **bento grid** of rounded frosted cards below.
> - **Overview layout:** tall **hero card** with the council **hex cartogram** (hover/click a council for a floating callout with value, points vs England and rank); a wide **construction-age** bar card; a **watch list** (top 5 councils); a **deprivation** card. One indicator switch drives every card.
> - **Look:** page `#E4E5E9`; cards white-to-translucent with 24px radius; Plus Jakarta Sans; big numbers; small pills. **Orange** `#F07B2B` marks the highest bar and **periwinkle** `#8E9BF5` the lowest; other bars are white with a grey top edge; values are labelled; a dashed line shows the England average. Text colours meet WCAG AA (`#1B1D21`, muted `#5E636B`, orange text `#B4530F`).
> - **Build:** pages are Markdown with the HTML layout plus a JS cell; D3 components in `dashboard/src/components/`; styles in `dashboard/src/style.css`. **Python data loaders** (`dashboard/src/data/*.json.py`) read `data/processed/dashboard/` and output small JSON, so all analysis stays in Python. Static build in `dashboard/dist/` → GitHub Pages.
> - **Rejected along the way** (for the record): default Streamlit; editorial/civic/dark mock-ups; a restyled Streamlit "hybrid"; a Streamlit dark theme. The problem was Streamlit's stacked layout and default-looking charts, not the colours.

---

## 1. Audience & goals

| Audience | What they need | Where they get it |
|---|---|---|
| **Recruiter / hiring manager** (primary) | Grasp the project in 30 seconds, then see technical depth | README headline → dashboard Overview → Model page |
| **Housing professional** (realistic user) | "Where should we inspect first, and what kind of homes?" | Area Explorer + Risk Drivers |
| **Technical reviewer** | Is the method sound? | Model & Method page + notebooks |

**Design rule:** every page opens with a one-sentence takeaway in plain English, *then* the charts.

---

## 2. Dashboard structure (original Streamlit plan: superseded, see box above; page list still applies)

```
app/
├── app.py                     # Home / Overview
├── pages/
│   ├── 1_Area_Explorer.py
│   ├── 2_Risk_Drivers.py
│   ├── 3_Risk_and_Deprivation.py
│   └── 4_Model_and_Method.py
├── components/                # shared chart + layout helpers
└── data/                      # small aggregated files (committed)
```

Global sidebar on every page: project title, a short "What is this?" blurb, filters (region, property type) where relevant, and links to GitHub and the write-up.

### Page 1: Overview (landing)
```
┌───────────────────────────────────────────────────────────────┐
│  Damp Risk Atlas                                              │
│  "Estimated damp & mould risk across England's social homes"  │
├──────────┬──────────┬──────────┬──────────────────────────────┤
│ Homes    │ Avg est. │ % homes  │ EPC coverage                 │
│ scored   │ risk     │ high-risk│ of social stock              │
├──────────┴──────────┴──────────┼──────────────────────────────┤
│                                │  Key findings                │
│   Choropleth map               │  1. …                        │
│   (local authority level)      │  2. …                        │
│   colour = mean est. risk      │  3. …                        │
│                                ├──────────────────────────────┤
│                                │  Top 10 highest-risk LAs     │
│                                │  (table + mini bar)          │
└────────────────────────────────┴──────────────────────────────┘
```

### Page 2: Area Explorer
- Select a **local authority**, then see an **MSOA-level** map for that LA only (keeps geometry small). MSOA is the default small-area view.
- ~~LSOA toggle~~ **Dropped (2026-11-09):** LSOA map shapes would add ~31 MB to the repo for an optional view, and 16% of LSOAs would be hidden anyway. LSOA data is still used on the Deprivation page.
- Next to it: risk distribution (histogram) for the LA vs England.
- Property mix table: age band, built form and EPC band in this LA vs the national average.
- Areas where EPC coverage is below the threshold are **greyed out** with a note.

### Page 3: Risk Drivers (the showcase page)
- **Global SHAP** bar chart: which features matter most.
- **Effect plots** for the top drivers (e.g. risk by construction age band, by SAP score).
- **"What-if" property calculator:** pick age band, built form, wall type, heating and SAP band to get an estimated probability, with a SHAP waterfall chart explaining it. Hypothetical homes only, so no addresses are involved.

### Page 4: Risk & Deprivation
- Scatter: LSOA mean risk vs IMD 2025 score (sampled or hex-binned for readability).
- Box/strip plot: risk by IMD decile.
- Concentration curve: "the most deprived X% of areas hold Y% of predicted damp cases."

### Page 5: Model & Method
- Metrics table: baseline vs logistic regression vs LightGBM (PR-AUC, ROC-AUC, Brier score).
- Precision-recall curve and **calibration curve**.
- Validation: predicted vs weighted EHS regional prevalence (dot plot).
- Feature harmonisation table (EHS variable ↔ EPC field).
- Limitations & ethics (same text as the README).

---

## 3. App data contract

The dashboard reads **only small, aggregated files**, so it can be deployed free on Streamlit Community Cloud without licensed microdata or individual addresses.

| File | Grain | Key columns |
|---|---|---|
| `la_summary.parquet` | Local authority | `lad_code, lad_name, region, n_homes, mean_risk, pct_high_risk, coverage` |
| `msoa_summary.parquet` | MSOA (default small area) | `msoa_code, msoa_name, lad_code, n_homes, mean_risk, pct_high_risk, imd_score_popw, pct_lsoas_most_deprived_decile, coverage` |
| `lsoa_summary.parquet` | LSOA (detail toggle, n ≥ 10 only) | `lsoa_code, msoa_code, lad_code, n_homes, mean_risk, imd_score, imd_decile, coverage` |
| `la_boundaries.geojson` | LA, simplified | `lad_code, geometry` (dissolved from LSOAs) |
| `msoa_boundaries/<lad_code>.geojson` | MSOA, simplified, split per LA | `msoa_code, geometry` (dissolved from LSOAs) |
| `lsoa_boundaries/<lad_code>.geojson` | LSOA, simplified, split per LA | `lsoa_code, geometry` |
| `shap_global.parquet` | Feature | `feature, mean_abs_shap` |
| `metrics.json` | Model | metrics and curve points |
| `model.joblib` | – | Calibrated model for the What-if calculator |

Suppress any area with fewer than ~10 scored homes (small numbers can be unreliable and disclosive).

**Geography notes**
- **Area hierarchy:** LSOA → MSOA → LA, all taken from the ONS postcode lookup (MSOA) and the IMD 2025 file (LA 2024 codes). MSOA and LA boundaries are built by **dissolving the LSOA boundaries**, so no extra boundary downloads are needed and the shapes always match the data.
- **Deprivation at MSOA level:** IMD is published for LSOAs only, so derive (a) a population-weighted mean IMD score (weights from IMD File 7's population columns) and (b) the % of the MSOA's LSOAs in the most deprived national decile. Label these clearly as derived.
- **Risk & Deprivation page:** the statistical analysis stays at **LSOA level** (where IMD is defined), using LSOAs with ≥10 homes. Maps default to MSOA.
- **Social homes per area (checked 2026-11-09):** MSOA has a median of 320 (10th percentile 93) and 28 of 6,856 areas below 10. LSOA has a median of 55 and 5,139 of 32,744 below 10.

---

## 4. Visual style

> **Updated 2026-11-09: "hybrid" design adopted.** Inspired by a soft bento-style reference, adapted for a serious public-health topic:
> - **Surfaces:** soft grey page `#E9EAED`, white cards with 20px radius and a 1px `#DCDEE2` border, no heavy shadows. Font: Plus Jakarta Sans.
> - **Colour:** one accent, orange: `#D9661F` for graphics (3.6:1 on white), `#A9430B` for text (5.5:1). Neutral bars `#8A9099` (3.3:1). Text `#16181C`, secondary `#4B5058` (8:1). Meets WCAG AA.
> - **Headlines state the finding** (e.g. "One in five social homes has uninsulated walls…"), followed by a short standfirst.
> - **Maps are flat, not 3D.** The council map defaults to a **hex cartogram** (one equal hexagon per council) so large rural councils don't dominate visually, with a real-map toggle.
> - **Charts:** neutral grey with one orange highlight that marks the point; values labelled on bars.
> - **Navigation:** top bar (Overview · Areas · Drivers · Deprivation · Method). A status pill ("Building indicators · model coming") replaces the big preview banner.
>
> The notes below are the original style guide; where they conflict, the update above wins.

**Colour**
- Risk uses a **single-hue sequential** scale (light → dark), never red/green. It should be colourblind-safe, e.g. `#fff5eb → #7f2704` (Oranges) or Viridis.
- Deprivation uses a separate sequential hue (e.g. purples) so the two never get confused.
- Grey `#bdbdbd` = insufficient data.
- Model comparison: baseline in grey, logistic regression in blue, LightGBM in the accent colour.

**Typography & layout**
- Streamlit `layout="wide"`. Use `st.metric` for the KPI cards and `st.columns` for grids.
- Titles state the finding, not the variable: *"Older solid-wall homes carry the highest risk"*, not *"Risk by wall type"*.
- Always label units and say "estimated" when describing risk.

**Charts:** Plotly throughout (interactive, consistent theme). Set one shared template in `app/components/theme.py`.

---

## 5. Written report (`reports/write-up.md`, ~1,500 words)

1. **Summary**: 3 bullet findings + 1 recommendation
2. **The problem**: Awaab's Law, why proactive targeting matters
3. **Data**: EHS + EPC, and why they need combining
4. **Method**: harmonisation → model → calibration → scoring (one diagram)
5. **Findings**: 3–4 sections, each with one chart and a plain-English title
6. **What landlords could do with this**
7. **Limitations & ethics**
8. **What I'd do next**: e.g. use landlord repairs data, add weather/exposure data, temporal validation

---

## 6. Notebooks

| Notebook | Purpose |
|---|---|
| `01_data_audit.ipynb` | Load EHS + EPC, inspect variables, document harmonisation decisions |
| `02_eda.ipynb` | Weighted damp prevalence by feature, class balance, feature drift EHS vs EPC |
| `03_modelling.ipynb` | Baseline → LR → LightGBM, CV, calibration, SHAP |
| `04_scoring_spatial.ipynb` | Apply to EPC, aggregate, IMD join, maps, validation |

Keep notebooks for exploration and storytelling. Move reusable logic into `src/` as soon as it works.
