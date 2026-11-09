"""Build England LSOA, MSOA and local authority boundaries from the LSOA file.

MSOA and LA shapes are made by dissolving (merging) LSOAs, so every map uses
exactly the same geography as the data:
- LSOA -> MSOA from the ONS postcode lookup (LSOAs nest exactly in MSOAs)
- LSOA -> LA (2024 codes) from the IMD 2025 file

Outputs (British National Grid, EPSG:27700, full resolution):
    data/processed/geo/lsoa_england.gpkg
    data/processed/geo/msoa_england.gpkg
    data/processed/geo/lad_england.gpkg

Simplified, web-ready versions for the dashboard are made later (Week 4).

Usage:
    .venv\\Scripts\\python.exe -m src.geo.boundaries
"""

from __future__ import annotations

import time
from pathlib import Path

import duckdb
import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LSOA_GPKG = PROJECT_ROOT / "data" / "raw" / "boundaries" / "LSOA_2021_EW_BGC_V5.gpkg"
POSTCODES = PROJECT_ROOT / "data" / "interim" / "postcode_lookup.parquet"
IMD_CSV = PROJECT_ROOT / "data" / "raw" / "imd" / "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
OUT_DIR = PROJECT_ROOT / "data" / "processed" / "geo"


def lsoa_hierarchy() -> pd.DataFrame:
    """One row per England LSOA with its MSOA and LA (2024) codes and names."""
    con = duckdb.connect()
    df = con.sql(f"""
        with msoa as (
            select distinct lsoa21cd, msoa21cd, msoa21nm
            from read_parquet('{POSTCODES.as_posix()}')
            where lsoa21cd like 'E%'
        ),
        lad as (
            select "LSOA code (2021)" as lsoa21cd,
                   "LSOA name (2021)" as lsoa21nm,
                   "Local Authority District code (2024)" as lad24cd,
                   "Local Authority District name (2024)" as lad24nm
            from read_csv('{IMD_CSV.as_posix()}', all_varchar = true)
        )
        -- One MSOA (E02000781) has no name in the ONS lookup; MSOA names are
        -- the LSOA name minus its final letter ('Redbridge 012A' -> 'Redbridge 012').
        select lad.lsoa21cd, msoa.msoa21cd,
               coalesce(msoa.msoa21nm, regexp_replace(lad.lsoa21nm, '[A-Z]$', '')) as msoa21nm,
               lad.lad24cd, lad.lad24nm
        from lad left join msoa using (lsoa21cd)
    """).df()

    # Sanity checks: each LSOA belongs to exactly one MSOA and one LA
    dupes = df["lsoa21cd"].duplicated().sum()
    missing = df["msoa21cd"].isna().sum()
    if dupes or missing:
        raise ValueError(f"LSOA hierarchy problem: {dupes} duplicated LSOAs, {missing} without an MSOA")
    return df


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    lsoa = gpd.read_file(LSOA_GPKG, columns=["LSOA21CD", "LSOA21NM"])
    lsoa = lsoa[lsoa["LSOA21CD"].str.startswith("E")].rename(columns=str.lower)
    lsoa = lsoa.merge(lsoa_hierarchy(), on="lsoa21cd", how="left", validate="one_to_one")
    lsoa.to_file(OUT_DIR / "lsoa_england.gpkg", driver="GPKG")
    print(f"LSOA: {len(lsoa):,}")

    # Group by code only: dissolve silently drops groups with a null key, so a
    # missing name would lose the whole area. Names are carried with aggfunc='first'.
    msoa = lsoa.dissolve(by="msoa21cd", aggfunc="first", as_index=False)[
        ["msoa21cd", "msoa21nm", "lad24cd", "lad24nm", "geometry"]
    ]
    msoa.to_file(OUT_DIR / "msoa_england.gpkg", driver="GPKG")
    print(f"MSOA: {len(msoa):,}")

    lad = lsoa.dissolve(by="lad24cd", aggfunc="first", as_index=False)[["lad24cd", "lad24nm", "geometry"]]
    for name, gdf, expected in [("MSOA", msoa, lsoa["msoa21cd"].nunique()), ("LA", lad, lsoa["lad24cd"].nunique())]:
        if len(gdf) != expected:
            raise ValueError(f"{name}: dissolved {len(gdf)} areas but expected {expected}")
    lad.to_file(OUT_DIR / "lad_england.gpkg", driver="GPKG")
    print(f"LA:   {len(lad):,}")


def main() -> None:
    t0 = time.time()
    build()
    print(f"Done in {time.time() - t0:.0f}s -> {OUT_DIR}")


if __name__ == "__main__":
    main()
