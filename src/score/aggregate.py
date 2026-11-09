"""Build the small, aggregated files the dashboard reads (app/data/).

Only area-level, non-disclosive data goes into app/data/ (it is committed and
deployed). Areas with fewer than MIN_HOMES scored homes have their metrics
blanked out.

Until the model exists (Week 2), areas are described by **building indicators
from the EPC** (e.g. % rated E-G, % with uninsulated walls). The published EHS
benchmarks show these are strongly linked to damp. Risk columns are added here
once `src/score` produces predictions.

Usage:
    .venv\\Scripts\\python.exe -m src.score.aggregate
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import duckdb
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOCIAL = PROJECT_ROOT / "data" / "processed" / "epc_social.parquet"
GEO = PROJECT_ROOT / "data" / "processed" / "geo"
IMD_CSV = PROJECT_ROOT / "data" / "raw" / "imd" / "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
APP_DATA = PROJECT_ROOT / "app" / "data"

MIN_HOMES = 10

# Indicator name -> SQL expression evaluated per home (true/false), averaged per area
INDICATORS = {
    "pct_epc_efg": "epc_band in ('E', 'F', 'G')",
    "pct_wall_uninsulated": "wall_insulation = 'none'",
    "pct_pre1919": "age_band = 'pre1919'",
    "pct_flats": "dwelling_type = 'flat'",
    "pct_electric_heating": "heating in ('electric_storage', 'electric_direct')",
    "pct_not_full_glazing": "glazing in ('single', 'partial')",
    "pct_cert_before_2015": "year(lodgement_date) < 2015",
}
MIX_FEATURES = ["dwelling_type", "age_band", "wall_insulation", "heating", "epc_band"]

# Simplification tolerance in metres (British National Grid) per level
SIMPLIFY_M = {"lad": 150, "msoa": 50}
COORD_DECIMALS = 4  # ~10 m at UK latitudes: plenty for screen maps, halves file size


def _indicator_sql() -> str:
    parts = [f"round(100.0 * avg(({expr})::int), 1) as {name}" for name, expr in INDICATORS.items()]
    return ",\n".join(parts + ["round(median(least(sap_score, 100)), 0) as median_sap"])


def _suppress(con: duckdb.DuckDBPyConnection, table: str) -> None:
    cols = list(INDICATORS) + ["median_sap"]
    con.sql(f"update {table} set " + ", ".join(f"{c} = null" for c in cols) + f" where n_homes < {MIN_HOMES}")


def build_summaries(con: duckdb.DuckDBPyConnection) -> dict:
    con.sql(f"create or replace view social as select * from read_parquet('{SOCIAL.as_posix()}')")
    con.sql(f"""
        create or replace view imd as
        select "LSOA code (2021)" as lsoa21cd,
               try_cast("Index of Multiple Deprivation (IMD) Score" as double) as imd_score,
               try_cast("Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)" as int)
                   as imd_decile,
               try_cast("Total population: mid 2022" as double) as population
        from read_csv('{IMD_CSV.as_posix()}', all_varchar = true)
    """)
    lsoa_geo = gpd.read_file(GEO / "lsoa_england.gpkg", columns=["lsoa21cd", "msoa21cd", "msoa21nm", "lad24cd"])
    con.register("hierarchy", lsoa_geo.drop(columns="geometry"))

    ind = _indicator_sql()
    con.sql(f"""
        create or replace table la_summary as
        select lad24cd, any_value(lad24nm) as lad24nm, mode(region_name) as region_name,
               count(*) as n_homes, {ind}
        from social
        where lad24cd is not null
        group by lad24cd
    """)
    con.sql(f"""
        create or replace table msoa_summary as
        with dep as (
            select h.msoa21cd,
                   sum(i.imd_score * i.population) / sum(i.population) as imd_score_popw,
                   round(100.0 * avg((i.imd_decile = 1)::int), 1) as pct_lsoas_most_deprived_decile
            from hierarchy h join imd i using (lsoa21cd) group by 1
        )
        select s.msoa21cd, any_value(s.msoa21nm) as msoa21nm, any_value(s.lad24cd) as lad24cd,
               count(*) as n_homes, {ind},
               round(any_value(d.imd_score_popw), 1) as imd_score_popw,
               any_value(d.pct_lsoas_most_deprived_decile) as pct_lsoas_most_deprived_decile
        from social s left join dep d using (msoa21cd)
        where s.msoa21cd like 'E%'  -- a few certificates marked England have Welsh postcodes
        group by s.msoa21cd
    """)
    con.sql(f"""
        create or replace table lsoa_summary as
        select s.lsoa21cd, any_value(s.msoa21cd) as msoa21cd, any_value(s.lad24cd) as lad24cd,
               count(*) as n_homes, {ind},
               any_value(i.imd_score) as imd_score, any_value(i.imd_decile) as imd_decile
        from social s left join imd i using (lsoa21cd)
        where s.lsoa21cd like 'E%'
        group by s.lsoa21cd
    """)
    for t in ("la_summary", "msoa_summary", "lsoa_summary"):
        _suppress(con, t)
    # LSOA file only keeps areas with enough homes (used for the deprivation analysis)
    con.sql(f"delete from lsoa_summary where n_homes < {MIN_HOMES}")

    mix_parts = []
    for f in MIX_FEATURES:
        mix_parts.append(f"""
            select lad24cd, '{f}' as feature, coalesce({f}::varchar, 'unknown') as category, count(*) as n
            from social where lad24cd is not null group by all
            union all
            select 'ENGLAND', '{f}', coalesce({f}::varchar, 'unknown'), count(*) from social group by all
        """)
    con.sql("create or replace table feature_mix as " + " union all ".join(mix_parts))
    con.sql("""
        create or replace table feature_mix as
        select *, round(100.0 * n / sum(n) over (partition by lad24cd, feature), 1) as pct from feature_mix
    """)

    england = con.sql(f"select count(*) as n_homes, {ind} from social").df().iloc[0].to_dict()
    england.update(
        {
            "n_msoas": int(con.sql("select count(*) from msoa_summary").fetchall()[0][0]),
            "n_las": int(con.sql("select count(*) from la_summary").fetchall()[0][0]),
            "latest_certificate": str(con.sql("select max(lodgement_date) from social").fetchall()[0][0]),
            "min_homes_shown": MIN_HOMES,
        }
    )
    return {k: (int(v) if k == "n_homes" else v) for k, v in england.items()}


def build_boundaries(out_dir: Path) -> None:
    """Simplified WGS84 GeoJSON: one LA file, and MSOA files split per LA."""
    # LSOA shapes are not shipped: at ~31 MB they'd triple the repo size for an optional
    # detail view. LSOA *data* is still used for the deprivation analysis.
    for level, fname, key in [("lad", "lad_england.gpkg", "lad24cd"), ("msoa", "msoa_england.gpkg", "msoa21cd")]:
        gdf = gpd.read_file(GEO / fname)
        gdf["geometry"] = gdf.geometry.simplify(SIMPLIFY_M[level], preserve_topology=True)
        gdf = gdf.to_crs(4326)
        if level == "lad":
            gdf[[key, "lad24nm", "geometry"]].to_file(
                out_dir / "la_boundaries.geojson", driver="GeoJSON", COORDINATE_PRECISION=COORD_DECIMALS
            )
            continue
        sub = out_dir / f"{level}_boundaries"
        sub.mkdir(exist_ok=True)
        for lad, part in gdf.groupby("lad24cd"):
            part[[key, "geometry"]].to_file(
                sub / f"{lad}.geojson", driver="GeoJSON", COORDINATE_PRECISION=COORD_DECIMALS
            )


def main() -> None:
    t0 = time.time()
    APP_DATA.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    england = build_summaries(con)
    for t in ("la_summary", "msoa_summary", "lsoa_summary", "feature_mix"):
        con.sql(f"copy {t} to '{(APP_DATA / f'{t}.parquet').as_posix()}' (format parquet, compression zstd)")
    (APP_DATA / "england_summary.json").write_text(json.dumps(england, indent=1, default=str), encoding="utf-8")
    build_boundaries(APP_DATA)

    total = sum(p.stat().st_size for p in APP_DATA.rglob("*") if p.is_file())
    print(json.dumps(england, indent=1, default=str))
    print(f"app/data: {total / 1e6:.1f} MB in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
