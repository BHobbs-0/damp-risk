"""Tests for the EHS loader using small synthetic SPSS files (not real EHS data)."""

import json
import zipfile

import pandas as pd
import pyreadstat
import pytest

from src.ingest import ehs


def _write_fake_sav(path):
    df = pd.DataFrame({"serialno": [1, 2, 3], "fakedamp": [1, 2, -9], "fakewt": [1500.5, 2200.0, 1800.25]})
    pyreadstat.write_sav(
        df,
        str(path),
        column_labels={"serialno": "Case identifier", "fakedamp": "Any damp problems", "fakewt": "Dwelling weight"},
        variable_value_labels={"fakedamp": {1: "Yes", 2: "No", -9: "Unknown"}},
    )


@pytest.fixture
def raw_dir(tmp_path):
    raw = tmp_path / "raw" / "ehs"
    # Year 2022: plain extracted .sav
    (raw / "2022" / "spss").mkdir(parents=True)
    _write_fake_sav(raw / "2022" / "spss" / "physical_fake.sav")
    # Year 2018: zipped, as downloaded from the UK Data Service
    (raw / "2018").mkdir(parents=True)
    _write_fake_sav(tmp_path / "derived_fake.sav")
    with zipfile.ZipFile(raw / "2018" / "UKDA-0000-spss.zip", "w") as zf:
        zf.write(tmp_path / "derived_fake.sav", "UKDA-0000-spss/spss/derived_fake.sav")
    return raw


def test_dictionary_and_search(raw_dir, tmp_path):
    out = tmp_path / "dict.csv"
    df = ehs.build_dictionary(raw_dir, out)

    assert out.exists()
    assert set(df["year"]) == {"2018", "2022"}  # zip was extracted and year taken from folder
    assert len(df) == 6  # 3 variables x 2 files

    hits = ehs.search("damp", df)
    assert set(hits["variable"]) == {"fakedamp"}
    assert "1=Yes" in hits.iloc[0]["value_labels"]
    # Regex across value labels too
    assert set(ehs.search("Unknown", df)["variable"]) == {"fakedamp"}


def test_convert_keeps_codes_and_labels(raw_dir, tmp_path):
    out_dir = tmp_path / "interim"
    written = ehs.convert(raw_dir, out_dir)

    assert len(written) == 2
    parquet = out_dir / "2022" / "physical_fake.parquet"
    df = pd.read_parquet(parquet)
    assert df["fakedamp"].tolist() == [1, 2, -9]  # numeric codes kept, missing code preserved

    labels = json.loads(parquet.with_suffix(".value_labels.json").read_text(encoding="utf-8"))
    assert labels["value_labels"]["fakedamp"]["1"] == "Yes"
    assert labels["variable_labels"]["fakewt"] == "Dwelling weight"


def test_prefers_sav_over_duplicate_dta(raw_dir):
    sav = raw_dir / "2022" / "spss" / "physical_fake.sav"
    df, _ = pyreadstat.read_sav(str(sav))
    pyreadstat.write_dta(df, str(sav.with_suffix(".dta")))
    files = ehs.find_data_files(raw_dir)
    assert sav in files
    assert sav.with_suffix(".dta") not in files


def test_rejects_unsafe_zip(tmp_path):
    raw = tmp_path / "ehs" / "2022"
    raw.mkdir(parents=True)
    with zipfile.ZipFile(raw / "bad.zip", "w") as zf:
        zf.writestr("../escape.txt", "x")
    with pytest.raises(ValueError, match="Unsafe path"):
        ehs.extract_zips(tmp_path / "ehs")
