# Historical event lineage, not current validation

The previous 2025 counts concern distinct historical input frames. A separate local audit reproduced the following combinations using the same minimum two-day duration, April–October season, inclusive temperature/wind comparisons and seven-day retained-start separation:

| 2025 weather values | Threshold values | Retained events |
|---|---|---:|
| Old archived weather | Old 2019–2022 thresholds | 72 |
| Explicit uniform ERA5 weather | Old thresholds | 54 |
| Old archived weather | Recomputed uniform ERA5 thresholds | 50 |
| Explicit uniform ERA5 weather | Recomputed uniform ERA5 thresholds | 32 |

Changing weather values and numerical thresholds demonstrably changes the counts. The percentile rules remained P80/P30, but numerical thresholds did not remain unchanged between versions. The new 32-event historical set was not simply a subset of the old 72: only three complete city/start/end intervals were shared. These are processing comparisons, not causal attributions of meteorological mechanisms.

The old 2019–2022, 2023–2024 and 2025 raw response files contain no preserved request URL, selected model field or first-retrieval record. The available local scripts did not establish the missing original request. Their concrete historical model identity is **unknown**; neither automatic blending nor a particular ERA5/ERA5-Land/IFS model transition is proved. Matching recorded timezone/offset labels in those older files do not establish correct AQS local-standard-day alignment.

The v2 reconstruction instead uses separately archived, explicitly requested UTC hourly ERA5 and EPA fixed standard offsets. Its completed source analysis reports **30** weather events in 2025. This number must not be replaced by the historical 32. Weather-defined events, events with qualifying NO2 and estimable contrasts have different denominators.

The historical four-input-combination audit is not rerun from this package: old response files are not bundled. Its report identity is recorded in `staging_record.json`. Neither that audit nor removing satellite results repairs or validates the former satellite QA extraction. No old satellite sensitivity is current supporting evidence.
