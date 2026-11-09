"""Cached loaders for app/data (small, aggregated, non-disclosive files only)."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data"


@st.cache_data
def england() -> dict:
    return json.loads((DATA / "england_summary.json").read_text(encoding="utf-8"))


@st.cache_data
def la_summary() -> pd.DataFrame:
    return pd.read_parquet(DATA / "la_summary.parquet")


@st.cache_data
def msoa_summary() -> pd.DataFrame:
    return pd.read_parquet(DATA / "msoa_summary.parquet")


@st.cache_data
def lsoa_summary() -> pd.DataFrame:
    return pd.read_parquet(DATA / "lsoa_summary.parquet")


@st.cache_data
def feature_mix() -> pd.DataFrame:
    return pd.read_parquet(DATA / "feature_mix.parquet")


@st.cache_data
def la_geojson() -> dict:
    return json.loads((DATA / "la_boundaries.geojson").read_text(encoding="utf-8"))


@st.cache_data
def msoa_geojson(lad24cd: str) -> dict:
    return json.loads((DATA / "msoa_boundaries" / f"{lad24cd}.geojson").read_text(encoding="utf-8"))


def bounds(geojson: dict) -> tuple[float, float, float, float]:
    """(min_lon, min_lat, max_lon, max_lat) of all coordinates in a GeoJSON."""
    xs, ys = [], []

    def walk(coords):
        if isinstance(coords[0], (int, float)):
            xs.append(coords[0])
            ys.append(coords[1])
        else:
            for c in coords:
                walk(c)

    for f in geojson["features"]:
        walk(f["geometry"]["coordinates"])
    return min(xs), min(ys), max(xs), max(ys)
