# Local independent reproduction summary

**Version 2.0.0 verified release artifact** · Artifact complete · Local verification PASS

Title: Urban Nitrogen Dioxide During Compound Heat and Low Wind Conditions.

## Executed results

| Layer | Independent check | Result |
| --- | --- | --- |
| Weather | 675,576 UTC hourly records → 28,127 local-standard-time city-days; six daily fields | All 168,762 values and complete reference CSV bytes exactly equal |
| NO2 input | 138,303 derived station-days, 63 sites across 2019–2025 | Original derived input bytes unchanged; national raw-AQS reconstruction not claimed |
| Analysis | 20 models, 98 contrasts; three schemes with 5,000 bootstrap attempts each | Complete independent execution; all 15 statistical tests passed |
| Statistical artifacts | 226 CSV + 40 NPZ + five scientific JSON files | All 271 exact; 6,342,487 numeric CSV cells and 7,642,280 array values, including missingness |
| Saved-result audit | 1,078 city contrasts; 294 scheme-by-contrast diagnostics; 1,470,000 replicate-contrast values | Passed; fixed-city synchronous reconstruction maximum absolute error 0 |
| Article tables | T1–T4, A1–A3, B1–B3 and numerical result ledger | Ten Markdown tables byte-identical; all scientific ledger fields exact |
| Figures 1–3 | Six PNGs, nine PDF/SVG/EPS vectors and Figure 1 metadata report | PNGs byte-identical; vector files identical except generation dates; scientific metadata exact |
| Presentation checks | Four portability/comparison regressions plus three preview visual inspections | Passed; no text overlap or clipping observed |

Analysis comparisons use exact equality, not a numerical tolerance. The weather report additionally records a tolerance diagnostic, but its actual outcome is bit/byte equality. Deliberately permitted differences are listed in the verification reports: execution timestamps/timing, owner-confirmed analysis-script identity and expanded passing tests, figure generation dates, and hash-validated input/output paths in the station metadata report. The source-only code-freeze record is verified as provenance, not miscounted as model-generated output.

## Scientific reporting boundaries

The rebuilt calendar contains 189 qualifying episodes in 2019–2024 and **30 in 2025**. Thirty-two refers to the previous ERA5 daily construction, not this version. Both direct binary comparisons identify only 10 of the 11 city targets; persistent low-wind comparison identifies 9; the 2025 episode extension identifies 10. The three-day-duration episode model identifies 9. Missing fixed-11-city targets remain NA; no available-city mean is substituted. Failed bootstrap replicates remain in the saved arrays and diagnostics. Conditional bootstrap percentiles and cross-city t dispersion summaries are not relabelled as unconditional guaranteed-coverage intervals.

The study is observational and noncausal. This package makes no new satellite QA, recovery-time or historical old-model identification claim. The old 72-event provenance limitations remain explicit in `provenance/HISTORICAL_LINEAGE.md`.

## Handoff and exclusions

All required inputs for the included-data analysis and figure/table generation are packaged. Hourly weather can be rebuilt offline; no credentials, live API, external basemap, machine-specific research directory or unpublished manuscript is required. Python and dependency wheels are not bundled. Verification used the documented installed environment, not a newly created environment or a second operating system.

The author's unpublished full text, manuscript DOCX/PDF, cover letters and `submission/` files are intentionally excluded. This is a completed code/data package, not a missing-manuscript package. The only distributed PDFs are the three figures. Version 1.0.0 and original E-drive sources were not modified.

`SHA256SUMS.json` identifies every distributed file. The ZIP builder uses this inventory and checks every archived member again, excluding local reproduction/cache directories. Public release and public-access/link verification are performed separately by the publishing owner. Local reproduction reports establish computational agreement, not external link accessibility; the static artifact metadata remain valid after publication.
