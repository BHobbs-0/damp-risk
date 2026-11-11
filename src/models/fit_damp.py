"""Fit the damp risk model to published EHS rates and validate it.

Pipeline:
    1. Group the 2.86m EPC social homes into cells (age x type x floor area x energy
       rating x region x deprivation decile) with counts.
    2. Targets: published social rented damp rates (EHS live tables DA5101, average of
       2023 and 2024) for age, dwelling type and floor area, plus energy rating derived
       from the EHS 2023-24 "Drivers and impacts" report (see EER_TARGETS).
    3. Fit `MarginModel` (src/models/calibrate.py) to those margins.
    4. Validate on margins the model never saw (region, deprivation decile; DA5102),
       and by leaving each fitted margin out in turn.

Outputs (data/processed/model/):
    damp_model.json      intercept, coefficients, targets and provenance
    validation.json      summary metrics
    margins.csv          predicted vs published rate for every category

Usage:
    .venv\\Scripts\\python.exe -m src.models.fit_damp
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from src.models.calibrate import MarginModel, margin_table, summarise

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOCIAL = PROJECT_ROOT / "data" / "processed" / "epc_social.parquet"
IMD_CSV = PROJECT_ROOT / "data" / "raw" / "imd" / "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
RATES = PROJECT_ROOT / "data" / "interim" / "ehs_tables" / "damp_rates.parquet"
OUT = PROJECT_ROOT / "data" / "processed" / "model"

TARGET_YEARS = (2023, 2024)  # 2022 excluded: partly modelled (COVID), visibly lower
FEATURES = ["age", "type", "area", "eer"]
HELD_OUT = ["region", "imd_decile"]

# EHS category -> our category
AGE_MAP = {
    "pre-1919": "pre1919",
    "1919-44": "1919-1944",
    "1945-64": "1945-1964",
    "1965-80": "1965-1980",
    "1981-90": "1981-1990",
    "post 1990": "post1990",
}
TYPE_MAP = {
    "end terrace": "end_terrace",
    "mid terrace": "mid_terrace",
    "semi-detached": "semi_detached",
    "bungalow": "bungalow",
    "all flats": "flat",
}  # EHS social 'detached' is suppressed
AREA_MAP = {
    "less than 50m2": "<50",
    "50 to 69m2": "50-69",
    "70 to 89m2": "70-89",
    "90 to 109m2": "90-109",
    "110m2 or more": "110+",
}
REGION_MAP = {
    "north east": "E12000001",
    "north west": "E12000002",
    "yorkshire and the humber": "E12000003",
    "east midlands": "E12000004",
    "west midlands": "E12000005",
    "east of england": "E12000006",
    "london": "E12000007",
    "south east": "E12000008",
    "south west": "E12000009",
}
DECILE_MAP = {
    "most deprived 10% of areas": "1",
    "2nd": "2",
    "3rd": "3",
    "4th": "4",
    "5th": "5",
    "6th": "6",
    "7th": "7",
    "8th": "8",
    "9th": "9",
    "least deprived 10% of areas": "10",
}

# Energy rating: the live tables don't split it by tenure. The EHS 2023-24 "Drivers and impacts
# of housing quality" report gives social figures: band D 9%; A-C 8% (LA) / 4% (HA); E-G 29% (LA) /
# 16% (HA). LA and HA are combined using the approximate social stock split (LA ~39%, HA ~61%).
LA_SHARE = 0.39
EER_TARGETS = {
    "A-C": LA_SHARE * 0.08 + (1 - LA_SHARE) * 0.04,
    "D": 0.09,
    "E-G": LA_SHARE * 0.29 + (1 - LA_SHARE) * 0.16,
}


# Model features from EPC fields, in the categories the published rates use.
# Shared by fitting (grouped into cells) and scoring (per home), so they can't drift apart.
FEATURE_SQL = """
    coalesce(age_band, 'unknown') as age,
    case when dwelling_type in ('end_terrace','mid_terrace','semi_detached','bungalow','flat','detached')
         then dwelling_type else 'other' end as type,
    case when floor_area_m2 < 50 then '<50' when floor_area_m2 < 70 then '50-69'
         when floor_area_m2 < 90 then '70-89' when floor_area_m2 < 110 then '90-109'
         when floor_area_m2 >= 110 then '110+' else 'unknown' end as area,
    case when epc_band in ('A','B','C') then 'A-C' when epc_band = 'D' then 'D'
         when epc_band in ('E','F','G') then 'E-G' else 'unknown' end as eer
"""


def load_cells() -> pd.DataFrame:
    con = duckdb.connect()
    return (
        con.sql(f"""
        with imd as (
            select "LSOA code (2021)" as lsoa21cd,
                   "Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)" as imd_decile
            from read_csv('{IMD_CSV.as_posix()}', all_varchar = true)
        )
        select {FEATURE_SQL},
            region_code as region,
            imd.imd_decile,
            count(*) as n
        from read_parquet('{SOCIAL.as_posix()}') s
        left join imd using (lsoa21cd)
        group by all
    """)
        .df()
        .fillna("unknown")
    )


def load_targets(years=TARGET_YEARS) -> tuple[dict, dict]:
    """(fitted targets, held-out targets) as {feature: {category: rate 0-1}}."""
    r = pd.read_parquet(RATES)
    r = r[(r.tenure == "social_rented") & (r.damp_type == "any") & r.year.isin(years)]
    avg = r.groupby(["breakdown", "category"]).rate.mean() / 100  # average of the years (skips suppressed)

    def pick(breakdown, mapping):
        s = avg.loc[breakdown]
        return {ours: float(s[ehs]) for ehs, ours in mapping.items() if ehs in s and not np.isnan(s[ehs])}

    fitted = {
        "age": pick("dwelling age", AGE_MAP),
        "type": pick("dwelling type", TYPE_MAP),
        "area": pick("total usable floor area", AREA_MAP),
        "eer": EER_TARGETS,
    }
    held = {
        "region": pick("government office region", REGION_MAP),
        "imd_decile": pick("deprived local areas", DECILE_MAP),
    }
    # The table's national "all dwellings" row sits under whichever breakdown comes last, so find it by category
    totals = avg[avg.index.get_level_values("category") == "all dwellings"]
    if totals.empty:
        raise ValueError("No 'all dwellings' row found in the published rates")
    return fitted, held | {"_overall": float(totals.mean())}


SOCIAL_SAMPLE_SHARE = 0.17  # approx. share of EHS surveyed dwellings that are social rented
OVERLAP_FACTOR = 1.5  # 2023 and 2024 are two-year rolling samples sharing a year: ~1.5x one year's sample


def noise_floor(breakdown: str, mapping: dict, targets: dict, years=TARGET_YEARS) -> float:
    """Expected mean absolute error (points) from sampling noise alone, even for a perfect model.

    The published rate for a category is itself an estimate from a few hundred social homes.
    For a binomial proportion, E|estimate - truth| = sqrt(2/pi) * sqrt(p(1-p)/n). The table only gives
    the all-tenure sample size, so the social sample is approximated; design effects are ignored,
    so this is a *lower bound* on the noise.
    """
    r = pd.read_parquet(RATES)
    r = r[
        (r.table == "DA5102")
        & (r.breakdown == breakdown)
        & r.year.isin(years)
        & (r.tenure == "social_rented")
        & (r.damp_type == "any")
    ]
    n_all = r.groupby("category").sample_all_tenures.mean()
    errs = []
    for ehs, ours in mapping.items():
        if ours in targets and ehs in n_all:
            n = n_all[ehs] * SOCIAL_SAMPLE_SHARE * OVERLAP_FACTOR
            t = targets[ours]
            errs.append(np.sqrt(2 / np.pi) * np.sqrt(t * (1 - t) / n) * 100)
    return round(float(np.mean(errs)), 2) if errs else float("nan")


def main() -> None:
    cells = load_cells()
    fitted, held = load_targets()
    overall = held.pop("_overall") or 0.069
    model = MarginModel(FEATURES).fit(cells, fitted)
    p = model.predict(cells)
    predicted_overall = float(np.average(p, weights=cells.n))

    report = {"fit": summarise(model.fit_report, overall)}
    held_tables = {}
    floors = {
        "region": noise_floor("government office region", REGION_MAP, held["region"]),
        "imd_decile": noise_floor("deprived local areas", DECILE_MAP, held["imd_decile"]),
    }
    for f in HELD_OUT:
        t = margin_table(p, cells, {f: held[f]})
        held_tables[f] = t
        report[f"held_out_{f}"] = summarise(t, overall) | {"noise_floor_mae_pts": floors[f]}

    loo_tables = []
    for f in FEATURES:  # leave each fitted margin out, refit, predict it
        m = MarginModel(FEATURES).fit(cells, {k: v for k, v in fitted.items() if k != f})
        t = margin_table(m.predict(cells), cells, {f: fitted[f]})
        report[f"leave_out_{f}"] = summarise(t, overall)
        loo_tables.append(t.assign(check=f"leave_out_{f}"))

    report["overall"] = {
        "published_social_rate": round(overall, 4),
        "predicted_mean": round(predicted_overall, 4),
        "homes": int(cells.n.sum()),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "damp_model.json").write_text(
        json.dumps(
            {
                "intercept": model.intercept,
                "coefs": model.coefs,
                "features": FEATURES,
                "targets": fitted,
                "target_years": list(TARGET_YEARS),
                "eer_targets_note": "Derived from EHS 2023-24 Drivers and impacts report; LA/HA combined with LA share "
                f"{LA_SHARE}",
                "source": "EHS live tables DA5101/DA5102 (social rented, any damp)",
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    (OUT / "validation.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    pd.concat(
        [
            model.fit_report.assign(check="fit"),
            *[t.assign(check=f"held_out_{k}") for k, t in held_tables.items()],
            *loo_tables,
        ]
    ).to_csv(OUT / "margins.csv", index=False)

    print(json.dumps(report, indent=1))
    print("\nCoefficients (log-odds vs average):")
    for f, c in model.coefs.items():
        print(f"  {f:6}", {k: round(v, 2) for k, v in sorted(c.items(), key=lambda kv: -kv[1])})
    for f, t in held_tables.items():
        print(f"\nHeld out: {f}")
        print(
            (
                t[["category", "target", "predicted"]].assign(
                    target=lambda d: (100 * d.target).round(1), predicted=lambda d: (100 * d.predicted).round(1)
                )
            ).to_string(index=False)
        )


if __name__ == "__main__":
    main()
