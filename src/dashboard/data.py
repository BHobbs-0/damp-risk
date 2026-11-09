"""Data for the Observable Framework dashboard (dashboard/).

Framework's data loaders (dashboard/src/data/*.py) call these functions and
print JSON to stdout. Inputs are the aggregated, non-disclosive files built by
`python -m src.score.aggregate`, so nothing here touches raw or licensed data.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGG = PROJECT_ROOT / "data" / "processed" / "dashboard"  # output of src.score.aggregate

INDICATORS = ["pct_wall_uninsulated", "pct_epc_efg", "pct_not_full_glazing", "pct_electric_heating"]
AGE_ORDER = ["pre1919", "1919-1944", "1945-1964", "1965-1980", "1981-1990", "post1990"]


def _records(df: pd.DataFrame) -> list[dict]:
    """JSON-safe records (NaN -> null, numbers rounded)."""
    return json.loads(df.round(2).to_json(orient="records"))


def overview() -> dict:
    """England totals, councils, and national breakdowns by construction age and IMD decile."""
    england = json.loads((AGG / "england_summary.json").read_text(encoding="utf-8"))
    la = pd.read_parquet(AGG / "la_summary.parquet")[
        ["lad24cd", "lad24nm", "region_name", "n_homes", "median_sap", *INDICATORS]
    ]
    ages = pd.read_parquet(AGG / "by_age_band.parquet").set_index("age_band").loc[AGE_ORDER].reset_index()

    lsoa = pd.read_parquet(AGG / "lsoa_summary.parquet").dropna(subset=["imd_decile"])
    w = lsoa.n_homes
    deciles = pd.DataFrame(
        {c: (lsoa[c] * w).groupby(lsoa.imd_decile).sum() / w.groupby(lsoa.imd_decile).sum() for c in INDICATORS}
    ).reset_index()

    keep = ["n_homes", "n_msoas", "n_las", "median_sap", "latest_certificate", "min_homes_shown", *INDICATORS]
    return {
        "england": {k: england[k] for k in keep},
        "councils": _records(la),
        "by_age": _records(ages[["age_band", "n_homes", *INDICATORS]]),
        "by_decile": _records(deciles.rename(columns={"imd_decile": "decile"})),
    }


def la_hex() -> dict:
    """Council hex cartogram (GeoJSON, clockwise rings for d3-geo)."""
    return json.loads((AGG / "la_hex.geojson").read_text(encoding="utf-8"))
