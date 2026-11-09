"""Overview page (entry point). Run with:  .venv\\Scripts\\streamlit.exe run app/Overview.py"""

import streamlit as st
from components import data, layout
from components.theme import INDICATORS, label

layout.page(
    "Damp risk in England's social homes",
    "2.9 million social homes have an Energy Performance Certificate. Where are the building conditions linked to "
    "damp most common?",
)

e = data.england()
la = data.la_summary()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Social homes", f"{e['n_homes'] / 1e6:.2f}m", help="Latest EPC per home, social rented, England")
k2.metric("Rated EPC E–G", f"{e['pct_epc_efg']:.1f}%", help=INDICATORS["pct_epc_efg"][2])
k3.metric("Uninsulated walls", f"{e['pct_wall_uninsulated']:.1f}%", help=INDICATORS["pct_wall_uninsulated"][2])
k4.metric("Neighbourhoods", f"{e['n_msoas']:,}", help="Middle-layer Super Output Areas (MSOAs), ~8,000 residents each")

left, right = st.columns([3, 2], gap="large")
with left:
    metric = layout.indicator_picker("overview_indicator")
    st.caption(INDICATORS[metric][2])
    st.plotly_chart(
        layout.choropleth(la, data.la_geojson(), "lad24cd", metric, "lad24nm"),
        width="stretch",
        config={"scrollZoom": True},
    )

with right:
    st.subheader("Key findings so far")
    worst = la[la.n_homes >= 500].nlargest(1, "pct_epc_efg").iloc[0]
    st.markdown(
        f"""
1. **{e["pct_wall_uninsulated"]:.0f}% of social homes have uninsulated walls**, one of the clearest
   building-level links to damp in published survey data.
2. **Poor energy ratings are concentrated in rural areas** (off the gas grid), e.g. {worst.lad24nm}:
   {worst.pct_epc_efg:.0f}% rated E–G vs {e["pct_epc_efg"]:.0f}% nationally.
3. **Most homes are fairly efficient**: median SAP {e["median_sap"]:.0f} (band C). Risk is concentrated in a
   minority of homes and places, which is what makes targeted inspection worthwhile.

*Damp risk findings will replace these once the model is trained.*
"""
    )

    st.subheader("Highest-scoring councils")
    min_homes = 500
    top = la[la.n_homes >= min_homes].nlargest(10, metric)[["lad24nm", "n_homes", metric]]
    unit_max = float(top[metric].max())
    st.dataframe(
        top,
        hide_index=True,
        width="stretch",
        column_config={
            "lad24nm": "Council",
            "n_homes": st.column_config.NumberColumn("Social homes", format="localized"),
            metric: st.column_config.ProgressColumn(label(metric), format="%.1f", min_value=0, max_value=unit_max),
        },
    )
    st.caption(f"Councils with at least {min_homes:,} social homes with an EPC.")

layout.footer()
