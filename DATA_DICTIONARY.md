# Derived inputs and source fields

## Weather city-days

`data/weather/weather_daily.csv` has one row per `city` and `date`: 11 cities × 2,557 dates, 2019–2025. `date` is the EPA AQS fixed local standard date, not UTC and not a daylight-saving civil date.

| Field | Unit | Construction |
|---|---|---|
| temperature_2m_max | °C | Maximum of 24 instantaneous hourly temperatures |
| wind_speed_10m_mean | km/h | Scalar mean of 24 instantaneous hourly wind speeds |
| relative_humidity_2m_mean | % | Mean of 24 instantaneous relative humidities |
| wind_direction_10m_dominant | degrees | Speed-weighted vector/circular direction, atan2(mean(speed × sin(direction)), mean(speed × cos(direction))) modulo 360; not a modal wind direction |
| precipitation_sum | mm | Sum of the 24 preceding-hour intervals whose starts fall in the local date |
| shortwave_radiation_sum | MJ/m² | Sum of the same 24 hourly mean radiation values in W/m², multiplied by 0.0036 |

Hourly JSON `time` values are UTC. Retained hourly fields are `temperature_2m`, `wind_speed_10m`, `relative_humidity_2m`, `precipitation`, `shortwave_radiation` and `wind_direction_10m`; their exact original units are checked against the source metadata. The hourly range includes one day of padding at both ends. Source response hashes refer to the unchanged complete JSON bytes.

## NO2 station-days

`data/stations/station_daily.csv` has one row per `city`, `station_id`, `date` and 138,303 rows across all months in 2019–2025. It is not the restricted warm-season model panel.

| Field | Meaning |
|---|---|
| city | Fixed city assignment using the listed centre and 25 km radius |
| station_id | Zero-padded state–county–site identifier; preserve it as text |
| date | AQS Date Local, local standard date |
| observation_count | Sum of weights used across retained collocated instruments; each instrument uses its observation count, with the documented minimum/fallback weight of one |
| n_pocs | Number of distinct retained parameter occurrence codes (instruments), not number of geographic sites |
| min_observation_percent | Minimum daily observation coverage percentage among the retained instruments |
| latitude, longitude | Aggregated retained site coordinates in degrees |
| distance_km | Haversine distance to the fixed city centre |
| no2_ppb | Observation-count-weighted mean of retained instrument daily NO2 means, parts per billion |

The daily input is unchanged from the prior audited station reconstruction; it is not interpolated and the weather rewrite does not alter NO2 dates or values. Native national AQS files are outside the compact package; their uncompressed CSV hashes and original ZIP download URLs are separately documented.

## Metadata and model outputs

EPA `GMT Offset` supplies the fixed city standard offset after checking every included site and within-city agreement. Site and monitor metadata are snapshots; land use, setting, operating dates and agency fields are not assumed to provide unchanged annual historical classifications.

`results/model_summary.csv` contains the 20-model, 98-contrast matrix, estimable-city counts, missing-city names, cross-city summaries, temporal diagnostics and all attempted/valid/failed bootstrap counts. Blank unavailable values are not zeros. `*_bootstrap_draws.npz` retains attempted draws including NaNs. `*_sufficient_statistics.npz` records model blocks used by the saved-result audit. `*_selected_station_days.csv` and `*_selected_strata.csv`, where generated, document restricted comparator samples. Consult the model specifications, thresholds, event manifests and support tables together; weather events, observed events and estimable contrasts are different denominators.
