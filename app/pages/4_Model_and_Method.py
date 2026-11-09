"""Model & Method: how the estimates are made, and their limits."""

import streamlit as st
from components import data, layout

layout.page("Model and method", "How the estimates are produced, how well they work, and what they can't tell you.")
e = data.england()

st.subheader("Approach")
st.markdown(
    """
1. **Train** a classifier on the **English Housing Survey**, where surveyors inspect homes and record damp.
2. Use only **features recorded in both datasets**: dwelling type, age, wall and roof insulation, glazing, heating,
   energy efficiency (SAP), floor area and region.
3. **Calibrate** the probabilities, so that averages over an area are meaningful.
4. **Score** every social home in the **EPC register** and **aggregate** to neighbourhoods and councils.
5. **Validate**: predicted regional rates are compared against published survey figures (7% of social homes had
   damp in 2024).
"""
)

st.subheader("Model performance")
st.info(
    "Results appear here after training (Week 2): a baseline vs logistic regression vs LightGBM, with "
    "precision-recall and calibration curves.",
    icon="⏳",
)

st.subheader("Data")
st.markdown(
    f"""
| Dataset | Role |
|---|---|
| English Housing Survey: housing stock data (UK Data Service, End User Licence) | Training labels and features |
| Energy Performance Certificates, England | {e["n_homes"]:,} social homes to score |
| ONS postcode lookup (May 2026) and LSOA 2021 boundaries | Linking homes to neighbourhoods |
| English Indices of Deprivation 2025 | Deprivation context |
"""
)

st.subheader("Limitations")
st.markdown(
    f"""
- **A risk indicator, not a diagnosis.** Estimates reflect *building characteristics only*. Occupancy, heating
  habits, overcrowding, leaks and repair condition are major drivers of damp that EPCs don't record.
- **Coverage.** Homes without an EPC, or whose latest certificate doesn't record tenure, are missing.
  {e["pct_cert_before_2015"]:.0f}% of certificates pre-date 2015 and may not reflect later improvements.
- **Harmonisation.** EPC and survey categories don't match exactly (e.g. age bands are aligned approximately).
- **Area-level only.** No address-level results are published. Areas with fewer than {e["min_homes_shown"]}
  homes are hidden.
"""
)

layout.footer()
