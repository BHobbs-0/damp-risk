"""Risk Drivers: what makes a home more likely to be damp."""

import pandas as pd
import plotly.express as px
import streamlit as st
from components import layout
from components.theme import ACCENT, GREY

layout.page(
    "What drives damp risk?",
    "Published survey data already shows damp is far more common in poorly insulated, inefficient homes.",
)

st.subheader("What the English Housing Survey reports (2023, all tenures)")
bench = pd.DataFrame(
    [
        ("Energy rating", "A–C", 3),
        ("Energy rating", "D", 7),
        ("Energy rating", "E–G", 12),
        ("Walls", "Insulated", 3),
        ("Walls", "Uninsulated", 8),
        ("Loft insulation", "200mm or more", 3),
        ("Loft insulation", "Under 200mm", 7),
        ("Glazing", "Fully double glazed", 5),
        ("Glazing", "Not fully double glazed", 10),
    ],
    columns=["Characteristic", "Group", "Damp rate (%)"],
)
bench["worse"] = bench.groupby("Characteristic")["Damp rate (%)"].transform(lambda s: s == s.max())
fig = px.bar(
    bench,
    x="Damp rate (%)",
    y="Group",
    color="worse",
    facet_row="Characteristic",
    orientation="h",
    color_discrete_map={True: ACCENT, False: GREY},
    height=460,
    text="Damp rate (%)",
)
fig.update_yaxes(matches=None, title="")
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
fig.update_layout(showlegend=False)
fig.update_traces(texttemplate="%{text}%", textposition="outside")
st.plotly_chart(fig, width="stretch")
st.caption(
    "Source: English Housing Survey 2023 to 2024, *Drivers and impacts of housing quality*. Damp is as recorded by "
    "trained surveyors. These are simple comparisons that don't control for other factors."
)

st.subheader("Coming after modelling")
c1, c2, c3 = st.columns(3)
c1.markdown(
    "**Feature importance**  \nWhich building characteristics matter most *after accounting for the "
    "others* (SHAP values from the trained model)."
)
c2.markdown(
    "**Effect of each feature**  \nHow predicted risk changes across age bands, wall types, energy "
    "ratings and heating systems."
)
c3.markdown(
    "**What-if calculator**  \nDescribe a hypothetical home and see its estimated damp risk, with an "
    "explanation of what pushes it up or down."
)

layout.footer()
