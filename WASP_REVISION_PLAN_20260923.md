# WASP revision: decision and analysis specification

Recorded 23 September 2026 before the new aligned-weather fits. This is a prospective record of this revision's calculations, not a preregistration of the study: earlier results are known. Preserve every listed analysis regardless of direction, uncertainty or estimability.

## Route and contribution

SCI environmental assessment; Research Manuscript for Water, Air, & Soil Pollution. Primary standard: interpretable pollution comparisons with traceable observations, comparator support and appropriate uncertainty. Apply sci-full-workflow only to environmental design, evidence and publication modules, not ML benchmarks or economic causal identification. The contribution is distinguishing monitored concentration differences relative to neither weather threshold from differences relative to a single component; multiple cities supply the evidence, not the novelty by themselves.

## Gate 1: measurement and historical provenance

Verify AQS local standard days against archived Open-Meteo offsets. Obtain UTC hourly ERA5 for 2019–2025 with boundary padding and reconstruct fixed local standard time days using EPA site GMT offsets. For temperature, wind speed, relative humidity and direction, assign instantaneous hourly values to their local date. For preceding-hour precipitation and radiation, assign each value to the local date of interval start. Require all 24 values; do not impute. Temperature maximum, scalar wind/RH means, precipitation sum, radiation energy sum and vector mean direction define daily weather. Freeze derived weather after completeness/offset tests, then reconstruct thresholds and all episode labels. Archive old-vs-new per-day and per-city changes; never overwrite old raw files.

Audit the old 72-event 2025 count against 32 under uniform ERA5, distinguishing demonstrated changes from unknown historical provenance. Remove the old satellite QA result from all current evidence; do not claim the old extraction has been validated.

## Gate 2: predefined comparisons

Maintain the 11 fixed cities, 25 km inclusion, April–October 2019–2024, AQS outcome/coverage rules, 2019–2022 threshold reference, site × year × month × weekday strata, and equal city-day/equal city weighting. Both episode versus neither and episode versus wind-only are co-primary descriptive comparisons; no causal or national-population inference.

| Analysis | Single change/purpose |
|---|---|
| Calendar only / weather adjusted | Base contrast, then RH/rain/radiation/direction conditioning |
| Direct support, neither | Only strata containing episode and neither; keep both-category rows for a binary comparison |
| Direct support, wind only | Only strata containing episode and wind-only; keep both-category rows for a binary comparison |
| Persistent wind-only comparator | Compare episodes to wind-only runs of at least two consecutive days; distinguish isolated wind-only days |
| Continuous wind adjustment | Within episode/wind-only support, add a prespecified 3-df natural spline in actual wind speed |
| Four weather states | No persistence condition; report all contrasts and additive interaction using consistent definitions |
| Temperature P85 | Wind P30, duration 2 days unchanged |
| Wind P20 | Temperature P80, duration 2 days unchanged |
| Duration 3 days | Temperature P80, wind P30 unchanged |
| All episode runs | Remove seven-day start-separation rule; this is definition sensitivity, not new validation |
| Coverage / aggregation | At least 172 qualifying warm days per site-year; equal site weights; city median |
| Time | Exclude 2020; synchronous leave-one-year; leave-one-city; 2019–2022 / 2023–2024; 2025 retrospective extension |

Support reporting includes strata, station-days, episode station-days, episode city-days, events and estimable cities. A day with any supporting site is not a fully supported site-day sample. A missing city contrast makes the 11-city mean unavailable; any available-city summary must explicitly name its changed target. Never replace nonidentifiable estimates with zero.

## Uncertainty and interpretation

The target is the equal-weight mean of 11 fixed city associations in the defined frame. The old cross-city t summary describes between-city dispersion and relies on approximate independent-city conditions; it does not guarantee 95% coverage for a fixed heterogeneous city estimand. Report it as a cross-city summary interval, not a nationally representative confidence interval. Add synchronous year deletion estimates for both primary contrasts and the factorial interaction. Report the six estimates and delete-year jackknife diagnostic with its six-block assumptions, without selecting an interval because it is narrower or excludes zero. Retain 5000 hierarchical/synchronous bootstrap diagnostics, seed 20260923, explicitly conditional on estimability; record failures for every contrast. No bootstrap rejection replacement. A single year receives no temporal interval.

## Environmental descriptions and writing

Report city-day mean of available sites before descriptive summaries, preserving equal city-day weighting. Provide by-city/weather-class count, mean, median, quartiles, temperature/wind and weather/persistence distributions. Obtain EPA site/monitor metadata rather than guessing site types. Main figures: site geography, city contrasts (both comparators), sensitivity (both comparators). Phases are secondary and, if retained, belong in integrated appendix rather than recovery claims. Core missing-support, uncertainty and exploratory limitations remain in the main text.

## Resources, execution and deliverables

D drive checked: approximately 393 GiB free; E approximately 299 GiB free. CPU analysis, no paid API/ML training. Expected new raw weather/metadata below 0.5 GB; outputs below 2 GB excluding document renders. New downloads only in E:/AcademicData/urban_no2_recovery_scs/raw/wasp_20260923; scripts/results/temp on D. Original archives are read-only. Use outcome-blind audits first, then complete all model specifications, then build article specification and rewrite. Authoritative manuscript, checked DOCX/PDF, WASP cover letter, issue-resolution record and new public version; preserve v1.0.0. No journal submission or editorial contact authorized by this revision request.

Current stage: time alignment audit pending; final submission readiness not yet reassessed.
