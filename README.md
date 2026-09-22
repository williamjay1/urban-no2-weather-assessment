# Urban nitrogen dioxide and compound weather

Version 1.0.0 supports **Urban Nitrogen Dioxide During Compound Heat and Low Wind Conditions**, Junjie Zhang. It contains the actual derived environmental observations, analysis scripts and complete model summaries used in the revised assessment, not simulated example data.

This is a retrospective, exploratory environmental association study, not a preregistered or causal analysis. The sample comprises 11 United States cities, April–October 2019–2024, with a retrospective 2025 extension. The source record spans 2019–2025. All primary, component and sensitivity contrasts are retained, including uncertain estimates. No unverified satellite quality-sensitivity result is used.

## Main result

The weather-adjusted equal-city episode contrast with neither-threshold days is **3.33 ppb (approximate 95% interval 2.17–4.49)**. The episode contrast with low wind alone is **0.46 ppb (−0.48–1.40)**. These different comparisons must not be conflated. The primary model uses 69,326 station-days, 62 monitoring sites and 195 episodes. Direct ordinary-weather support exists for 406 of 577 episode days and at least one day in 178 episodes. The full model is not a collection of 195 directly matched pairs.

Intervals in the manuscript are approximate cross-city t intervals (10 degrees of freedom), assuming approximately independent city estimates. Individual-city intervals, when estimable, use a delete-one-year jackknife. Bootstrap quantiles are **conditional on estimability** and retain failure counts; they are not presented as unconditional confidence intervals. See `provenance/analysis_plan.md` for the retrospective design and documented interval-reporting amendment.

## Reproduce from the included data

Tested with Python 3.12 on Windows; scripts use portable paths and no credentials. A new directory is recommended. Installing the pinned libraries may require platform-compatible wheels.

```bash
python -m pip install -r requirements.txt
python scripts/calendar_station_analysis.py --self-test
python scripts/calendar_station_analysis.py --input-root data --output reproduced_results --bootstrap 5000
python scripts/verify_reproduction.py --reference results --reproduced reproduced_results --report reproduced_results/verification.json
python scripts/make_revision_figures.py --results reproduced_results --output reproduced_figures
```

The full analysis writes all specifications, not just the main estimate. `model_summary.csv` is the source for the abstract and pooled result tables. `*_city_estimates.csv` contains city-level results. `episode_manifest.csv` records weather-defined events; its 2025 count is 32, of which 31 have qualifying surface measurements. Large expanded model panels are generated during reproduction but omitted from the release because they are reconstructed from the included inputs.

## Rebuild the derived inputs

Download and unzip the seven EPA files `daily_42602_2019.zip` through `daily_42602_2025.zip` using the exact URLs in `provenance/source_manifest.csv`. Place their CSV files in one source directory. They are national files and are not included in this compact release. Original file SHA-256 values identify the versions used; a later EPA download may have changed. Do not silently treat changed source versions as identical.

The eleven weather API responses used here are included under `data/weather_source_responses/`; they are attributed to Open-Meteo and ERA5/Copernicus. Request URLs, units, timezones, retrieval timestamps and checksums are in `provenance/weather_download_audit.json`. The service was explicitly asked for ERA5, not automatic model blending.

```bash
python scripts/build_derived_inputs.py --aqs-directory /path/to/aqs_csvs --weather-json-directory data/weather_source_responses --output rebuilt_data
python scripts/verify_reconstruction.py --reference data --rebuilt rebuilt_data --report rebuilt_data/verification.json
python scripts/calendar_station_analysis.py --input-root rebuilt_data --output rebuilt_results --bootstrap 5000
```

Reconstruction selects one-hour daily records for the NO2 1-hour 2010 standard, ppb units, at least 75% observation coverage, and monitoring locations within 25 km of the listed centres. It deduplicates alternative exceptional-event records and combines collocated instruments using observation-count weights. No measurements are imputed. The script never writes to the source files.

## Files and provenance

- `data/stations/station_daily.csv`: 138,303 observed site-days, all months in 2019–2025; 63 sites across the whole record, 62 in the primary warm-season sample.
- `data/weather/weather_daily.csv`: 28,127 complete city-days and six weather variables.
- `data/weather_source_responses/`: unchanged API responses used for reconstruction.
- `provenance/`: city centres, station coverage, source versions, weather download record, analysis plan and reproduction audits.
- `results/`: thresholds, episode and support manifests, all model estimates, leave-year estimates, rank/uncertainty diagnostics.
- `figures/`: three original scientific figures, supplied as vector SVG/PDF/EPS and native 1200 dpi PNG.
- `SHA256SUMS.json`: checksums of release files (excluding itself and Git metadata).

The historical matched-station audit and matching candidate funnel are retained only as provenance. They do not define the current primary estimate. The previous across-month matching scheme and event-end subtraction endpoint are not used in the revised model.

## Availability and responsible interpretation

Release URL: https://github.com/williamjay1/urban-no2-weather-assessment/releases/tag/v1.0.0

This is a public versioned GitHub release, not a claim of a repository DOI or permanent institutional preservation. The attached downloadable package and checksum file identify the version supporting the manuscript. Data are environmental observations, not participant data. The study does not estimate personal exposure, health effects, causal heat effects or a universal recovery time.

AI assistance included analysis redesign, programming, checks, figures and manuscript drafting; scientific responsibility remains with the author. See `LICENSE` for code and `DATA_LICENSE.md` for source attribution and data conditions.
