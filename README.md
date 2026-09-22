# Urban Nitrogen Dioxide During Compound Heat and Low Wind Conditions

Junjie Zhang · version 2.0.0 · verified release artifact.

This retrospective environmental association study concerns 11 fixed United States cities. It does not estimate causal effects, personal exposure, health effects, national population averages or a universal recovery time. Version 1.0.0 is preserved; this major revision rebuilds weather days from UTC hourly ERA5 to AQS local standard time and adds the WASP analysis specifications.

## Current scope

The offline input package contains unchanged hourly weather responses, EPA site/monitor metadata, derived NO2 observations and the main analysis's rebuilt weather reference. The portable reconstruction uses the exact `aggregate` function from `wasp_weather_alignment.py`, without its downloader or machine paths. All inputs have SHA-256 identities. No credentials or live API are needed to execute reconstruction.

The main source analysis now records completion of 20 model specifications and 98 pooled contrasts. Its 2025 weather calendar has **30** events after the new UTC reconstruction. The historical **32** belongs to the earlier uniform ERA5 daily version, not this version. Both direct binary comparisons have 10 estimable cities; the persistent low-wind comparison has 9; the 2025 episode extension has 10. These do **not** establish directly supported estimates for all 11 cities. An unavailable 11-city contrast must remain unavailable, not be replaced by an unlabelled available-city mean.

The statistical owner confirmed the frozen source hashes; completed source outputs and the three statistical scripts are included. Full independent model reproduction **passed**: 226 CSV files, 40 NPZ files and five scientific JSON files match exactly, including 6,342,487 numeric CSV cells and 7,642,280 array values. All three final figures and ten article tables have also been regenerated from the independent run and verified. Execution metadata differences are explicitly recorded. The version 2.0.0 artifact is complete and its local verification is **PASS**. The author's unpublished manuscript and submission files are deliberately excluded from this code/data package; their absence is not unfinished package work. Public-access verification and the actual release/tree links are maintained separately by the publishing owner.

## Offline weather reconstruction

Requires Python 3.12 and the versions in `requirements-weather.txt`. Dependencies are not bundled. Install them in advance, or use a previously obtained local wheel directory; installation may require internet, but reconstruction itself does not.

Run from the package directory:

```bash
python -m pip install -r requirements-weather.txt
python -B -m unittest discover -s scripts -p test_rebuild_weather.py
python -B scripts/rebuild_weather.py
python -B scripts/rebuild_weather.py --output reproduced_data --report reproduced_data/verification.json
```

The first reconstruction command verifies without writing. The second creates a fresh output directory and refuses to replace one that already exists. `--package-root` is optional; the script locates inputs relative to itself, independent of the working directory. The output contains rebuilt `weather/weather_daily.csv` and a byte-preserving copy of the included `stations/station_daily.csv`, ready for a later analysis run. Copying the derived NO2 table is not described as reconstructing it from national AQS files.

The verifier checks all 28,127 city-days × six weather fields against `data/weather/weather_daily.csv`, including keys, missingness, numerical differences and CSV byte identity. It independently obtains fixed offsets from the included EPA sites ZIP and compares them with the selected site metadata. The executed `provenance/weather_reconstruction_check.json` reports exact equality of all 168,762 values and of the complete CSV bytes. Eight abnormal-input/path-protection tests passed.

## Reproduce all statistical specifications

Use the frozen public entry point below: it supplies explicit input/output paths to the unchanged statistical source and disables Python-level network calls. The default input is the package's `data` directory; use `reproduced_data` to run the complete hourly-weather-to-statistics chain. It refuses an existing output directory. Do not invoke the statistical source's machine-specific historical defaults.

```bash
python -m pip install -r requirements.txt
python -B scripts/run_analysis_offline.py --input-root reproduced_data --output reproduced_results
python -B scripts/verify_analysis_reproduction.py --reference results --reproduced reproduced_results --report verification_runs/independent_analysis.json
```

For an offline installation with wheels already obtained for the platform, use `python -m pip install --no-index --find-links /path/to/wheels -r requirements.txt`. No wheels or Python runtime are bundled. The dependency list includes `packaging` and runtime dependencies, not just the five top-level scientific libraries. Standard Python invocation uses the installed environment; `-I` can hide packages installed in the Python user site and is not required.

The run executes all 20 models, including all 98 contrasts, all three 5,000-attempt bootstrap schemes, failed replicates and nonestimable city results. Approximate cross-city t intervals describe dispersion, not guaranteed coverage of a fixed heterogeneous-city mean. Whole-year jackknife/percentile diagnostics retain their few-year-block assumptions; percentiles are conditional on estimability. Missing fixed-11-city contrasts remain missing. No available-city pooled estimate is substituted.

The independent verifier checks every CSV cell, every NPZ array and all scientific JSON fields exactly; NaN locations must also match. It permits only explicitly documented execution-metadata differences (timestamps, timing, owner-confirmed source hashes and additional passing tests). The owner-authored `FINAL_CODE_FREEZE.json` is checked as source provenance rather than expected to be regenerated by a model run. The original fitted source is identified separately from the final portable/audit version in `provenance/analysis_staging.json`; all original non-`main` function ASTs were unchanged. Source-only execution snapshots/review text omitted from the compact results folder are named there, and the full original output inventory is retained as provenance.

The executed full replay passed all 15 statistical tests and reproduced the entire output matrix from the independently rebuilt weather plus the included derived NO2. Its saved-result audit checked 1,078 city contrasts and 1,470,000 saved replicate-contrast values, with zero error when reconstructing fixed-city synchronous replicates. See `provenance/analysis_reproduction_check.json` and `provenance/EXECUTION_NOTES.md`. This is an independent rerun in the existing documented environment, not a claim that a new clean environment or another operating system was tested. Frozen stage and execution logs describe the state at their creation, not subsequent public availability; `RELEASE_STATUS.json` records artifact completeness and local verification. Public verification is recorded separately by the publishing owner.

## Reproduce the final figures and tables

All research scripts that generate the released figures and tables are included: `wasp_station_map.py` (Figure 1 and site-metadata report), `wasp_result_figures.py` (Figures 2–3), and `wasp_article_tables.py` (Tables T1–T4, A1–A3 and B1–B3, plus the result ledger). Their release copies add package-relative paths, explicit input/output CLI arguments, output protection and local cache/network handling. Every original function AST is unchanged after the two documented table-input path substitutions; no statistics or plot geometry were changed. The generation code reads no external basemap, web service or unpublished full text.

```bash
python -B -m unittest discover -s scripts -p test_release_presentation.py
python -B scripts/reproduce_presentation.py --analysis reproduced_results --station-daily reproduced_data/stations/station_daily.csv --output reproduced_presentation
python -B scripts/verify_presentation_reproduction.py --reproduced reproduced_presentation --analysis reproduced_results --report verification_runs/independent_presentation.json
```

Use a fresh output directory. Each script also has its own `--help` and required `--output`; Figures 2–3 and tables accept `--analysis`, and Figure 1 accepts explicit station/site/city metadata paths. Matplotlib caches are placed in the reproduction output, or in package-local `verification_runs/matplotlib` when a plotting script is run directly; `MPLCONFIGDIR` may override this for a read-only package.

Executed verification: the ten Markdown tables, three native 1200 dpi PNGs and three 240 dpi preview PNGs are byte-identical. All nine PDF/SVG/EPS vector files are identical after normalizing only their generation-date field. The scientific result ledger and site-metadata report also match, with only the enumerated execution timestamps, confirmed analysis-source/test metadata and hash-validated I/O locations differing. No numerical or pixel tolerance was used. Three regenerated previews were visually inspected; no clipped or overlapping text was observed. See `provenance/presentation_reproduction_check.json` and `REPRODUCTION_SUMMARY.md`.

## Day construction

Each city has 61,416 UTC hours from 31 December 2018 through 1 January 2026, including boundary padding. The retained local dates are 1 January 2019 through 31 December 2025 (2,557 days per city). Daily summer/winter clock changes are not applied: AQS fixed local standard time is used throughout.

- Temperature maximum, scalar wind-speed mean, relative-humidity mean and speed-weighted vector wind direction use instantaneous values assigned by local standard date.
- Precipitation and shortwave radiation refer to the preceding hour and are assigned by that interval's start. Radiation is converted from summed hourly W/m² values to MJ/m² using 0.0036.
- Every retained day requires 24 instantaneous and 24 accumulation values. Missing, repeated, unordered or non-hourly timestamps, altered hashes and incompatible units cause failure; nothing is imputed.

The city offsets are UTC−8 (Los Angeles, San Diego, Seattle), UTC−7 (Phoenix, Denver), UTC−6 (Houston, Dallas, Chicago), and UTC−5 (Atlanta, New York, Philadelphia). Source-specific records include request coordinates, returned grid coordinates, units and hashes. The original audit's `retrieved_utc` field is preserved, but the retrieval script can reuse cached files: it is not guaranteed to be the first network retrieval time. EPA metadata likewise lack a separately recorded first retrieval time.

## NO2 and provenance boundaries

The included derived table has 138,303 station-days and 63 sites across all months of 2019–2025. AQS one-hour daily observations use the NO2 1-hour 2010 standard, ppb units, at least 75% coverage and a 25 km city-centre radius. Alternative event records are deduplicated; collocated instruments are combined using observation-count weights. Source URLs and SHA-256 values in `provenance/source_manifest.csv` identify the **uncompressed national CSVs**, not the downloadable ZIPs. These national files are not bundled; a fresh download is not a prerequisite for the included-data analysis. Complete national-AQS-to-NO2 replay is a separate provenance boundary, not a claimed part of this weather verification.

Historical 72-versus-32 event counts and the unknown identity of the old weather model are described in `provenance/HISTORICAL_LINEAGE.md`. They do not prove a satellite QA repair. No old TROPOMI QA sensitivity, satellite agreement, event-end subtraction or recovery claim is supplied as current evidence.

## Contents and checksums

- `data/weather_hourly_utc/`: 11 unchanged Open-Meteo ERA5 response files.
- `data/aqs_metadata_sources/`: unchanged EPA site and monitor ZIPs.
- `data/weather/`, `data/stations/`: reference daily inputs.
- `scripts/`: offline reconstruction, full statistical analysis, every figure/table generator, tests, independent verifiers and local archive creation.
- `provenance/`: source URLs, input identities, offsets, audit semantics and execution reports.
- `results/`: 272 source result/provenance artifacts (226 CSV, 40 NPZ, six JSON), plus their checksum inventory; one JSON is the owner-authored code-freeze record.
- `figures/`: all three final figures as native PNG, preview PNG, PDF, SVG and EPS; Figure 1 also includes a descriptive metadata report.
- `tables/`: ten generated article tables and their numerical result ledger, not the author's full manuscript.
- `SHA256SUMS.json`: current package inventory, created after verification; not a publication claim.

Run `python -B scripts/verify_package.py` to check the frozen package inventory. Local reproduction folders (`reproduced_data`, `reproduced_results`, `reproduced_figures`, `reproduced_tables`, `reproduced_presentation`, `verification_runs`) and Python/Git caches are not distribution artifacts. The local ZIP is built from the inventory, not by recursively adding work folders:

```bash
python -B scripts/build_release_archive.py --archive ../urban-no2-weather-assessment-v2.0.0.zip
```

This refuses to overwrite an archive, includes the checksum inventory, checks every archived byte by SHA-256 after compression, and writes an adjacent `.zip.sha256` checksum file. It reports package/archive sizes, the largest file and both decimal 100 MB and binary 100 MiB file checks. This packaging command makes no network call, Git operation or publication. Public-access verification is performed separately by the publishing owner. Unpublished manuscript DOCX/PDF, cover letters and all `submission/` contents are excluded; the only distributed PDFs are the three figure vectors.

Weather data by [Open-Meteo](https://open-meteo.com/), using ERA5 information from ECMWF/Copernicus Climate Change Service. See `DATA_LICENSE.md` for attribution, transformations and source conditions. Code is MIT licensed; upstream data are not relicensed as MIT. `CITATION.cff` identifies the verified version 2.0.0 artifact using the unchanged title. No DOI, release date or unverified public URL is fabricated.
