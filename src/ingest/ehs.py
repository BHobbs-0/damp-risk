"""Load English Housing Survey (EHS) files: variable dictionary, search and Parquet export.

The EUL download from the UK Data Service is a zip containing SPSS (.sav) or
Stata (.dta) files plus documentation. Put each year's zip (or its extracted
folder) under ``data/raw/ehs/<year>/``. Zips are extracted automatically into
``data/raw/ehs/<year>/_extracted/<zip name>/``.

Commands:
    # 1. Build a searchable dictionary of every variable in every file
    .venv\\Scripts\\python.exe -m src.ingest.ehs dictionary

    # 2. Search names, labels and value labels (case-insensitive regex)
    .venv\\Scripts\\python.exe -m src.ingest.ehs search damp
    .venv\\Scripts\\python.exe -m src.ingest.ehs search "mould|condens"

    # 3. Convert the data files to Parquet (+ value labels as JSON)
    .venv\\Scripts\\python.exe -m src.ingest.ehs convert

Outputs (git-ignored, because the EUL forbids redistribution):
    data/interim/ehs/variable_dictionary.csv
    data/interim/ehs/<year>/<file>.parquet
    data/interim/ehs/<year>/<file>.value_labels.json
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path

import pandas as pd
import pyreadstat

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "ehs"
OUT_DIR = PROJECT_ROOT / "data" / "interim" / "ehs"
DICTIONARY = OUT_DIR / "variable_dictionary.csv"

READERS = {".sav": pyreadstat.read_sav, ".dta": pyreadstat.read_dta}


def extract_zips(raw_dir: Path = RAW_DIR) -> list[Path]:
    """Extract any UK Data Service zips into their own new folder (once)."""
    extracted = []
    for zip_path in sorted(raw_dir.rglob("*.zip")):
        if "_extracted" in zip_path.parts:
            continue
        target = zip_path.parent / "_extracted" / zip_path.stem
        if target.exists():
            continue
        with zipfile.ZipFile(zip_path) as zf:
            for name in zf.namelist():  # refuse paths that would escape the target folder
                if name.startswith(("/", "\\")) or ".." in Path(name).parts:
                    raise ValueError(f"Unsafe path {name!r} in {zip_path}")
            zf.extractall(target)
        extracted.append(target)
        print(f"Extracted {zip_path.name} -> {target.relative_to(raw_dir)}")
    return extracted


def survey_year(path: Path, raw_dir: Path = RAW_DIR) -> str:
    """Survey year = first folder under data/raw/ehs (e.g. '2022'), else first 20xx in the path."""
    try:
        first = path.relative_to(raw_dir).parts[0]
        if re.fullmatch(r"20\d{2}", first):
            return first
    except ValueError:
        pass
    match = re.search(r"(20\d{2})", str(path))
    return match.group(1) if match else "unknown"


def find_data_files(raw_dir: Path = RAW_DIR) -> list[Path]:
    """All SPSS / Stata files under the raw EHS folder.

    UK Data Service zips often contain the same data in more than one format.
    If both exist for a file, prefer .sav and skip the .dta duplicate.
    """
    files = sorted(p for p in raw_dir.rglob("*") if p.suffix.lower() in READERS)
    sav_stems = {(survey_year(p, raw_dir), p.stem.lower()) for p in files if p.suffix.lower() == ".sav"}
    return [
        p for p in files if not (p.suffix.lower() == ".dta" and (survey_year(p, raw_dir), p.stem.lower()) in sav_stems)
    ]


def _code(key: object) -> str:
    """SPSS stores codes as floats: show 1.0 as '1' but keep 1.5 as '1.5'."""
    if isinstance(key, float) and key.is_integer():
        return str(int(key))
    return str(key)


def _format_value_labels(labels: dict | None, limit: int = 15) -> str:
    if not labels:
        return ""
    items = [f"{_code(k)}={v}" for k, v in list(labels.items())[:limit]]
    more = f" (+{len(labels) - limit} more)" if len(labels) > limit else ""
    return "; ".join(items) + more


def build_dictionary(raw_dir: Path = RAW_DIR, out_path: Path = DICTIONARY) -> pd.DataFrame:
    """Read metadata only (fast, no data loaded) and write one row per variable."""
    extract_zips(raw_dir)
    rows = []
    for path in find_data_files(raw_dir):
        _, meta = READERS[path.suffix.lower()](path, metadataonly=True)
        value_labels = {var: meta.value_labels.get(name) for var, name in meta.variable_to_label.items()}
        for var in meta.column_names:
            rows.append(
                {
                    "year": survey_year(path, raw_dir),
                    "file": path.stem,
                    "variable": var,
                    "label": meta.column_names_to_labels.get(var) or "",
                    "n_rows": meta.number_rows,
                    "value_labels": _format_value_labels(value_labels.get(var)),
                }
            )
    df = pd.DataFrame(rows, columns=["year", "file", "variable", "label", "n_rows", "value_labels"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


def search(pattern: str, dictionary: pd.DataFrame | None = None) -> pd.DataFrame:
    """Case-insensitive regex search across variable names, labels and value labels."""
    df = dictionary if dictionary is not None else pd.read_csv(DICTIONARY, dtype=str).fillna("")
    text = df["variable"] + " | " + df["label"] + " | " + df["value_labels"]
    return df[text.str.contains(pattern, case=False, regex=True)]


def convert(raw_dir: Path = RAW_DIR, out_dir: Path = OUT_DIR) -> list[Path]:
    """Convert every data file to Parquet, keeping numeric codes and saving labels as JSON.

    Codes are kept (not replaced by text labels) so modelling code decides
    explicitly how to recode each variable, including EHS missing-value codes
    such as -8 / -9 ('does not apply' / 'unknown').
    """
    extract_zips(raw_dir)
    written = []
    for path in find_data_files(raw_dir):
        df, meta = READERS[path.suffix.lower()](path)
        year_dir = out_dir / survey_year(path, raw_dir)
        year_dir.mkdir(parents=True, exist_ok=True)
        out = year_dir / f"{path.stem.lower()}.parquet"
        df.columns = [c.lower() for c in df.columns]
        df.to_parquet(out, index=False, compression="zstd")
        labels = {
            "variable_labels": {k.lower(): v for k, v in meta.column_names_to_labels.items()},
            "value_labels": {
                var.lower(): {_code(k): v for k, v in meta.value_labels[name].items()}
                for var, name in meta.variable_to_label.items()
            },
        }
        out.with_suffix(".value_labels.json").write_text(json.dumps(labels, indent=1), encoding="utf-8")
        written.append(out)
        print(f"{survey_year(path, raw_dir)}/{path.name}: {len(df):,} rows x {df.shape[1]} cols -> {out.name}")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("dictionary", help="Build the variable dictionary CSV")
    s = sub.add_parser("search", help="Search the dictionary (regex)")
    s.add_argument("pattern")
    sub.add_parser("convert", help="Convert data files to Parquet")
    args = parser.parse_args()

    if not any(RAW_DIR.rglob("*.zip")) and not find_data_files():
        raise SystemExit(f"No EHS files found under {RAW_DIR}. See docs/data-sources.md section 1.")

    if args.command == "dictionary":
        df = build_dictionary()
        print(f"{len(df):,} variables from {df['file'].nunique()} files -> {DICTIONARY}")
        print(df.groupby(["year", "file"]).agg(variables=("variable", "size"), rows=("n_rows", "first")).to_string())
    elif args.command == "search":
        if not DICTIONARY.exists():
            build_dictionary()
        hits = search(args.pattern)
        with pd.option_context("display.max_colwidth", 80, "display.width", 200):
            print(hits.to_string(index=False) if len(hits) else f"No matches for {args.pattern!r}")
    elif args.command == "convert":
        convert()


if __name__ == "__main__":
    main()
