"""Page setup, sidebar and shared building blocks."""

import math

import plotly.express as px
import streamlit as st

from components import data
from components.theme import INDICATORS, NO_DATA, RISK_SCALE, label

GITHUB = "https://github.com/BHobbs-0/damp-risk"


def page(title: str, takeaway: str) -> None:
    """Every page starts with its title and a one-sentence plain-English takeaway."""
    st.set_page_config(page_title=f"{title} · Damp Risk Atlas", page_icon="🏠", layout="wide")
    with st.sidebar:
        st.markdown("### Damp Risk Atlas")
        st.caption(
            "Estimating damp and mould risk in England's social homes from building characteristics. "
            "A portfolio project combining the English Housing Survey and the EPC register."
        )
        st.markdown(f"[Code on GitHub]({GITHUB})")
    st.title(title)
    st.markdown(f"**{takeaway}**")
    preview_banner()


def preview_banner() -> None:
    st.info(
        "**Preview.** Damp risk estimates are added once the model is trained. For now, areas are described by "
        "**building indicators** from Energy Performance Certificates that published housing survey data links to "
        "damp (e.g. poor energy ratings and uninsulated walls).",
        icon="🚧",
    )


def footer() -> None:
    e = data.england()
    st.divider()
    st.caption(
        f"Social rented homes in England with an EPC (latest certificate per home, up to {e['latest_certificate']}). "
        f"Areas with fewer than {e['min_homes_shown']} homes are not shown. "
        "Contains public sector information licensed under the Open Government Licence v3.0. "
        "Contains OS data © Crown copyright and database right. Royal Mail data © Royal Mail copyright and database "
        "right. National Statistics data © Crown copyright and database right."
    )


def indicator_picker(key: str, default: str | None = None) -> str:
    cols = list(INDICATORS)
    return st.selectbox(
        "Indicator",
        cols,
        index=cols.index(default) if default else 0,
        format_func=lambda c: INDICATORS[c][0],
        key=key,
        help="How each area is coloured on the map.",
    )


def zoom_for(bbox: tuple[float, float, float, float]) -> tuple[dict, float]:
    """Centre and an approximate MapLibre zoom that fits a bounding box."""
    min_x, min_y, max_x, max_y = bbox
    span = max(max_x - min_x, (max_y - min_y) * 1.6, 1e-3)
    return {"lon": (min_x + max_x) / 2, "lat": (min_y + max_y) / 2}, max(5.0, min(12.0, math.log2(360 / span) - 0.1))


def choropleth(df, geojson, id_col: str, value: str, hover_name: str, height: int = 560):
    centre, zoom = zoom_for(data.bounds(geojson))
    # Cap the colour scale at the 98th percentile so one extreme area (e.g. a council
    # with very few homes) doesn't wash out the variation everywhere else.
    vmax = float(df[value].quantile(0.98)) if df[value].notna().any() else None
    vmin = float(df[value].min()) if df[value].notna().any() else None
    fig = px.choropleth_map(
        df,
        geojson=geojson,
        locations=id_col,
        featureidkey=f"properties.{id_col}",
        color=value,
        color_continuous_scale=RISK_SCALE,
        range_color=(vmin, vmax) if vmax is not None else None,
        hover_name=hover_name,
        hover_data={id_col: False, "n_homes": ":,", value: ":.1f"},
        labels={value: label(value), "n_homes": "Social homes"},
        map_style="carto-positron",
        center=centre,
        zoom=zoom,
        opacity=0.85,
        height=height,
    )
    fig.update_traces(marker_line_width=0.3, marker_line_color="white")
    fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0}, coloraxis_colorbar={"title": "", "thickness": 12})
    return fig


__all__ = ["page", "footer", "indicator_picker", "choropleth", "NO_DATA"]
