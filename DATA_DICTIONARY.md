# Data dictionary

Dates are local calendar dates in ISO 8601 format. Missing fields in CSV output represent unavailable observations or nonestimable quantities, never zero. NO2 units are ppb.

## station_daily.csv

| Field | Meaning |
|---|---|
| city | Fixed named urban domain |
| station_id | Zero-padded AQS state-county-site identifier; retain as text |
| date | AQS Date Local |
| observation_count | Sum of valid hourly observation counts across retained occurrence codes |
| n_pocs | Number of distinct collocated parameter occurrence codes |
| min_observation_percent | Lowest reported observation percentage among retained codes |
| latitude, longitude | Mean reported instrument coordinates within the site-date |
| distance_km | Great-circle distance from the fixed centre; Earth radius 6371.0088 km |
| no2_ppb | Observation-count-weighted mean across instruments at the site-date |

The source pollutant-standard field is a row-selection criterion, not a claim that the outcome is an hourly maximum. The outcome is the daily arithmetic mean from the selected one-hour measurement record.

## weather_daily.csv

| Field | Unit / meaning |
|---|---|
| city, date | Join keys; one row per city-date |
| temperature_2m_max | °C, daily maximum |
| wind_speed_10m_mean | km/h, daily mean |
| relative_humidity_2m_mean | %, daily mean |
| precipitation_sum | mm per day |
| shortwave_radiation_sum | MJ/m² per day |
| wind_direction_10m_dominant | degrees, daily dominant direction |

See original responses for the returned grid point, elevation, timezone and metadata. The query used explicit ERA5 and timezone=auto. Responses were checked against the previously frozen exposure series; every daily maximum temperature and mean wind value agreed.

## Model and support outputs

`episode_manifest.csv`: weather-defined sustained episodes, with city, start/end dates, duration and year. `sample_support_by_city.csv` and `episode_calendar_support.csv`: direct calendar comparison availability, not newly matched pairs. `thresholds.csv`: warm-season 2019–2022 quantiles. `spline_specifications.json`: weather-only knots, boundaries and bases. `analysis_audit.json`: input hashes, tests, counts and uncertainty roles.

`model_summary.csv`: one row per model and contrast. `estimate_ppb` is an equal-city mean. `ci_lower` and `ci_upper` are the approximate cross-city t limits described in `ci_method`. `bootstrap_conditional_lower/upper` and `synchronized_conditional_lower/upper` are diagnostic quantiles conditioned on rank-based estimability; accompanying valid/attempted counts must be used. An unavailable all-city contrast is kept as missing, not calculated from an arbitrary subset of cities. `leave_city_min/max` describe sensitivity point estimates rather than interval limits. Sample count fields refer to model observations. In the all-consecutive sensitivity, `episodes` (pooled file) and `n_episodes` (city file) preserve the original retained-event identifier count; use the exposure-day category counts or the weather reconstruction to identify the broadened run definition.

`*_city_estimates.csv`: city-specific coefficients and contrasts, design rank/condition, category support, and delete-one-year jackknife limits when at least three years and all leave-year fits identify the contrast. A 2025 city has no interannual jackknife interval. Missing intervals are intentional, not collapsed to a zero-width bar.

## Coverage audit

`station_manifest.csv` lists site coordinates, first/last dates and counts across all months. `station_year_coverage.csv` counts qualifying warm-season days; completeness is valid days divided by 214, and the core criterion is at least 172 dates. `aqs_filter_flow.csv` records national-to-urban selection and deduplication counts. `source_manifest.csv` hashes the original unzipped national CSVs. The historical audit describes the previous matched-window analysis only; it is not the current primary model.
