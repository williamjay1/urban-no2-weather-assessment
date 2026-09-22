# Station locations: descriptive metadata report

Generated (UTC): 2026-09-22T16:52:46+00:00

## Suggested caption

Monitoring locations. Panels read left to right: top row, US locator, Atlanta (ATL), Chicago (CHI), Dallas (DAL); middle row, Denver (DEN), Houston (HOU), Los Angeles (LA), New York (NY); bottom row, Philadelphia (PHL), Phoenix (PHX), San Diego (SD), Seattle (SEA). Abbreviations identify cities in the locator. The 62 sites have at least one valid daily observation in April–October 2019–2024; n gives site counts. Colors and shapes indicate EPA Location Setting. Crosses mark city reference coordinates and dashed circles indicate 25 km radii. Local panels share approximate east–north offsets, with north upward. Close pairs are annotated without moving coordinates. The locator uses longitude and latitude; no boundaries or basemap are shown.

## Selection and counts

Selected **62 unique sites in 11 cities**, contributing 69,458 unique site-days. Inclusion requires at least one row dated in April–October of 2019–2024, a finite no2_ppb value and a positive finite observation_count in the supplied revision station_daily.csv. This is a union across the study window, not a claim that each site operated throughout all six years. No additional completeness rule or new measurement-quality filter was imposed.

The daily table contains 63 sites across all dates, and the metadata table contains 63 rows. All 62 selected sites have unique matching metadata and valid coordinates. In-window rows rejected by the finite-value/count check: 0.

| City | Sites | Site-days |
| --- | --- | --- |
| Atlanta | 3 | 3704 |
| Chicago | 4 | 4663 |
| Dallas | 4 | 4551 |
| Denver | 5 | 6049 |
| Houston | 10 | 11010 |
| Los Angeles | 8 | 9254 |
| New York | 9 | 10749 |
| Philadelphia | 6 | 5982 |
| Phoenix | 6 | 5991 |
| San Diego | 5 | 5057 |
| Seattle | 2 | 2448 |

Excluded sites in the daily input:

| City | Site ID | First available day | Last available day | Available days |
| --- | --- | --- | --- | --- |
| Seattle | 53-033-0057 | 2025-01-08 | 2025-12-31 | 344 |

## Observation coverage

April–October contains 214 calendar days per year, giving 1,284 days across 2019–2024. A city's covered day has at least one selected site observation. Daily site counts include every study-window date, including zero-site days. The fixed-network site-day fraction divides observed site-days by selected sites × 1,284. This is a descriptive common-window denominator, not regulatory completeness or a claim that every site was scheduled to operate throughout the window.

| City | Covered days / 1,284 | Days with no sites | Daily sites min / median / max | Site-days / fixed network (%) |
| --- | --- | --- | --- | --- |
| Atlanta | 1284 | 0 | 1 / 3 / 3 | 96.16% |
| Chicago | 1284 | 0 | 1 / 4 / 4 | 90.79% |
| Dallas | 1284 | 0 | 1 / 4 / 4 | 88.61% |
| Denver | 1284 | 0 | 2 / 5 / 5 | 94.22% |
| Houston | 1284 | 0 | 1 / 9 / 10 | 85.75% |
| Los Angeles | 1284 | 0 | 5 / 7 / 8 | 90.09% |
| New York | 1284 | 0 | 4 / 8 / 9 | 93.02% |
| Philadelphia | 1284 | 0 | 2 / 5 / 5 | 77.65% |
| Phoenix | 1284 | 0 | 3 / 5 / 5 | 77.76% |
| San Diego | 1284 | 0 | 1 / 4 / 5 | 78.77% |
| Seattle | 1282 | 2 | 0 / 2 / 2 | 95.33% |

Distinct sites with observations in each April–October season:

| City | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
| --- | --- | --- | --- | --- | --- | --- |
| Atlanta | 3 | 3 | 3 | 3 | 3 | 3 |
| Chicago | 4 | 4 | 4 | 4 | 4 | 4 |
| Dallas | 4 | 4 | 4 | 4 | 4 | 4 |
| Denver | 5 | 5 | 5 | 5 | 5 | 5 |
| Houston | 9 | 9 | 10 | 10 | 10 | 10 |
| Los Angeles | 7 | 8 | 8 | 7 | 7 | 7 |
| New York | 9 | 9 | 9 | 9 | 8 | 8 |
| Philadelphia | 5 | 5 | 5 | 5 | 5 | 6 |
| Phoenix | 5 | 4 | 5 | 5 | 5 | 5 |
| San Diego | 4 | 4 | 4 | 4 | 5 | 5 |
| Seattle | 2 | 2 | 2 | 2 | 2 | 2 |

Network totals by season:

| Year | Distinct sites | Observed site-days |
| --- | --- | --- |
| 2019 | 57 | 11220 |
| 2020 | 57 | 11810 |
| 2021 | 59 | 11721 |
| 2022 | 58 | 11719 |
| 2023 | 58 | 11303 |
| 2024 | 59 | 11685 |

## Metadata category distributions

Counts below use the 62 selected sites (one vote per site). EPA text is retained exactly; categories describe the supplied site metadata snapshot, not historical category stability or a citywide property. Land Use and Location Setting are separate fields. Missing includes blank values and explicit NA/N/A/NaN/null/none/unknown/not reported tokens; a blank field need not imply an error.

### Location Setting

Known: 62; missing: 0.

| Category | Sites | Percent of 62 |
| --- | --- | --- |
| RURAL | 1 | 1.6% |
| SUBURBAN | 22 | 35.5% |
| URBAN AND CENTER CITY | 39 | 62.9% |

### Land Use

Known: 62; missing: 0.

| Category | Sites | Percent of 62 |
| --- | --- | --- |
| AGRICULTURAL | 1 | 1.6% |
| BLIGHTED AREAS | 1 | 1.6% |
| COMMERCIAL | 24 | 38.7% |
| INDUSTRIAL | 6 | 9.7% |
| MILITARY RESERVATION | 1 | 1.6% |
| MOBILE | 4 | 6.5% |
| RESIDENTIAL | 25 | 40.3% |

### GMT Offset

Known: 62; missing: 0.

| Category | Sites | Percent of 62 |
| --- | --- | --- |
| -5 | 18 | 29.0% |
| -6 | 18 | 29.0% |
| -7 | 11 | 17.7% |
| -8 | 15 | 24.2% |

### gmt_offset_hours

Known: 62; missing: 0.

| Category | Sites | Percent of 62 |
| --- | --- | --- |
| -5 | 18 | 29.0% |
| -6 | 18 | 29.0% |
| -7 | 11 | 17.7% |
| -8 | 15 | 24.2% |

### Datum

Known: 62; missing: 0.

| Category | Sites | Percent of 62 |
| --- | --- | --- |
| NAD83 | 22 | 35.5% |
| WGS84 | 40 | 64.5% |

### Extraction Date

Known: 62; missing: 0.

| Category | Sites | Percent of 62 |
| --- | --- | --- |
| 2026-06-26 | 62 | 100.0% |

### Owning Agency

Known: 62; missing: 0.

| Category | Sites | Percent of 62 |
| --- | --- | --- |
| Arizona Department Of Environmental Quality | 1 | 1.6% |
| Colorado Department of Public Health And Environment | 5 | 8.1% |
| Cook County Department of Environmental Control | 2 | 3.2% |
| Georgia Air Protection Branch Ambient Monitoring Program | 3 | 4.8% |
| Illinois Environmental Protection Agency | 2 | 3.2% |
| Maricopa County Air Quality | 5 | 8.1% |
| New Jersey State Department Of Environmental Protection | 7 | 11.3% |
| New York State Department Of Environmental Conservation | 4 | 6.5% |
| Pennsylvania Department Of Environmental Protection | 1 | 1.6% |
| Philadelphia Air Management Services | 3 | 4.8% |
| San Diego County Air Pollution Control District | 5 | 8.1% |
| South Coast Air Quality Management District | 8 | 12.9% |
| Texas Commission On Environmental Quality | 14 | 22.6% |
| Washington State Department Of Ecology | 2 | 3.2% |

## Metadata completeness

All non-key columns are counted separately; zero and negative GMT offsets are known values. Site Closed Date and meteorological-site fields can legitimately be blank. A GMT offset is reported as supplied and is not a date-specific daylight-saving-time conversion.

| Field | Known | Missing |
| --- | --- | --- |
| State Code | 62 | 0 |
| County Code | 62 | 0 |
| Site Number | 62 | 0 |
| Latitude | 62 | 0 |
| Longitude | 62 | 0 |
| Datum | 62 | 0 |
| Elevation | 62 | 0 |
| Land Use | 62 | 0 |
| Location Setting | 62 | 0 |
| Site Established Date | 62 | 0 |
| Site Closed Date | 3 | 59 |
| Met Site State Code | 3 | 59 |
| Met Site County Code | 3 | 59 |
| Met Site Site Number | 3 | 59 |
| Met Site Type | 29 | 33 |
| Met Site Distance | 6 | 56 |
| Met Site Direction | 6 | 56 |
| GMT Offset | 62 | 0 |
| Owning Agency | 62 | 0 |
| Local Site Name | 62 | 0 |
| Address | 62 | 0 |
| Zip Code | 60 | 2 |
| State Name | 62 | 0 |
| County Name | 62 | 0 |
| City Name | 62 | 0 |
| CBSA Name | 62 | 0 |
| Tribe Name | 0 | 62 |
| Extraction Date | 62 | 0 |
| gmt_offset_hours | 62 | 0 |

## Seattle: actual selected site information

Seattle contributes two sites. Both have known EPA Location Setting, Land Use, GMT Offset, coordinates, datum and local site name. Both are URBAN AND CENTER CITY. Their distinct Land Use labels are reproduced as recorded; BLIGHTED AREAS is an EPA metadata value, not an inference about neighborhood conditions made for this figure.

Seattle observation coverage (same 1,284-day calendar denominator):

| Site ID | Observed days | Fraction of 1,284 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 53-033-0030 | 1209 | 94.16% | 210 | 213 | 199 | 200 | 194 | 193 |
| 53-033-0080 | 1239 | 96.50% | 211 | 214 | 212 | 214 | 205 | 183 |

| Field | 53-033-0030 | 53-033-0080 |
| --- | --- | --- |
| State Code | 53 | 53 |
| County Code | 033 | 033 |
| Site Number | 0030 | 0080 |
| Latitude | 47.597222 | 47.568236 |
| Longitude | -122.319722 | -122.308628 |
| Datum | WGS84 | WGS84 |
| Elevation | 15 | 105 |
| Land Use | BLIGHTED AREAS | RESIDENTIAL |
| Location Setting | URBAN AND CENTER CITY | URBAN AND CENTER CITY |
| Site Established Date | 2014-04-01 | 1979-06-04 |
| Site Closed Date | [MISSING] | [MISSING] |
| Met Site State Code | [MISSING] | [MISSING] |
| Met Site County Code | [MISSING] | [MISSING] |
| Met Site Site Number | [MISSING] | [MISSING] |
| Met Site Type | [MISSING] | ON-SITE MET EQUIP |
| Met Site Distance | [MISSING] | [MISSING] |
| Met Site Direction | [MISSING] | [MISSING] |
| GMT Offset | -8 | -8 |
| Owning Agency | Washington State Department Of Ecology | Washington State Department Of Ecology |
| Local Site Name | Seattle-10th & Weller | SEATTLE - BEACON HILL |
| Address | 10th & Weller | 4103 BEACON HILL S |
| Zip Code | 98104 | 98108 |
| State Name | Washington | Washington |
| County Name | King | King |
| City Name | Seattle | Seattle |
| CBSA Name | Seattle-Tacoma-Bellevue, WA | Seattle-Tacoma-Bellevue, WA |
| Tribe Name | [MISSING] | [MISSING] |
| Extraction Date | 2026-06-26 | 2026-06-26 |
| gmt_offset_hours | -8 | -8 |

Seattle-only known versus missing counts:

| Field | Known | Missing |
| --- | --- | --- |
| State Code | 2 | 0 |
| County Code | 2 | 0 |
| Site Number | 2 | 0 |
| Latitude | 2 | 0 |
| Longitude | 2 | 0 |
| Datum | 2 | 0 |
| Elevation | 2 | 0 |
| Land Use | 2 | 0 |
| Location Setting | 2 | 0 |
| Site Established Date | 2 | 0 |
| Site Closed Date | 0 | 2 |
| Met Site State Code | 0 | 2 |
| Met Site County Code | 0 | 2 |
| Met Site Site Number | 0 | 2 |
| Met Site Type | 1 | 1 |
| Met Site Distance | 0 | 2 |
| Met Site Direction | 0 | 2 |
| GMT Offset | 2 | 0 |
| Owning Agency | 2 | 0 |
| Local Site Name | 2 | 0 |
| Address | 2 | 0 |
| Zip Code | 2 | 0 |
| State Name | 2 | 0 |
| County Name | 2 | 0 |
| City Name | 2 | 0 |
| CBSA Name | 2 | 0 |
| Tribe Name | 0 | 2 |
| Extraction Date | 2 | 0 |
| gmt_offset_hours | 2 | 0 |

Excluded Seattle site 53-033-0057 (SEATTLE - DUWAMISH): Location Setting = SUBURBAN; Land Use = INDUSTRIAL; GMT Offset = -8. Its supplied observations run from 2025-01-08 to 2025-12-31, outside the 2019–2024 selection. Its SUBURBAN / INDUSTRIAL labels must not be attributed to the two selected Seattle sites.

## Coordinates, local geometry and limitations

City reference coordinates are read from the previous release's provenance/city_metadata.json. They are study reference points; this script does not assert that they are administrative centroids, downtown boundaries or population centers. Site coordinates come from city_site_metadata.csv and are cross-checked against all selected daily coordinates.

Offsets use R = 6371 km, x = R cos(latitude0) (longitude − longitude0) and y = R (latitude − latitude0), with angular differences in radians. x increases eastward and y northward. Local panels all span −28 to +28 km in each direction, have equal aspect, and draw a 25 km circle in this approximate coordinate system. This is a local equirectangular approximation, not a surveyed distance or an ellipsoidal geodesic projection. The locator has angular axes and must not be used to measure distance or area. No geographic boundaries, coastlines, roads, land cover or other unsupported basemap features are drawn.

Maximum selected-site spherical distance from its reference point: 24.040544 km. Maximum approximate radius: 24.045434 km. Maximum radial difference between the local approximation and spherical haversine: 12.578 m. All selected sites are within 25 km by both calculations and in the supplied daily-distance column.

Maximum metadata-to-daily coordinate separation: 0.000000 m. Sites with multiple coordinate pairs in the selected daily rows: 0. Maximum difference from the source daily radius: 0.033206 m.

The supplied coordinates include NAD83 and WGS84 datum labels. No datum transformation was performed; the coordinates are displayed as supplied for this city-scale locator. The approximation-error check does not quantify datum or source-coordinate uncertainty. Metadata is a snapshot, so the figure does not establish that the setting or land-use category was unchanged in every study year. Site density and category counts describe this selected monitoring network, not population exposure or representativeness of a whole city.

Pairs separated by less than 2 km receive a '2 sites' callout. Markers remain at their true plotted coordinates; no site is jittered, merged, dropped or moved. Some glyphs consequently overlap at print size.

| City | Site 1 | Site 2 | Separation (km) |
| --- | --- | --- | --- |
| Denver | 08-031-0026 | 08-031-0028 | 1.596 |
| New York | 36-081-0124 | 36-081-0125 | 0.474 |
| Philadelphia | 34-007-0002 | 34-007-0010 | 1.203 |

## City reference coordinates

| City | Latitude | Longitude |
| --- | --- | --- |
| Atlanta | 33.7490 | -84.3880 |
| Chicago | 41.8781 | -87.6298 |
| Dallas | 32.7767 | -96.7970 |
| Denver | 39.7392 | -104.9903 |
| Houston | 29.7604 | -95.3698 |
| Los Angeles | 34.0522 | -118.2437 |
| New York | 40.7128 | -74.0060 |
| Philadelphia | 39.9526 | -75.1652 |
| Phoenix | 33.4484 | -112.0740 |
| San Diego | 32.7157 | -117.1611 |
| Seattle | 47.6062 | -122.3321 |

## Selected-site audit

| City | Site ID | Latitude | Longitude | Location Setting | Land Use | Radius (km) | Days | First selected date | Last selected date | Observed years |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Atlanta | 13-089-0002 | 33.687800 | -84.290500 | SUBURBAN | RESIDENTIAL | 11.297 | 1204 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Atlanta | 13-089-0003 | 33.698643 | -84.272614 | SUBURBAN | COMMERCIAL | 12.051 | 1260 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Atlanta | 13-121-0056 | 33.778400 | -84.391400 | URBAN AND CENTER CITY | MOBILE | 3.284 | 1240 | 2019-05-03 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Chicago | 17-031-0076 | 41.751400 | -87.713488 | SUBURBAN | RESIDENTIAL | 15.703 | 1115 | 2019-04-01 | 2024-10-29 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Chicago | 17-031-0219 | 41.920009 | -87.672995 | URBAN AND CENTER CITY | COMMERCIAL | 5.873 | 1102 | 2019-07-26 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Chicago | 17-031-3103 | 41.965193 | -87.876265 | SUBURBAN | MOBILE | 22.574 | 1279 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Chicago | 17-031-4002 | 41.855243 | -87.752470 | SUBURBAN | RESIDENTIAL | 10.471 | 1167 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Dallas | 48-113-0069 | 32.820061 | -96.860117 | URBAN AND CENTER CITY | COMMERCIAL | 7.619 | 1232 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Dallas | 48-113-0075 | 32.919207 | -96.808501 | SUBURBAN | RESIDENTIAL | 15.882 | 1127 | 2019-04-01 | 2024-10-14 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Dallas | 48-113-0087 | 32.676448 | -96.872050 | SUBURBAN | COMMERCIAL | 13.174 | 1113 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Dallas | 48-113-1067 | 32.921150 | -96.753522 | URBAN AND CENTER CITY | COMMERCIAL | 16.568 | 1079 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Denver | 08-001-3001 | 39.838119 | -104.949840 | RURAL | AGRICULTURAL | 11.530 | 1155 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Denver | 08-031-0002 | 39.751184 | -104.987625 | URBAN AND CENTER CITY | COMMERCIAL | 1.352 | 1236 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Denver | 08-031-0026 | 39.779490 | -105.005180 | URBAN AND CENTER CITY | RESIDENTIAL | 4.657 | 1191 | 2019-04-06 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Denver | 08-031-0027 | 39.732170 | -105.015300 | URBAN AND CENTER CITY | COMMERCIAL | 2.276 | 1228 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Denver | 08-031-0028 | 39.786100 | -104.988600 | URBAN AND CENTER CITY | COMMERCIAL | 5.217 | 1239 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Houston | 48-201-0024 | 29.901030 | -95.326147 | SUBURBAN | RESIDENTIAL | 16.194 | 1119 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Houston | 48-201-0026 | 29.802716 | -95.125516 | SUBURBAN | RESIDENTIAL | 24.041 | 1212 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Houston | 48-201-0047 | 29.834167 | -95.489129 | SUBURBAN | RESIDENTIAL | 14.137 | 1108 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Houston | 48-201-0055 | 29.695660 | -95.499240 | SUBURBAN | RESIDENTIAL | 14.424 | 1094 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Houston | 48-201-0416 | 29.686289 | -95.294723 | URBAN AND CENTER CITY | RESIDENTIAL | 10.976 | 1213 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Houston | 48-201-0417 | 29.772857 | -95.395937 | URBAN AND CENTER CITY | COMMERCIAL | 2.878 | 818 | 2021-04-01 | 2024-10-31 | 2021, 2022, 2023, 2024 |
| Houston | 48-201-1034 | 29.768033 | -95.220574 | SUBURBAN | COMMERCIAL | 14.429 | 1235 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Houston | 48-201-1035 | 29.733737 | -95.257605 | URBAN AND CENTER CITY | INDUSTRIAL | 11.230 | 1002 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Houston | 48-201-1052 | 29.814387 | -95.387817 | URBAN AND CENTER CITY | RESIDENTIAL | 6.250 | 1075 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Houston | 48-201-1066 | 29.721621 | -95.492667 | URBAN AND CENTER CITY | COMMERCIAL | 12.622 | 1134 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Los Angeles | 06-037-0113 | 34.051110 | -118.456360 | URBAN AND CENTER CITY | MOBILE | 19.592 | 1277 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Los Angeles | 06-037-1103 | 34.066590 | -118.226880 | URBAN AND CENTER CITY | RESIDENTIAL | 2.227 | 1276 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Los Angeles | 06-037-1302 | 33.901389 | -118.205000 | URBAN AND CENTER CITY | RESIDENTIAL | 17.145 | 1257 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Los Angeles | 06-037-1602 | 34.010290 | -118.068500 | SUBURBAN | COMMERCIAL | 16.804 | 1265 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Los Angeles | 06-037-2005 | 34.132600 | -118.127200 | URBAN AND CENTER CITY | RESIDENTIAL | 13.965 | 1266 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Los Angeles | 06-037-4008 | 33.859662 | -118.200707 | SUBURBAN | INDUSTRIAL | 21.773 | 1271 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Los Angeles | 06-037-4010 | 34.181977 | -118.363036 | SUBURBAN | INDUSTRIAL | 18.136 | 1058 | 2020-04-01 | 2024-10-31 | 2020, 2021, 2022, 2023, 2024 |
| Los Angeles | 06-037-5005 | 33.955070 | -118.430490 | SUBURBAN | RESIDENTIAL | 20.325 | 584 | 2019-04-01 | 2021-09-15 | 2019, 2020, 2021 |
| New York | 34-003-0010 | 40.853550 | -73.966180 | URBAN AND CENTER CITY | COMMERCIAL | 16.006 | 1259 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| New York | 34-013-0003 | 40.720989 | -74.192892 | URBAN AND CENTER CITY | RESIDENTIAL | 15.777 | 814 | 2019-04-01 | 2022-09-25 | 2019, 2020, 2021, 2022 |
| New York | 34-017-0006 | 40.670250 | -74.126081 | URBAN AND CENTER CITY | COMMERCIAL | 11.175 | 1267 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| New York | 34-017-1002 | 40.731645 | -74.066308 | URBAN AND CENTER CITY | COMMERCIAL | 5.497 | 1221 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| New York | 34-039-0004 | 40.641440 | -74.208365 | SUBURBAN | INDUSTRIAL | 18.820 | 1257 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| New York | 36-005-0110 | 40.816000 | -73.902000 | URBAN AND CENTER CITY | RESIDENTIAL | 14.436 | 1214 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| New York | 36-005-0133 | 40.867900 | -73.878090 | URBAN AND CENTER CITY | COMMERCIAL | 20.332 | 1274 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| New York | 36-081-0124 | 40.736140 | -73.821530 | URBAN AND CENTER CITY | COMMERCIAL | 15.760 | 1251 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| New York | 36-081-0125 | 40.739264 | -73.817694 | URBAN AND CENTER CITY | MOBILE | 16.139 | 1192 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Philadelphia | 34-007-0002 | 39.934559 | -75.125219 | URBAN AND CENTER CITY | INDUSTRIAL | 3.955 | 1121 | 2019-04-01 | 2024-06-11 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Philadelphia | 34-007-0010 | 39.923969 | -75.122317 | URBAN AND CENTER CITY | COMMERCIAL | 4.848 | 82 | 2024-08-02 | 2024-10-31 | 2024 |
| Philadelphia | 42-045-0002 | 39.835556 | -75.372500 | URBAN AND CENTER CITY | INDUSTRIAL | 21.958 | 1139 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Philadelphia | 42-101-0048 | 39.991389 | -75.080833 | URBAN AND CENTER CITY | RESIDENTIAL | 8.384 | 1153 | 2019-07-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Philadelphia | 42-101-0075 | 40.054171 | -74.985166 | URBAN AND CENTER CITY | COMMERCIAL | 19.045 | 1240 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Philadelphia | 42-101-0076 | 39.988842 | -75.207205 | URBAN AND CENTER CITY | COMMERCIAL | 5.390 | 1247 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Phoenix | 04-013-0019 | 33.483780 | -112.142560 | SUBURBAN | RESIDENTIAL | 7.478 | 1224 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Phoenix | 04-013-3002 | 33.457970 | -112.046590 | URBAN AND CENTER CITY | RESIDENTIAL | 2.757 | 1253 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Phoenix | 04-013-4019 | 33.396230 | -111.967990 | URBAN AND CENTER CITY | COMMERCIAL | 11.421 | 214 | 2019-04-01 | 2019-10-31 | 2019 |
| Phoenix | 04-013-4020 | 33.461730 | -112.127960 | URBAN AND CENTER CITY | RESIDENTIAL | 5.221 | 1203 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Phoenix | 04-013-4021 | 33.410460 | -112.002640 | URBAN AND CENTER CITY | COMMERCIAL | 7.852 | 827 | 2021-04-01 | 2024-10-31 | 2021, 2022, 2023, 2024 |
| Phoenix | 04-013-9997 | 33.503833 | -112.095767 | URBAN AND CENTER CITY | RESIDENTIAL | 6.486 | 1270 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| San Diego | 06-073-0001 | 32.631242 | -117.059088 | SUBURBAN | RESIDENTIAL | 13.393 | 1231 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| San Diego | 06-073-1016 | 32.845709 | -117.123964 | SUBURBAN | MILITARY RESERVATION | 14.867 | 1248 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| San Diego | 06-073-1022 | 32.789565 | -116.944308 | SUBURBAN | COMMERCIAL | 21.874 | 1214 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| San Diego | 06-073-1025 | 32.552824 | -117.047345 | SUBURBAN | RESIDENTIAL | 21.011 | 221 | 2023-10-19 | 2024-10-31 | 2023, 2024 |
| San Diego | 06-073-1026 | 32.710177 | -117.142665 | URBAN AND CENTER CITY | COMMERCIAL | 1.831 | 1143 | 2019-08-03 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Seattle | 53-033-0030 | 47.597222 | -122.319722 | URBAN AND CENTER CITY | BLIGHTED AREAS | 1.363 | 1209 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |
| Seattle | 53-033-0080 | 47.568236 | -122.308628 | URBAN AND CENTER CITY | RESIDENTIAL | 4.574 | 1239 | 2019-04-01 | 2024-10-31 | 2019, 2020, 2021, 2022, 2023, 2024 |

## Rendering and provenance

Physical size: 174 × 160 mm. PNG is rendered directly from the Matplotlib scene at 1200 dpi (no upsampling); preview is rendered independently at 240 dpi. PDF, SVG and EPS contain vector marks and text; PDF/EPS use embedded TrueType fonts, and SVG keeps editable text with a DejaVu Sans font declaration. SVG appearance can depend on font availability. The layout has four columns and three rows, with the locator first and cities in alphabetical order. No figure-number title, panel letters or caption sentences are embedded. All figure type is at least 8 pt. EPA settings use both color and shape. The compact 160 mm image height reserves manuscript space below the image for a separately typeset caption.

| Raster | Width (px) | Height (px) | Recorded DPI |
| --- | --- | --- | --- |
| fig1_station_locations.png | 8220 | 7559 | 1199.9976 × 1199.9976 |
| fig1_station_locations_preview.png | 1644 | 1511 | 240.0046 × 240.0046 |

Automated checks cover site count, city count, metadata uniqueness, daily-row uniqueness, coordinate validity, radius inclusion, text within the figure canvas, locator label overlap and raster dimensions. Visual inspection is a separate operator step; successful rendering alone does not verify layout.

Runtime versions: NumPy 2.5.1; Matplotlib 3.11.1.

Read-only inputs (SHA-256 at generation):

| Input | SHA-256 |
| --- | --- |
| D:\MLWork\urban_no2_recovery_scs\results\revision_20260922\stations\station_daily.csv | 4e29a55138f84a2f051c34ca6685940813a927982ee314067eed020e4fe603ea |
| D:\MLWork\urban_no2_recovery_scs\results\wasp_20260923\metadata\city_site_metadata.csv | edf20374a5c22e8694de9b988ae112deacfe2324441feb8c88ca18e54dcfd2f2 |
| D:\MLWork\urban_no2_recovery_scs\release\urban-no2-weather-assessment-v1.0.0\provenance\city_metadata.json | a4280a547bf7225c510eec8dfa66682aaabc3d6e84f51ccf67e360fe7ad24a5b |

Generated outputs:

- D:\MLWork\urban_no2_recovery_scs\results\wasp_20260923\figures\fig1_station_locations.png
- D:\MLWork\urban_no2_recovery_scs\results\wasp_20260923\figures\fig1_station_locations.pdf
- D:\MLWork\urban_no2_recovery_scs\results\wasp_20260923\figures\fig1_station_locations.svg
- D:\MLWork\urban_no2_recovery_scs\results\wasp_20260923\figures\fig1_station_locations.eps
- D:\MLWork\urban_no2_recovery_scs\results\wasp_20260923\figures\fig1_station_locations_preview.png
- D:\MLWork\urban_no2_recovery_scs\results\wasp_20260923\figures\fig1_station_locations_metadata.md
