"""Convert the ONS postcode -> OA/LSOA/MSOA/LAD best-fit lookup to Parquet.

Reads the CSV straight from the ONS zip and writes
``data/interim/postcode_lookup.parquet`` with a normalised join key
(``pcd_key``: upper-case, no spaces) so EPC postcodes can be matched
regardless of spacing.

Usage:
    .venv\\Scripts\\python.exe -m src.ingest.postcodes
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pv
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ZIP = PROJECT_ROOT / "data" / "raw" / "postcodes" / "PCD_OA21_LSOA21_MSOA21_LAD_MAY26_UK_LU.zip"
DEFAULT_OUT = PROJECT_ROOT / "data" / "interim" / "postcode_lookup.parquet"


def normalise_postcode(arr: pa.Array) -> pa.Array:
    """Upper-case and strip all whitespace: 'm1 1ae' / 'M1  1AE' -> 'M11AE'."""
    return pc.replace_substring_regex(pc.utf8_upper(arr), pattern=r"\s+", replacement="")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    with zipfile.ZipFile(args.zip) as zf:
        csv_name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        with zf.open(csv_name) as raw:
            table = pv.read_csv(
                raw,
                read_options=pv.ReadOptions(encoding="latin-1"),  # ONS files may contain non-UTF8 Welsh names
                convert_options=pv.ConvertOptions(strings_can_be_null=True, auto_dict_encode=False),
            )

    table = table.rename_columns([c.lower() for c in table.column_names])
    # All codes as text, even if pyarrow guessed numbers
    table = table.cast(pa.schema([pa.field(c, pa.string()) for c in table.column_names]))
    table = table.append_column("pcd_key", normalise_postcode(table["pcds"]))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, args.out, compression="zstd")
    print(f"{table.num_rows:,} postcodes -> {args.out} ({args.out.stat().st_size / 1e6:.0f} MB)")
    print("columns:", table.column_names)


if __name__ == "__main__":
    main()
