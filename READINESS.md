# v2.0.0 readiness

Version 2.0.0 verified release artifact: **artifact complete; local verification PASS**. The title remains **Urban Nitrogen Dioxide During Compound Heat and Low Wind Conditions**.

Completed and executed:

- Unchanged hourly ERA5 responses and EPA site/monitor metadata are bundled, with source URLs, hashes, fixed offsets, units, returned grids and source-license attribution.
- Portable offline hourly-to-daily reconstruction reproduces all 168,762 weather values and the reference CSV bytes exactly. NO2 is a byte-preserving copy of the 138,303-row derived station input.
- The three final statistical files match the owner's confirmed hashes. The complete independent rerun passes 15 tests and reproduces all 20 models / 98 contrasts, all failures and all missing all-city estimates, with 271 scientific artifacts matching exactly.
- All three final figures, ten article tables and their portable generation scripts are included and independently reproduced. Six PNGs are byte-identical; nine vector files differ only in generation dates; table text and scientific ledger/report content match exactly. Four presentation-layer tests passed, and all three previews were visually checked.
- README, citation metadata, separate code/data conditions, data dictionary and historical source limitations are included. No satellite QA repair or unknown old-model identity is invented.

The code/data/figure/table package is complete within the authorized scope. The unpublished author manuscript, cover letters and all submission files are deliberately excluded, not outstanding package deliverables. Figure PDFs are included; manuscript PDFs and DOCX files are not. Main-agent manuscript/Word review remains a separate task, and no claim of manuscript verification is made here.

The checksum inventory and inventory-only ZIP describe the verified artifact. Public-access verification is performed and saved separately by the publishing owner; that owner verifies the real v2.0.0 release/tree links before using them in the manuscript's data/code statement. This static artifact record does not encode a permanent unpublished status or claim that code reproduction establishes public accessibility. No DOI, live URL or release date is fabricated.

Known scope boundaries, not new statistical exclusions: national AQS source CSVs, a Python interpreter and dependency wheels are not bundled. Full analysis is offline from the included derived NO2 and reconstructed weather; raw national-AQS-to-NO2 reconstruction is not newly claimed. An existing documented Python environment was used, not a newly built virtual environment. The historical old-model identity and first-retrieval timestamps remain unresolved where the archives do not record them.
