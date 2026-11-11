"""Data for the Observable Framework dashboard (dashboard/).

Framework's data loaders (dashboard/src/data/*.py) call these functions and
print JSON to stdout. Inputs are the aggregated, non-disclosive files built by
`python -m src.score.aggregate`, so nothing here touches raw or licensed data.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGG = PROJECT_ROOT / "data" / "processed" / "dashboard"  # output of src.score.aggregate

MODEL_DIR = PROJECT_ROOT / "data" / "processed" / "model"  # output of src.models.fit_damp

# `risk` = modelled % of homes estimated to have damp; the rest are EPC building indicators (% of homes)
INDICATORS = ["risk", "pct_wall_uninsulated", "pct_epc_efg", "pct_not_full_glazing", "pct_electric_heating"]
AGE_ORDER = ["pre1919", "1919-1944", "1945-1964", "1965-1980", "1981-1990", "post1990"]


def _records(df: pd.DataFrame) -> list[dict]:
    """JSON-safe records (NaN -> null, numbers rounded)."""
    return json.loads(df.round(2).to_json(orient="records"))


def _columns(df: pd.DataFrame, digits: int = 1) -> dict[str, list]:
    """Column-oriented JSON for big tables: names appear once instead of on every row
    (the browser turns it back into rows)."""
    out = {}
    for c in df.columns:
        col = df[c].round(digits) if df[c].dtype.kind == "f" else df[c]
        out[c] = json.loads(col.to_json(orient="values"))
    return out


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

    keep = [
        "n_homes",
        "n_msoas",
        "n_las",
        "median_sap",
        "latest_certificate",
        "min_homes_shown",
        "expected_cases",
        "risk_p90",
        *INDICATORS,
    ]
    return {
        "england": {k: england[k] for k in keep},
        "councils": _records(la),
        "by_age": _records(ages[["age_band", "n_homes", *INDICATORS]]),
        "by_decile": _records(deciles.rename(columns={"imd_decile": "decile"})),
    }


def la_hex() -> dict:
    """Council hex cartogram (GeoJSON, clockwise rings for d3-geo)."""
    return json.loads((AGG / "la_hex.geojson").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- Areas page

AREA_COLS = [*INDICATORS, "pct_pre1919", "median_sap", "expected_cases", "pct_top10"]
MIX_FEATURES = ["age_band", "dwelling_type", "heating", "epc_band"]


def areas() -> dict:
    """Councils and neighbourhoods (MSOAs) with indicators, plus housing mix per council vs England."""
    england = json.loads((AGG / "england_summary.json").read_text(encoding="utf-8"))
    la = pd.read_parquet(AGG / "la_summary.parquet")[["lad24cd", "lad24nm", "region_name", "n_homes", *AREA_COLS]]
    msoa = pd.read_parquet(AGG / "msoa_summary.parquet")[["msoa21cd", "msoa21nm", "lad24cd", "n_homes", *AREA_COLS]]

    mix_df = pd.read_parquet(AGG / "feature_mix.parquet")
    mix_df = mix_df[mix_df.feature.isin(MIX_FEATURES)]
    mix: dict = {}
    for (lad, feat), g in mix_df.groupby(["lad24cd", "feature"]):
        mix.setdefault(lad, {})[feat] = {str(c): round(float(p), 1) for c, p in zip(g.category, g.pct, strict=True)}

    return {
        "england": {k: england[k] for k in ["n_homes", "min_homes_shown", *AREA_COLS]},
        "councils": _records(la),
        "msoas": _columns(msoa),  # column-oriented: {col: [values]}
        "mix": mix,
    }


def msoa_shapes(simplify_m: float = 90, scale: float = 1e4) -> dict:
    """All England MSOA outlines in a compact encoding (~10x smaller than GeoJSON).

    Each ring is a flat list of integers: the first point as lon/lat * scale, then
    the change from the previous point. Small integers compress well and keep the
    whole country in one file the browser can load once. Rings are clockwise for d3-geo.
    """
    import geopandas as gpd  # local import: only this loader needs geopandas
    import shapely

    gdf = gpd.read_file(PROJECT_ROOT / "data" / "processed" / "geo" / "msoa_england.gpkg")
    gdf["geometry"] = gdf.geometry.simplify(simplify_m, preserve_topology=True)
    gdf = gdf.to_crs(4326)
    gdf["geometry"] = shapely.orient_polygons(gdf.geometry.values, exterior_cw=True)

    def encode(ring) -> list[int]:
        pts = [(round(x * scale), round(y * scale)) for x, y in ring.coords]
        out = [pts[0][0], pts[0][1]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:], strict=False):
            if (x1, y1) != (x0, y0):
                out += [x1 - x0, y1 - y0]
        return out

    shapes = []
    for code, lad, geom in zip(gdf.msoa21cd, gdf.lad24cd, gdf.geometry, strict=True):
        polys = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
        shapes.append(
            {"id": code, "lad": lad, "p": [[encode(p.exterior), *(encode(r) for r in p.interiors)] for p in polys]}
        )
    return {"scale": scale, "shapes": shapes}


# --------------------------------------------------------------------------- Deprivation page


def deprivation() -> dict:
    """Indicators by IMD decile (weighted mean and middle 50% of LSOAs) and MSOA points for a scatter."""
    lsoa = pd.read_parquet(AGG / "lsoa_summary.parquet").dropna(subset=["imd_decile"])
    w = lsoa.n_homes
    rows = []
    for d, g in lsoa.groupby("imd_decile"):
        row = {"decile": int(d), "n_lsoas": len(g), "n_homes": int(g.n_homes.sum())}
        for c in INDICATORS:
            row[c] = float((g[c] * g.n_homes).sum() / g.n_homes.sum())
            row[f"{c}_q1"], row[f"{c}_q3"] = (float(v) for v in g[c].quantile([0.25, 0.75]))
        rows.append(row)

    msoa = pd.read_parquet(AGG / "msoa_summary.parquet").dropna(subset=["imd_score_popw"])
    msoa = msoa[msoa.n_homes >= 10][["msoa21nm", "n_homes", "imd_score_popw", *INDICATORS]]
    return {
        "by_decile": _records(pd.DataFrame(rows)),
        "msoas": _columns(msoa.rename(columns={"msoa21nm": "name", "imd_score_popw": "imd"})),  # {col: [values]}
        "n_lsoas": int(len(lsoa)),
        "n_homes": int(w.sum()),
    }


# --------------------------------------------------------------------------- Drivers page


def drivers() -> dict:
    """National profile by construction age (all indicators) and published EHS damp rates."""
    cols = [*INDICATORS, "pct_pre1919", "median_sap"]
    ages = pd.read_parquet(AGG / "by_age_band.parquet").set_index("age_band").loc[AGE_ORDER].reset_index()
    england = json.loads((AGG / "england_summary.json").read_text(encoding="utf-8"))
    # English Housing Survey 2023 to 2024, "Drivers and impacts of housing quality" (all tenures, % with damp)
    ehs = [
        {"group": "Energy rating", "items": [["A–C", 3], ["D", 7], ["E–G", 12]]},
        {"group": "Walls", "items": [["Insulated", 3], ["Uninsulated", 8]]},
        {"group": "Loft insulation", "items": [["200mm or more", 3], ["Under 200mm", 7]]},
        {"group": "Glazing", "items": [["Fully double glazed", 5], ["Not fully", 10]]},
    ]
    return {
        "by_age": _records(ages[["age_band", "n_homes", *[c for c in cols if c in ages.columns]]]),
        "england": {k: england[k] for k in ["n_homes", *INDICATORS, "median_sap"]},
        "ehs": ehs,
        "ehs_social_2024": 7,
        "effects": model_effects(),
    }


FEATURE_LABELS = {"age": "Built", "type": "Type", "area": "Floor area", "eer": "Energy rating"}
CATEGORY_LABELS = {
    "pre1919": "before 1919",
    "1919-1944": "1919–44",
    "1945-1964": "1945–64",
    "1965-1980": "1965–80",
    "1981-1990": "1981–90",
    "post1990": "after 1990",
    "mid_terrace": "mid-terrace",
    "end_terrace": "end-terrace",
    "semi_detached": "semi-detached",
    "flat": "flat",
    "bungalow": "bungalow",
    "A-C": "A–C",
    "D": "D",
    "E-G": "E–G",
    "<50": "under 50m²",
    "50-69": "50–69m²",
    "70-89": "70–89m²",
    "90-109": "90–109m²",
    "110+": "110m² or more",
}


def model_effects() -> list[dict]:
    """Each fitted category's effect as an odds ratio vs a home with average characteristics.
    Categories fixed at 0 (no published rate, e.g. detached) are left out."""
    model = json.loads((MODEL_DIR / "damp_model.json").read_text(encoding="utf-8"))
    rows = []
    for f, coefs in model["coefs"].items():
        for cat, b in coefs.items():
            if cat in model["targets"].get(f, {}):
                rows.append(
                    {
                        "feature": FEATURE_LABELS[f],
                        "category": CATEGORY_LABELS.get(cat, cat),
                        "odds_ratio": round(float(np.exp(b)), 3),
                    }
                )
    return sorted(rows, key=lambda r: -abs(np.log(r["odds_ratio"])))


def method() -> dict:
    """Headline numbers and model validation for the Method page."""
    england = json.loads((AGG / "england_summary.json").read_text(encoding="utf-8"))
    keep = [
        "n_homes",
        "n_msoas",
        "n_las",
        "pct_cert_before_2015",
        "latest_certificate",
        "min_homes_shown",
        "risk",
        "expected_cases",
    ]
    validation = json.loads((MODEL_DIR / "validation.json").read_text(encoding="utf-8"))
    return {k: england[k] for k in keep} | {"validation": validation}
