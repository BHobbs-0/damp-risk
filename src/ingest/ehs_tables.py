"""Parse the English Housing Survey's published damp tables (open data, no licence needed).

Sources (GOV.UK "Dwelling condition and safety" live tables, ODS):
    DA5101  Damp and mould - dwellings  (by dwelling age, type, floor area, occupancy)
    DA5102  Damp and mould - areas      (by area type, deprivation decile, region)

Each file has one sheet per survey year. Every sheet has the same shape: a label
column, then for each tenure (owner occupied, private rented, social rented, all
tenures) four damp measures (any damp, rising, penetrating, condensation/mould),
then the weighted number of dwellings and the unweighted sample size.

Output: data/interim/ehs_tables/damp_rates.parquet, one row per
(table, year, breakdown, category, tenure, damp_type) with the published % rate.
Rates suppressed by the survey for small samples ("u") become null.

Usage:
    .venv\\Scripts\\python.exe -m src.ingest.ehs_tables
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW = PROJECT_ROOT / "data" / "raw" / "ehs_tables"
OUT = PROJECT_ROOT / "data" / "interim" / "ehs_tables" / "damp_rates.parquet"

TENURES = {
    "owner occupied": "owner_occupied",
    "private rented": "private_rented",
    "social rented": "social_rented",
    "all tenures": "all",
}
DAMP_TYPES = {"any": "any", "rising": "rising", "penetrating": "penetrating", "condensation": "condensation_mould"}


def _norm(x: object) -> str:
    return re.sub(r"\s+", " ", str(x)).strip().lower() if pd.notna(x) else ""


def _damp_type(cell: object) -> str | None:
    s = _norm(cell)
    return next((v for k, v in DAMP_TYPES.items() if s.startswith(k)), None)


def parse_sheet(raw: pd.DataFrame, table: str, year: int) -> pd.DataFrame:
    """Parse one year's sheet into tidy rows."""
    cells = raw.map(_norm)
    tenure_row = next(i for i in range(len(cells)) if "social rented" in set(cells.iloc[i]))
    damp_row = tenure_row + 1

    # Map each rate column to (tenure, damp type): tenure label sits above the first of its columns
    col_map, tenure = {}, None
    for j in range(cells.shape[1]):
        label = cells.iat[tenure_row, j]
        if label in TENURES:
            tenure = TENURES[label]
        damp = _damp_type(raw.iat[damp_row, j])
        if tenure and damp:
            col_map[j] = (tenure, damp)
    dwell_col = next(j for j in range(cells.shape[1]) if "000s" in cells.iat[tenure_row, j])
    sample_col = next(j for j in range(cells.shape[1]) if "sample size" in cells.iat[tenure_row, j])

    rows, section = [], None
    for i in range(damp_row + 1, len(raw)):
        label = cells.iat[i, 0]
        if not label or label.startswith(("notes", "source", "1)", "2)", "3)", "4)")):
            if label.startswith(("notes", "source")):
                break
            continue
        values = [raw.iat[i, j] for j in col_map]
        if all(pd.isna(v) or _norm(v) == "" for v in values):  # a section heading, e.g. "dwelling age"
            section = label
            continue
        for j, (ten, damp) in col_map.items():
            v = raw.iat[i, j]
            rows.append(
                {
                    "table": table,
                    "year": year,
                    "breakdown": section or "all",
                    "category": label,
                    "tenure": ten,
                    "damp_type": damp,
                    "rate": pd.to_numeric(v, errors="coerce"),  # 'u' (suppressed) -> NaN
                    "suppressed": _norm(v) == "u",
                    "dwellings_000s": pd.to_numeric(raw.iat[i, dwell_col], errors="coerce"),
                    "sample_all_tenures": pd.to_numeric(raw.iat[i, sample_col], errors="coerce"),
                }
            )
    return pd.DataFrame(rows)


def parse_file(path: Path) -> pd.DataFrame:
    table = re.match(r"(DA\d{4})", path.name).group(1)
    sheets = pd.read_excel(path, engine="odf", sheet_name=None, header=None)
    parts = []
    for name, raw in sheets.items():
        if not re.fullmatch(r"\d{4}", str(name).strip()):
            continue
        raw = raw.dropna(how="all").dropna(axis=1, how="all").reset_index(drop=True)
        raw.columns = range(raw.shape[1])
        try:
            parts.append(parse_sheet(raw, table, int(name)))
        except StopIteration:
            # Before 2022 the tables split social housing into local authority / housing
            # association (DA5101) or had no tenure split (DA5102). Only the 2022+ layout is used.
            skipped.append(f"{table} {name}")
    return pd.concat(parts, ignore_index=True)


skipped: list[str] = []


def build(raw_dir: Path = RAW, out: Path = OUT) -> pd.DataFrame:
    files = sorted(raw_dir.glob("DA510[12]*.ods"))
    if not files:
        raise SystemExit(f"No DA5101/DA5102 files in {raw_dir}. See docs/data-sources.md.")
    df = pd.concat([parse_file(f) for f in files], ignore_index=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    return df


if __name__ == "__main__":
    d = build()
    print(f"{len(d):,} rows -> {OUT}")
    print(
        f"Skipped {len(skipped)} older sheets without a 'social rented' column "
        f"({min(skipped)[-4:]}–{max(skipped)[-4:]})"
    )
    print(d.groupby(["table"]).year.agg(["min", "max", "nunique"]).to_string())
    social = d[(d.tenure == "social_rented") & (d.damp_type == "any")]
    print("\nBreakdowns (social rented, any damp), years available:")
    print(social.groupby(["table", "breakdown"]).year.agg(["min", "max", "nunique"]).to_string())
