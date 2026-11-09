"""Risk & Deprivation: do the most deprived areas have the worst housing conditions?"""

import plotly.express as px
import streamlit as st
from components import data, layout
from components.theme import ACCENT, INDICATORS, label

lsoa = data.lsoa_summary().dropna(subset=["imd_decile"])
layout.page(
    "Building conditions and deprivation",
    "How do building conditions in social homes vary with neighbourhood deprivation?",
)

metric = layout.indicator_picker("deprivation_indicator", default="pct_wall_uninsulated")
by_decile = lsoa.groupby("imd_decile").apply(
    lambda g: (g[metric] * g.n_homes).sum() / g.n_homes.sum(), include_groups=False
)
most, least = by_decile.loc[1], by_decile.loc[10]
unit = INDICATORS[metric][1]
st.markdown(
    f"#### {INDICATORS[metric][0]}: **{most:.1f}{unit}** in the most deprived 10% of neighbourhoods vs "
    f"**{least:.1f}{unit}** in the least deprived 10%"
)

left, right = st.columns([3, 2], gap="large")
with left:
    fig = px.box(
        lsoa,
        x="imd_decile",
        y=metric,
        points=False,
        color_discrete_sequence=[ACCENT],
        height=420,
        labels={"imd_decile": "IMD 2025 decile (1 = most deprived)", metric: label(metric)},
    )
    fig.add_scatter(
        x=by_decile.index, y=by_decile.values, mode="lines+markers", name="Weighted average", line={"color": "#2B6CB0"}
    )
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, width="stretch")
    st.caption(
        f"Each box summarises small areas (LSOAs) with at least 10 social homes ({len(lsoa):,} LSOAs). "
        "The line is the average across all social homes in each decile."
    )
with right:
    st.subheader("Why this matters")
    st.markdown(
        "Damp harms health, especially for children and older people, and deprived households are less able to "
        "heat homes adequately, which makes condensation worse. If poor building conditions also cluster in "
        "deprived areas, the risks compound.\n\n"
        "**After modelling**, this page will show estimated damp risk by decile, and how concentrated predicted "
        "damp cases are in the most deprived areas."
    )

layout.footer()
