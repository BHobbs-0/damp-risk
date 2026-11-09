"""Clean EPC certificates for social homes and engineer model features.

Pipeline:
    data/interim/epc/certificates_*.parquet      (raw strings, all tenures)
      -> latest certificate per UPRN, England, social rented
      -> join postcode lookup (OA/LSOA/MSOA) and IMD 2025 (LA 2024 codes)
      -> parse free-text fields into coarse categories
    data/processed/epc_social.parquet

Design choices (see docs/design.md and docs/data-sources.md):
- Categories are deliberately **coarse** so they can be matched to English
  Housing Survey (EHS) derived variables later. Raw fields are kept alongside
  for EDA.
- Free-text fields have only a few hundred distinct values, so each parser runs
  once per *distinct* value in Python (easy to unit test). The results are
  joined back in DuckDB, which is fast on 2.9M rows.

Usage:
    .venv\\Scripts\\python.exe -m src.features.epc
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EPC_GLOB = PROJECT_ROOT / "data" / "interim" / "epc" / "certificates_*.parquet"
POSTCODES = PROJECT_ROOT / "data" / "interim" / "postcode_lookup.parquet"
IMD_CSV = PROJECT_ROOT / "data" / "raw" / "imd" / "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
OUT_PATH = PROJECT_ROOT / "data" / "processed" / "epc_social.parquet"

# Values EPC uses to mean "missing"
PLACEHOLDERS = {"", "no data!", "invalid!", "not recorded", "nodata!", "n/a", "nan", "none"}

REGION_NAMES = {
    "E12000001": "North East",
    "E12000002": "North West",
    "E12000003": "Yorkshire and The Humber",
    "E12000004": "East Midlands",
    "E12000005": "West Midlands",
    "E12000006": "East of England",
    "E12000007": "London",
    "E12000008": "South East",
    "E12000009": "South West",
}

AGE_BANDS = ["pre1919", "1919-1944", "1945-1964", "1965-1980", "1981-1990", "post1990"]


def _clean(value: object) -> str | None:
    """Lower-case and strip a raw value; return None for EPC placeholders."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip().lower()
    return None if s in PLACEHOLDERS else s


# ---------------------------------------------------------------------------
# Parsers: one raw string in, clean categories out
# ---------------------------------------------------------------------------


def parse_age_band(raw: object) -> str | None:
    """Map an EPC construction age band to EHS-style age bands.

    EPC bands don't line up with EHS bands (e.g. EPC '1900-1929' straddles the
    EHS 1919 cut-off), so each EPC band is assigned using its **midpoint year**.
    'before 1900' uses 1899 and '2012 onwards' uses 2012. This is an
    approximation, documented as a harmonisation limitation.
    """
    s = _clean(raw)
    if s is None:
        return None
    years = [int(y) for y in re.findall(r"\b(1[89]\d{2}|20\d{2})\b", s)]
    if not years:
        return None
    if "before" in s:
        year = years[0] - 1
    elif len(years) >= 2:
        year = (years[0] + years[1]) / 2
    else:
        year = years[0]  # single year, or 'YYYY onwards'
    if year < 1919:
        return "pre1919"
    if year < 1945:
        return "1919-1944"
    if year < 1965:
        return "1945-1964"
    if year < 1981:
        return "1965-1980"
    if year < 1991:
        return "1981-1990"
    return "post1990"


def parse_walls(raw: object) -> tuple[str | None, str | None]:
    """Return (wall_type, wall_insulation) from a walls description.

    wall_type:       cavity | solid | timber | system | other
    wall_insulation: insulated | partial | none
    Newer certificates give a U-value instead ("Average thermal transmittance
    0.19 W/m²K"): type is unknown ('other') and U <= 0.6 counts as insulated.
    """
    s = _clean(raw)
    if s is None:
        return None, None

    u_value = re.search(r"transmittance\s+([\d.]+)", s)
    if u_value:
        return "other", "insulated" if float(u_value.group(1)) <= 0.6 else "none"

    if "cavity" in s:
        wall_type = "cavity"
    elif any(k in s for k in ("solid brick", "sandstone", "limestone", "granite", "whinstone", "cob", "stone")):
        wall_type = "solid"
    elif "timber" in s:
        wall_type = "timber"
    elif "system" in s:
        wall_type = "system"
    else:
        wall_type = "other"

    if "partial" in s:
        insulation = "partial"
    elif "no insulation" in s:
        insulation = "none"
    elif any(k in s for k in ("filled cavity", "insulated", "with external", "with internal", "additional insulation")):
        insulation = "insulated"
    else:
        insulation = None
    return wall_type, insulation


def parse_heating(raw: object) -> str | None:
    """Main heating system: community | heat_pump | electric_storage | gas |
    other_fuel | electric_direct | other."""
    s = _clean(raw)
    if s is None:
        return None
    if "community" in s:
        return "community"
    if "heat pump" in s:
        return "heat_pump"
    if "storage heater" in s:
        return "electric_storage"
    if "mains gas" in s:
        return "gas"
    if any(
        k in s for k in ("oil", "lpg", "coal", "smokeless", "wood", "dual fuel", "anthracite", "biomass", "bottled")
    ):
        return "other_fuel"
    if "electric" in s:
        return "electric_direct"
    return "other"


def parse_roof(raw: object) -> tuple[str | None, str | None]:
    """Return (roof_type, roof_insulation).

    roof_type:       dwelling_above | pitched | flat | thatched | roof_rooms | other
    roof_insulation: none (<50mm) | limited (50-149mm) | moderate (150-249mm) | good (250mm+)
                     None when another dwelling is above (no roof to insulate)
    """
    s = _clean(raw)
    if s is None:
        return None, None
    if "dwelling above" in s or "premises above" in s:
        return "dwelling_above", None

    u_value = re.search(r"transmittance\s+([\d.]+)", s)
    if u_value:  # newer certificates: U-value instead of a description
        return "other", "good" if float(u_value.group(1)) <= 0.25 else "limited"

    if "roof room" in s:
        roof_type = "roof_rooms"
    elif "pitched" in s:
        roof_type = "pitched"
    elif "flat" in s:
        roof_type = "flat"
    elif "thatched" in s:
        roof_type = "thatched"
    else:
        roof_type = "other"

    mm = re.search(r"(\d+)\+?\s*mm", s)
    if mm:
        depth = int(mm.group(1))
        insulation = "none" if depth < 50 else "limited" if depth < 150 else "moderate" if depth < 250 else "good"
    elif "no insulation" in s:
        insulation = "none"
    elif "limited insulation" in s:
        insulation = "limited"
    elif "insulated" in s:
        insulation = "moderate"  # 'insulated (assumed)': depth unknown, so don't claim 'good'
    else:
        insulation = None
    return roof_type, insulation


def parse_floor_type(raw: object) -> str | None:
    """Ground floor construction: dwelling_below | suspended | solid | exposed | other."""
    s = _clean(raw)
    if s is None:
        return None
    if "dwelling below" in s or "premises below" in s:
        return "dwelling_below"
    if "suspended" in s:
        return "suspended"
    if "solid" in s:
        return "solid"
    if "unheated space" in s or "external air" in s:
        return "exposed"
    return "other"


def parse_glazing(raw: object) -> str | None:
    """Glazing coverage from windows description: full | partial | single."""
    s = _clean(raw)
    if s is None:
        return None
    if s.startswith("single"):
        return "single"
    if any(k in s for k in ("mostly", "partial", "some")):
        return "partial"
    if any(k in s for k in ("fully", "high performance", "throughout", "full secondary")):
        return "full"
    return None


def parse_floor_level(raw: object) -> int | None:
    """Storey a flat is on: basement = -1, ground = 0, '3rd' = 3, '21st or above' = 21.
    'mid floor' / 'top floor' (no number) return None; flat_position handles them."""
    s = _clean(raw)
    if s is None:
        return None
    if "basement" in s:
        return -1
    if s.startswith("ground"):
        return 0
    num = re.match(r"(-?\d+)", s)
    return int(num.group(1)) if num else None


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def _mapping_table(con: duckdb.DuckDBPyConnection, column: str, parser, out_cols: list[str]) -> pd.DataFrame:
    """Run `parser` over every distinct value of `column` in the social table."""
    distinct = con.sql(f"select distinct {column} as raw from social_raw").df()
    parsed = distinct["raw"].map(parser)
    if len(out_cols) == 1:
        distinct[out_cols[0]] = parsed
    else:
        for i, col in enumerate(out_cols):
            distinct[col] = parsed.map(lambda t, i=i: t[i])
    return distinct


def build(con: duckdb.DuckDBPyConnection | None = None) -> pd.DataFrame:
    """Build and write the clean social-homes table. Returns a one-row summary."""
    con = con or duckdb.connect()

    # 1. Latest certificate per property (UPRN), England, social rented
    con.sql(f"""
        create or replace temp table social_raw as
        select *
        from read_parquet('{EPC_GLOB.as_posix()}')
        where uprn is not null and uprn <> '' and country = 'England'
        qualify row_number() over (
            partition by uprn
            order by lodgement_datetime desc nulls last, lodgement_date desc, certificate_number desc
        ) = 1
    """)
    # Filter tenure *after* picking the latest certificate: a home that was
    # social but has since been sold should drop out.
    con.sql("delete from social_raw where lower(coalesce(tenure, '')) <> 'rented (social)'")

    # 2. Mapping tables for free-text fields (parsed once per distinct value)
    maps = {
        "map_age": _mapping_table(con, "construction_age_band", parse_age_band, ["age_band"]),
        "map_walls": _mapping_table(con, "walls_description", parse_walls, ["wall_type", "wall_insulation"]),
        "map_heat": _mapping_table(con, "mainheat_description", parse_heating, ["heating"]),
        "map_roof": _mapping_table(con, "roof_description", parse_roof, ["roof_type", "roof_insulation"]),
        "map_floor": _mapping_table(con, "floor_description", parse_floor_type, ["floor_type"]),
        "map_glaze": _mapping_table(con, "windows_description", parse_glazing, ["glazing"]),
        "map_level": _mapping_table(con, "floor_level", parse_floor_level, ["floor_level_num"]),
    }
    for name, df in maps.items():
        con.register(name, df)
    con.register(
        "map_region", pd.DataFrame({"region_code": list(REGION_NAMES), "region_name": list(REGION_NAMES.values())})
    )

    # 3. Geography lookups
    con.sql(f"""
        create or replace temp view pc as
        select pcd_key, oa21cd, lsoa21cd, msoa21cd, msoa21nm
        from read_parquet('{POSTCODES.as_posix()}')
    """)
    con.sql(f"""
        create or replace temp view imd_lad as
        select "LSOA code (2021)" as lsoa21cd,
               "Local Authority District code (2024)" as lad24cd,
               "Local Authority District name (2024)" as lad24nm
        from read_csv('{IMD_CSV.as_posix()}', all_varchar = true)
    """)

    # 4. Assemble the clean table
    con.sql("""
        create or replace temp table social as
        with ref as (select max(try_cast(lodgement_date as date)) as ref_date from social_raw)
        select
            s.uprn,
            -- geography
            p.oa21cd, p.lsoa21cd, p.msoa21cd, p.msoa21nm, i.lad24cd, i.lad24nm,
            s.region as region_code, r.region_name,
            -- dwelling form
            case
                when s.property_type in ('Flat', 'Maisonette') then 'flat'
                when s.property_type = 'Bungalow' then 'bungalow'
                when s.property_type = 'House' then case
                    when s.built_form = 'Detached' then 'detached'
                    when s.built_form = 'Semi-Detached' then 'semi_detached'
                    when s.built_form in ('End-Terrace', 'Enclosed End-Terrace') then 'end_terrace'
                    when s.built_form in ('Mid-Terrace', 'Enclosed Mid-Terrace') then 'mid_terrace'
                    else 'house_unknown' end
                else 'other'
            end as dwelling_type,
            case
                when s.property_type not in ('Flat', 'Maisonette') then 'not_flat'
                when lv.floor_level_num = -1 then 'basement'
                when lv.floor_level_num = 0 or lower(s.floor_level) like 'ground%' then 'ground'
                when s.flat_top_storey = 'Y' or lower(s.floor_level) like 'top%' then 'top'
                else 'mid'
            end as flat_position,
            lv.floor_level_num,
            coalesce(lv.floor_level_num >= 6, false) as high_rise_flat,
            a.age_band,
            -- fabric
            w.wall_type, w.wall_insulation,
            rf.roof_type, rf.roof_insulation,
            f.floor_type,
            g.glazing,
            -- services
            h.heating,
            case s.mains_gas_flag when 'Y' then true when 'N' then false end as mains_gas,
            case when s.mechanical_ventilation is null then null
                 else lower(s.mechanical_ventilation) <> 'natural' end as mechanical_ventilation,
            -- performance and size
            try_cast(s.current_energy_efficiency as integer) as sap_score,
            s.current_energy_rating as epc_band,
            case when try_cast(s.total_floor_area as double) between 10 and 1000
                 then try_cast(s.total_floor_area as double) end as floor_area_m2,
            try_cast(s.number_habitable_rooms as integer) as habitable_rooms,
            -- certificate metadata
            try_cast(s.lodgement_date as date) as lodgement_date,
            date_diff('day', try_cast(s.lodgement_date as date), ref.ref_date) / 365.25 as cert_age_years,
            s.transaction_type,
            -- raw fields kept for EDA / audit
            s.property_type as raw_property_type, s.built_form as raw_built_form,
            s.construction_age_band as raw_age_band, s.walls_description as raw_walls,
            s.mainheat_description as raw_heating, s.roof_description as raw_roof
        from social_raw s
        cross join ref
        left join pc p on p.pcd_key = upper(replace(s.postcode, ' ', ''))
        left join imd_lad i on i.lsoa21cd = p.lsoa21cd
        left join map_region r on r.region_code = s.region
        left join map_age a on a.raw is not distinct from s.construction_age_band
        left join map_walls w on w.raw is not distinct from s.walls_description
        left join map_heat h on h.raw is not distinct from s.mainheat_description
        left join map_roof rf on rf.raw is not distinct from s.roof_description
        left join map_floor f on f.raw is not distinct from s.floor_description
        left join map_glaze g on g.raw is not distinct from s.windows_description
        left join map_level lv on lv.raw is not distinct from s.floor_level
    """)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    con.sql(f"copy social to '{OUT_PATH.as_posix()}' (format parquet, compression zstd)")

    return con.sql("""
        select count(*) as homes,
               count(lsoa21cd) as with_lsoa,
               count(lad24cd) as with_la,
               round(100.0 * avg((age_band is null)::int), 2) as pct_missing_age,
               round(100.0 * avg((wall_type is null)::int), 2) as pct_missing_walls,
               round(100.0 * avg((wall_insulation is null)::int), 2) as pct_missing_wall_ins,
               round(100.0 * avg((heating is null)::int), 2) as pct_missing_heating,
               round(100.0 * avg((glazing is null)::int), 2) as pct_missing_glazing,
               round(100.0 * avg((sap_score is null)::int), 2) as pct_missing_sap
        from social
    """).df()


def main() -> None:
    t0 = time.time()
    summary = build()
    print(summary.T.to_string(header=False))
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size / 1e6:.0f} MB) in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
