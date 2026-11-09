"""Area Explorer: pick a council, see its neighbourhoods (MSOAs) and housing mix."""

import plotly.express as px
import streamlit as st
from components import data, layout
from components.theme import ACCENT, GREY, INDICATORS, label

layout.page("Area explorer", "Pick a council to see how building conditions vary between its neighbourhoods.")

la = data.la_summary().sort_values("lad24nm")
msoa = data.msoa_summary()
e = data.england()

c1, c2 = st.columns([2, 1])
names = la.lad24nm.tolist()
default = names.index("Manchester") if "Manchester" in names else 0
council = c1.selectbox("Council", names, index=default)
with c2:
    metric = layout.indicator_picker("explorer_indicator")
row = la[la.lad24nm == council].iloc[0]
lad = row.lad24cd

left, right = st.columns([3, 2], gap="large")
with left:
    areas = msoa[msoa.lad24cd == lad]
    st.plotly_chart(
        layout.choropleth(areas, data.msoa_geojson(lad), "msoa21cd", metric, "msoa21nm", height=520),
        width="stretch",
        config={"scrollZoom": True},
    )
    hidden = int(areas[metric].isna().sum())
    st.caption(
        f"{len(areas)} neighbourhoods (MSOAs) · {int(row.n_homes):,} social homes"
        + (f" · {hidden} with too few homes to show" if hidden else "")
    )

with right:
    st.subheader(f"{council} vs England")
    comp = []
    for col, (name, unit, _) in INDICATORS.items():
        if unit == "%":
            comp += [
                {"Indicator": name, "Area": council, "Value": row[col]},
                {"Indicator": name, "Area": "England", "Value": e[col]},
            ]
    fig = px.bar(
        comp,
        y="Indicator",
        x="Value",
        color="Area",
        barmode="group",
        orientation="h",
        color_discrete_map={council: ACCENT, "England": GREY},
        height=420,
    )
    fig.update_layout(
        yaxis={"title": "", "autorange": "reversed"},
        xaxis_title="% of social homes",
        legend={"title": "", "orientation": "h", "y": -0.15},
    )
    st.plotly_chart(fig, width="stretch")

st.subheader("Housing mix")
mix = data.feature_mix()
mix = mix[mix.lad24cd.isin([lad, "ENGLAND"])]
feature_names = {
    "dwelling_type": "Dwelling type",
    "age_band": "Age band",
    "wall_insulation": "Wall insulation",
    "heating": "Heating",
    "epc_band": "EPC band",
}
tabs = st.tabs(list(feature_names.values()))
for tab, feat in zip(tabs, feature_names, strict=True):
    with tab:
        d = mix[mix.feature == feat].pivot_table(index="category", columns="lad24cd", values="pct").fillna(0)
        d = d.rename(columns={lad: council, "ENGLAND": "England"})
        d["Difference (pts)"] = d[council] - d["England"]
        st.dataframe(
            d.sort_values(council, ascending=False).round(1),
            width="stretch",
            column_config={
                council: st.column_config.NumberColumn(f"{council} (%)"),
                "England": st.column_config.NumberColumn("England (%)"),
            },
        )

st.caption(f"Map colour: {label(metric)}. {INDICATORS[metric][2]}")
layout.footer()
