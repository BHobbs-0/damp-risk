"""Convert the bulk EPC domestic download (zip of yearly CSVs) to Parquet.

Reads the ``certificates-*.csv`` files straight out of the zip (no extraction,
so the ~98 GB of uncompressed CSV never touches disk), keeps every column
except free-text address lines, and writes one zstd-compressed Parquet file
per year to ``data/interim/epc/``.

All columns are read as strings: types differ between years, so casting
happens later in ``src/features`` where each field is cleaned deliberately.

Usage:
    .venv\\Scripts\\python.exe -m src.ingest.epc
    .venv\\Scripts\\python.exe -m src.ingest.epc --years 2024 2025   # subset
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import time
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pv
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ZIP = PROJECT_ROOT / "data" / "raw" / "epc" / "domestic-csv.zip"
DEFAULT_OUT = PROJECT_ROOT / "data" / "interim" / "epc"

# Free-text address lines aren't needed for modelling; postcode + UPRN are kept
# for geography and de-duplication. Dropping them keeps personal data minimal.
DROP_COLUMNS = {"address1", "address2", "address3", "address"}

CERT_PATTERN = re.compile(r"^certificates-(\d{4})\.csv$")


def list_certificate_files(zf: zipfile.ZipFile) -> dict[int, str]:
    """Map year -> filename for every certificates CSV in the zip."""
    files = {}
    for name in zf.namelist():
        match = CERT_PATTERN.match(Path(name).name)
        if match:
            files[int(match.group(1))] = name
    return dict(sorted(files.items()))


def read_header(zf: zipfile.ZipFile, name: str) -> list[str]:
    with zf.open(name) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace")
        return next(csv.reader(text))


def convert_file(zf: zipfile.ZipFile, name: str, out_path: Path) -> int:
    """Stream one CSV from the zip into a Parquet file. Returns rows written."""
    header = read_header(zf, name)
    keep = [c for c in header if c.lower() not in DROP_COLUMNS]

    read_opts = pv.ReadOptions(block_size=64 * 1024 * 1024)
    parse_opts = pv.ParseOptions(newlines_in_values=True)
    convert_opts = pv.ConvertOptions(
        column_types={c: pa.string() for c in header},
        include_columns=keep,
        check_utf8=False,
        strings_can_be_null=True,
    )

    tmp_path = out_path.with_suffix(".parquet.tmp")
    rows = 0
    with zf.open(name) as raw:
        reader = pv.open_csv(
            raw, read_options=read_opts, parse_options=parse_opts, convert_options=convert_opts
        )
        with pq.ParquetWriter(tmp_path, reader.schema, compression="zstd") as writer:
            for batch in reader:
                writer.write_batch(batch)
                rows += batch.num_rows
    tmp_path.replace(out_path)  # only appears once complete
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--years", type=int, nargs="*", help="Only convert these years")
    parser.add_argument("--overwrite", action="store_true", help="Re-convert existing files")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.zip) as zf:
        files = list_certificate_files(zf)
        if args.years:
            files = {y: f for y, f in files.items() if y in set(args.years)}
        total_rows, start = 0, time.time()
        for year, name in files.items():
            out_path = args.out / f"certificates_{year}.parquet"
            if out_path.exists() and not args.overwrite:
                print(f"{year}: exists, skipping", flush=True)
                continue
            t0 = time.time()
            rows = convert_file(zf, name, out_path)
            total_rows += rows
            size_mb = out_path.stat().st_size / 1e6
            print(f"{year}: {rows:>10,} rows  {size_mb:7.0f} MB  {time.time() - t0:6.0f}s", flush=True)
        print(f"Done: {total_rows:,} rows in {time.time() - start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
