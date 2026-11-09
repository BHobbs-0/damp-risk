"""Shared colours, labels and Plotly defaults (see docs/design.md, section 4)."""

import plotly.graph_objects as go
import plotly.io as pio

ACCENT = "#D85A30"
GREY = "#9E9E9E"
NO_DATA = "#BDBDBD"
RISK_SCALE = "Oranges"  # single-hue sequential: colourblind-safe, never red/green
DEPRIVATION_SCALE = "Purples"

# Indicator column -> (label, unit, help text)
INDICATORS = {
    "pct_epc_efg": (
        "Rated EPC E–G",
        "%",
        "Homes rated E–G are about 4× as likely to have damp as A–C (EHS 2023: 12% vs 3%).",
    ),
    "pct_wall_uninsulated": (
        "Uninsulated walls",
        "%",
        "Homes with uninsulated walls have damp at more than twice the rate of insulated ones (EHS 2023: 8% vs 3%).",
    ),
    "pct_not_full_glazing": (
        "Not fully double glazed",
        "%",
        "Homes not fully double glazed: 10% damp vs 5% (EHS 2023).",
    ),
    "pct_pre1919": ("Built before 1919", "%", "Older, often solid-walled homes."),
    "pct_electric_heating": ("Electric heating", "%", "Storage or direct electric heating: often costlier to run."),
    "pct_flats": ("Flats", "%", "Share of homes that are flats or maisonettes."),
    "median_sap": ("Median SAP score", "", "Energy efficiency score (higher is better; band C starts at 69)."),
    "pct_cert_before_2015": (
        "Certificate before 2015",
        "%",
        "Data freshness: older certificates may miss later retrofit work.",
    ),
}
DEFAULT_INDICATOR = "pct_epc_efg"

pio.templates["damp"] = go.layout.Template(
    layout=go.Layout(
        font={"family": "Inter, Segoe UI, sans-serif", "size": 13},
        colorway=[ACCENT, "#2B6CB0", GREY, "#6B46C1"],
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        title={"font": {"size": 15}},
    )
)
pio.templates.default = "plotly_white+damp"


def label(col: str) -> str:
    name, unit, _ = INDICATORS[col]
    return f"{name} ({unit})" if unit else name
