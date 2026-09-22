# Data attribution and conditions

Official policy pages checked on 23 September 2026. The code's MIT license does not relicense upstream observations or metadata.

## Weather

[Weather data by Open-Meteo](https://open-meteo.com/). The included JSON files are unmodified API responses requested with `models=era5`. [Open-Meteo's data license](https://open-meteo.com/en/licence) is [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/): retain attribution, the license link and identification of changes. Its API service terms and free-service access restrictions are separate from the data license; see [service terms](https://open-meteo.com/en/terms). The API server's AGPL software license is not the license of these data; no server code is copied here.

Underlying weather information: ERA5, ECMWF / Copernicus Climate Change Service (C3S), as served by Open-Meteo. [ERA5 dataset information](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview). Daily fields in this package are author-created transformations: fixed EPA-standard-time day assignment, preceding-hour interval reassignment for precipitation/radiation, aggregation, radiation-unit conversion and vector wind-direction calculation. They are not untouched native ERA5 daily outputs. Preserve both Open-Meteo and underlying ERA5/C3S attribution. No endorsement or responsibility for these transformations by the source providers is implied.

## EPA AQS observations and metadata

Source: United States Environmental Protection Agency, Air Quality System / AirData, and contributing monitoring agencies. Exact source URLs and source-specific hashes are in `provenance/source_manifest.json` and `provenance/source_manifest.csv`. The latter hashes refer to uncompressed national CSVs, which are not bundled. EPA metadata ZIPs and the derived station-day table are included.

[EPA's disclaimers](https://www.epa.gov/web-policies-and-procedures/epa-disclaimers) describe scientific/educational distribution and use, possible document-specific rights, warranty limits and non-endorsement. That page is a catalogue of disclaimers and not an affirmative blanket CC BY or MIT license for every contributing agency's material. We therefore retain EPA source conditions and attribution rather than assigning a fabricated SPDX data license or claiming ownership of all upstream observations. Users remain responsible for any source-specific rights applicable to their use. EPA and the contributing agencies do not endorse this assessment.

## Author-created products

The author's contributions to derived tables, figures and data documentation are offered under CC BY 4.0 to the extent copyright applies and the author holds those rights, consistently with v1.0.0. Credit Junjie Zhang and this work; this grant does not remove upstream conditions or create ownership of public-domain facts. Software is separately MIT licensed. No guarantee is made of regulatory completeness, health-assessment suitability, future source stability or unqualified validity of historical analyses.

The three final figures and their generating code are included and independently verified. The author's unpublished manuscript, cover letters and submission files are intentionally excluded from this code/data package. The author's grant for included research products does not distribute that unpublished full text.
