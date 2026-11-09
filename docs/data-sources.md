# Data sources

Checked 2026-11-09. ✅ = downloaded into `data/raw/`, ⏳ = needs manual download (sign-in required).

## 1. English Housing Survey (EHS): Housing Stock Data ⏳
- **Where:** UK Data Service catalogue (search "English Housing Survey Housing Stock Data"). A free account is required.
- **Which version:** the **End User Licence (EUL)** editions (not "Special Licence Access", which needs a separate application).
- **Format:** choose **SPSS (.sav)** or **Stata (.dta)**. Both load with `pyreadstat`.
- **Save to:** `data/raw/ehs/<year>/`

### ⚠️ Rules for picking years
- Each stock dataset covers **two overlapping survey years** (e.g. "2022" = Apr 2021–Mar 2023). **When pooling, use only odd years or only even years**, otherwise homes get counted twice.
- **Avoid 2020 and 2021.** COVID stopped internal inspections in 2020–21, so damp may not be recorded for those cases.
- **Recommended:** even years **2018 + 2022** (add 2016 if more positive cases are needed), or odd years **2019 + 2023** (add 2017). Pick whichever set has the damp variables in the EUL.
- The EUL contains **derived variables only**. Check the data dictionary (in the `mrdoc` folder of each download) for damp, mould and condensation variables **before** committing to a set of years.
- Use the weights supplied with each dataset (two-year weights). Record which weight variable is used here.

## 2. EPC: domestic certificates (England & Wales) ✅
- **Downloaded:** `data/raw/epc/domestic-csv.zip` (7.9 GB, 38 CSVs, ~98 GB uncompressed). Only the 19 `certificates-YYYY.csv` files (2008–2026) are used; `recommendations-*` are ignored.
- **Converted:** `src/ingest/epc.py` streams them straight out of the zip into `data/interim/epc/certificates_YYYY.parquet` (all columns as strings, address lines dropped). Result: 30.5M certificates, ~2.3 GB, in ~4 min.
- **Profile (checked 2026-11-09):**
  - 20.1M distinct UPRNs; 1.4% of certificates have no UPRN (excluded).
  - England: 29.0M certificates. Latest certificate per UPRN, **social rented = 2.86M homes** (~70% of England's ~4m social homes).
  - `tenure` values vary in case (`rented (social)` / `Rented (social)`), so lower-case before filtering. **22% of the latest certificates have missing or unknown tenure** (mostly older certificates), so some social homes are missed. Report this as a coverage limitation.
  - The latest certificates of social homes date from 2012–2026, mostly 2021+. Older ones may not reflect later retrofit.
  - Key fields (age band, built form, walls, heating, SAP, postcode) are fully populated for social homes, but check for "NO DATA!" or "INVALID!" placeholder values when cleaning.
  - **There's no LSOA column.** `local_authority` uses pre-2023 codes for some areas (e.g. the old Cumbria and North Yorkshire districts). Map postcode → LSOA 2021 with a postcode lookup (see below), then take the LA code from the IMD file.
- **Postcode → LSOA:** see section 5. **99.98% of social homes match an LSOA.**

## 5. Postcode → OA/LSOA/MSOA/LAD lookup (May 2026) ✅
- **Publisher:** ONS Open Geography Portal, *Postcode to OA (2021) to LSOA to MSOA to LAD (May 2026) Best Fit Lookup in the UK* (ArcGIS item `2713c3a627454ff88add814226264d77`)
- **Downloaded:** `data/raw/postcodes/PCD_OA21_LSOA21_MSOA21_LAD_MAY26_UK_LU.zip` (22.4 MB; one 417 MB CSV inside)
- **Converted:** `src/ingest/postcodes.py` → `data/interim/postcode_lookup.parquet` (2.73M postcodes including terminated ones, 33 MB). Join on `pcd_key` (upper-case, no spaces).
- **Match results (social rented homes, latest certificate per property, England):**
  - 2,855,846 homes, of which **2,855,271 (99.98%) are matched to an LSOA**. 7,527 match via retired postcodes. The ~575 unmatched are mostly new-build postcodes newer than the lookup.
  - 32,746 LSOAs contain social homes (all but 2 are in IMD 2025). Median 55 homes per LSOA.
  - ⚠️ **5,140 LSOAs (16%) have fewer than 10 social homes**, so they'll be suppressed on LSOA maps.
  - **Decision (2026-11-09): MSOA is the default small-area map level.** All 6,856 England MSOAs contain social homes (median 320, 10th percentile 93), and only 28 have fewer than 10. LSOA remains available as a detail view.
- **Licence:** Open Government Licence v3.0. Contains OS data © Crown copyright and database right; Royal Mail data © Royal Mail copyright and database right; National Statistics data © Crown copyright and database right.

### How it was obtained (EPC)
- **Where:** [Get energy performance of buildings data](https://get-energy-performance-data.communities.gov.uk/), the official GOV.UK service that replaced `epc.opendatacommunities.org`.
- **Access:** sign in with **GOV.UK One Login** (free) to download bulk CSVs. A developer API is also available.
- **What to get:** domestic certificates (the certificates file; the recommendations file isn't needed). Start with one region or local authority if that option is offered. Otherwise get the full file and filter it with DuckDB.
- **Save to:** `data/raw/epc/`
- **Note:** the file includes expired and replaced certificates, so keep the latest per property in the loader.

## 3. English Indices of Deprivation 2025 ✅
- **Downloaded:** `data/raw/imd/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv` (9.44 MB, 33,755 rows × 56 columns)
- **Key columns:** `LSOA code (2021)`, `Local Authority District code (2024)` (note: **2024** LA codes), `Index of Multiple Deprivation (IMD) Score`, and the rank and decile columns.
- **Publisher:** MHCLG, [GOV.UK release page](https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025), published 30 Oct 2025, LSOA files corrected 17 Nov 2025.
- **File used:** *File 7: All ranks, scores, deciles and population denominators* (CSV, 9.44 MB). This one file contains the IMD score, rank and decile, the domain scores, and the LSOA → local authority codes.
- **Erratum:** LSOA E01027305 belongs to West Northamptonshire (E06000062), not Cherwell. The corrected files fix this. Use the v2 LA summary files if any are needed.
- **Licence:** Open Government Licence v3.0
- **Save to:** `data/raw/imd/`

## 4. LSOA boundaries (December 2021, BGC V5) ✅
- **Downloaded:** `data/raw/boundaries/LSOA_2021_EW_BGC_V5.gpkg` (47.8 MB, 35,672 LSOAs in England & Wales, CRS EPSG:27700 British National Grid). Filter to codes starting `E` for England (33,755). All 33,755 IMD LSOA codes match.
- **Columns:** `LSOA21CD`, `LSOA21NM`, `BNG_E`, `BNG_N`, `LAT`, `LONG`, `geometry`
- **Publisher:** ONS Open Geography Portal ([data.gov.uk listing](https://www.data.gov.uk/dataset/lower-layer-super-output-areas-december-2021-boundaries-ew-bgc-v5))
- **Format:** GeoPackage (England & Wales, generalised 20 m, clipped to coastline). The listing gives the dataset as ~79 MB.
- **Local authority boundaries:** don't download them separately. Build them by **dissolving LSOAs by the LA code in the IMD file**, so the map and data always use the same LA definitions.
- **Licence:** Open Government Licence v3.0. Contains OS data © Crown copyright and database right.
- **Save to:** `data/raw/boundaries/`

## Attribution (for README / dashboard footer)
- Contains public sector information licensed under the Open Government Licence v3.0.
- Contains OS data © Crown copyright and database right [year].
- English Housing Survey data: cite as instructed on each UK Data Service study page.
