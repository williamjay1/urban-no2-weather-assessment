"""Render the 62-site monitoring figure and a descriptive metadata audit.

Run with Python 3 and numpy/matplotlib. No downloads or other project imports.
Inputs are read-only; all six generated artifacts are confined to FIGURES.
The source site-day table already applies the project's AQS quality filters.
"""

from __future__ import annotations

import csv
import argparse
import hashlib
import json
import math
import warnings
from calendar import monthrange
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from itertools import combinations
from pathlib import Path

from release_cli import PACKAGE, disable_network, plotting_environment, prepare_output

plotting_environment()
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle
import numpy as np
from PIL import Image


DAILY = PACKAGE / "data/stations/station_daily.csv"
METADATA = PACKAGE / "provenance/city_site_metadata.csv"
CITY_METADATA = PACKAGE / "provenance/city_metadata.json"
FIGURES = PACKAGE / "reproduced_figures"
STEM = "fig1_station_locations"
WIDTH_MM, HEIGHT_MM, PANEL_MM = 174, 160, 32
NATIVE_DPI, PREVIEW_DPI = 1200, 240
EARTH_RADIUS_KM, RADIUS_KM = 6371.0, 25.0
MISSING = "[MISSING]"
STYLE = {
    "URBAN AND CENTER CITY": ("#0072B2", "o", "Urban and center city"),
    "SUBURBAN": ("#D55E00", "^", "Suburban"),
    "RURAL": ("#009E73", "s", "Rural"),
    MISSING: ("#666666", "D", "Missing"),
}
LOCATOR_LABELS = {
    "Atlanta": "ATL", "Chicago": "CHI", "Dallas": "DAL", "Denver": "DEN",
    "Houston": "HOU", "Los Angeles": "LA", "New York": "NY",
    "Philadelphia": "PHL", "Phoenix": "PHX", "San Diego": "SD", "Seattle": "SEA",
}
MISSING_TOKENS = {"", "na", "n/a", "nan", "null", "none", "unknown", "not reported"}


def category(value):
    value = str(value or "").strip()
    return MISSING if value.lower() in MISSING_TOKENS else value


def finite(value):
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def haversine(lat, lon, lat0, lon0):
    lat, lon, lat0, lon0 = np.radians([lat, lon, lat0, lon0])
    a = np.sin((lat - lat0) / 2) ** 2 + np.cos(lat) * np.cos(lat0) * np.sin((lon - lon0) / 2) ** 2
    return float(2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1))))


def local_offsets(lat, lon, center):
    """Local equirectangular offsets; east positive x, north positive y."""
    east = EARTH_RADIUS_KM * math.cos(math.radians(center["lat"])) * math.radians(lon - center["lon"])
    north = EARTH_RADIUS_KM * math.radians(lat - center["lat"])
    return east, north


def load_inputs():
    with CITY_METADATA.open(encoding="utf-8-sig") as handle:
        center_rows = json.load(handle)
    centers = {row["city"]: row for row in center_rows}
    if len(centers) != len(center_rows):
        raise ValueError("Duplicate city reference coordinates")
    with METADATA.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        metadata_rows = list(reader)
    metadata = {(r["city"], r["station_id"]): r for r in metadata_rows}
    if len(metadata) != len(metadata_rows):
        raise ValueError("Metadata must have exactly one row per city/site")

    all_dates = defaultdict(list)
    selected = defaultdict(list)
    seen = set()
    rejected_in_window = 0
    with DAILY.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = row["city"], row["station_id"]
            day = row["date"][:10]
            all_dates[key].append(day)
            year, month = int(day[:4]), int(day[5:7])
            if not (2019 <= year <= 2024 and 4 <= month <= 10):
                continue
            if not finite(row["no2_ppb"]) or not finite(row["observation_count"]) or float(row["observation_count"]) <= 0:
                rejected_in_window += 1
                continue
            day_key = key + (day,)
            if day_key in seen:
                raise ValueError(f"Duplicate selected site-day: {day_key}")
            seen.add(day_key)
            selected[key].append(row)

    if len(selected) != 62 or len({key[0] for key in selected}) != 11:
        raise ValueError(f"Expected 62 sites in 11 cities, got {len(selected)} sites")
    if len({key[1] for key in selected}) != 62:
        raise ValueError("The same site appears in multiple cities")
    if set(selected) - set(metadata):
        raise ValueError(f"Missing metadata rows: {set(selected) - set(metadata)}")
    if {key[0] for key in selected} - set(centers):
        raise ValueError("Missing city reference coordinates")

    sites = []
    for key, rows in sorted(selected.items()):
        meta = metadata[key]
        if not all(finite(meta[field]) for field in ("Latitude", "Longitude")):
            raise ValueError(f"Missing coordinate: {key}")
        lat, lon = float(meta["Latitude"]), float(meta["Longitude"])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError(f"Invalid coordinate: {key}")
        if category(meta["Location Setting"]) not in STYLE:
            raise ValueError(f"Unconfigured EPA setting: {meta['Location Setting']}")
        center = centers[key[0]]
        east, north = local_offsets(lat, lon, center)
        exact_radius = haversine(lat, lon, center["lat"], center["lon"])
        if exact_radius > RADIUS_KM or math.hypot(east, north) > RADIUS_KM:
            raise ValueError(f"Site falls outside the 25 km displayed domain: {key}")
        coordinates = {(float(r["latitude"]), float(r["longitude"])) for r in rows}
        daily_distance = [float(r["distance_km"]) for r in rows]
        if max(daily_distance) > RADIUS_KM:
            raise ValueError(f"Selected daily distance exceeds 25 km: {key}")
        sites.append({
            "city": key[0], "station_id": key[1], "meta": meta,
            "lat": lat, "lon": lon, "east": east, "north": north,
            "radius_km": exact_radius,
            "approx_radius_km": math.hypot(east, north),
            "days": len(rows), "first": min(r["date"] for r in rows),
            "last": max(r["date"] for r in rows),
            "dates": sorted({r["date"][:10] for r in rows}),
            "days_by_year": dict(Counter(int(r["date"][:4]) for r in rows)),
            "years": sorted({int(r["date"][:4]) for r in rows}),
            "coordinate_variants": len(coordinates),
            "metadata_daily_difference_km": max(haversine(lat, lon, la, lo) for la, lo in coordinates),
            "recorded_radius_difference_km": max(abs(d - exact_radius) for d in daily_distance),
        })
    return sites, centers, metadata, fields, all_dates, rejected_in_window


def close_pairs(sites):
    pairs = []
    for a, b in combinations(sites, 2):
        if a["city"] != b["city"]:
            continue
        separation = haversine(a["lat"], a["lon"], b["lat"], b["lon"])
        if separation < 2:
            pairs.append((a, b, separation))
    return pairs


def make_figure(sites, centers):
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.0,
        "axes.titlesize": 8.5, "axes.labelsize": 8.0,
        "xtick.labelsize": 8.0, "ytick.labelsize": 8.0,
        "axes.linewidth": 0.5, "pdf.fonttype": 42, "ps.fonttype": 42,
        "svg.fonttype": "none", "svg.hashsalt": "wasp-station-locations-20260923",
        "savefig.facecolor": "white", "figure.facecolor": "white",
        "axes.unicode_minus": True,
    })
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), dpi=PREVIEW_DPI)
    axes = []
    for row in range(3):
        for col in range(4):
            axes.append(fig.add_axes([
                (10 + 43 * col) / WIDTH_MM, (117 - 46.5 * row) / HEIGHT_MM,
                PANEL_MM / WIDTH_MM, PANEL_MM / HEIGHT_MM,
            ]))
    locator = axes[0]
    locator.set_title("US locator", loc="left", pad=4)
    locator.set(xlim=(-130, -66), ylim=(24, 52))
    locator.set_xticks([-120, -100, -80], ["120°W", "100°W", "80°W"])
    locator.set_yticks([30, 40, 50], ["30°N", "40°N", "50°N"])
    locator.tick_params(length=2, pad=2, labelsize=8.0)
    locator.grid(color="#E5E8EB", linewidth=0.4)
    # Label positions are annotations only; city symbols use the input coordinates.
    label_positions = {
        "Seattle": (-128, 49.5, "left"),
        "Los Angeles": (-128, 36.5, "left"),
        "San Diego": (-128, 27.0, "left"),
        "Phoenix": (-109, 30.0, "center"),
        "Denver": (-113, 43.0, "left"),
        "Dallas": (-96, 35.0, "center"),
        "Houston": (-98, 26.3, "center"),
        "Chicago": (-91, 48.0, "center"),
        "New York": (-67, 44.1, "right"),
        "Philadelphia": (-67, 38.6, "right"),
        "Atlanta": (-67, 32.3, "right"),
    }
    locator_annotations = []
    for city in sorted({s["city"] for s in sites}):
        center = centers[city]
        locator.plot(center["lon"], center["lat"], "+", color="#252525", markersize=4.2, markeredgewidth=0.85, zorder=4)
        x, y, align = label_positions[city]
        annotation = locator.annotate(
            LOCATOR_LABELS[city], (center["lon"], center["lat"]), xytext=(x, y),
            fontsize=8.0, ha=align, va="center", zorder=5,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.25},
            arrowprops={"arrowstyle": "-", "color": "#6A6A6A", "lw": 0.45, "shrinkA": 2, "shrinkB": 3},
        )
        locator_annotations.append(annotation)

    pairs = close_pairs(sites)
    pair_label_positions = {"Denver": (-21, 17), "New York": (-23, 12), "Philadelphia": (-24, -18)}
    local_axes = {}
    for ax, city in zip(axes[1:], sorted({s["city"] for s in sites}), strict=True):
        local_axes[city] = ax
        city_sites = [s for s in sites if s["city"] == city]
        ax.set(xlim=(-28, 28), ylim=(-28, 28), aspect="equal")
        ax.set_xticks([-20, 0, 20])
        ax.set_yticks([-20, 0, 20])
        ax.tick_params(length=2, pad=2)
        ax.grid(color="#E5E8EB", linewidth=0.4, zorder=0)
        ax.add_patch(Circle((0, 0), RADIUS_KM, fill=False, edgecolor="#707070", linewidth=0.7, linestyle=(0, (3, 2)), zorder=2))
        ax.plot(0, 0, "+", color="#252525", markersize=5.0, markeredgewidth=0.9, zorder=3)
        for site in city_sites:
            color, marker, _ = STYLE[category(site["meta"]["Location Setting"])]
            ax.plot(site["east"], site["north"], marker=marker, linestyle="none", markersize=4.3,
                    markerfacecolor=color, markeredgecolor="white", markeredgewidth=0.35, zorder=4)
        ax.set_title(city, loc="left", pad=4)
        ax.set_title(f"n = {len(city_sites)}", loc="right", pad=4, fontsize=8.0, color="#444444")
        for a, b, _ in pairs:
            if a["city"] != city:
                continue
            if city not in pair_label_positions:
                raise ValueError(f"Please inspect and place the close-site callout for {city}")
            midpoint = ((a["east"] + b["east"]) / 2, (a["north"] + b["north"]) / 2)
            ax.annotate("2 sites", midpoint, xytext=pair_label_positions[city], fontsize=8.0, va="center",
                        bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.5},
                        arrowprops={"arrowstyle": "-", "color": "#555555", "lw": 0.55, "shrinkA": 2, "shrinkB": 2}, zorder=6)

    for ax in axes:
        for spine in ax.spines.values():
            spine.set_color("#A3A9AF")
    fig.text(1.5 / WIDTH_MM, 86 / HEIGHT_MM, "North offset (km)", rotation=90, ha="center", va="center", fontsize=8.0)
    fig.text(90 / WIDTH_MM, 15.7 / HEIGHT_MM, "East offset (km)", ha="center", va="center", fontsize=8.0)
    settings = Counter(category(s["meta"]["Location Setting"]) for s in sites)
    legend_handles = [Line2D([], [], linestyle="none", marker=marker, color=color, markersize=4.6,
                             label=f"{label} ({settings[setting]})")
                      for setting, (color, marker, label) in STYLE.items() if settings[setting]]
    fig.legend(handles=legend_handles, loc="center", bbox_to_anchor=(0.5, 9.5 / HEIGHT_MM), ncol=3,
               frameon=False, fontsize=8.0, handletextpad=0.5, columnspacing=1.5)
    ref_handles = [
        Line2D([], [], color="#252525", marker="+", linestyle="none", markersize=5, label="City reference point"),
        Line2D([], [], color="#707070", linestyle=(0, (3, 2)), lw=0.7, label="25 km radius"),
    ]
    fig.legend(handles=ref_handles, loc="center", bbox_to_anchor=(0.5, 3.5 / HEIGHT_MM), ncol=2,
               frameon=False, fontsize=8.0, handlelength=1.6, handletextpad=0.6, columnspacing=2)
    fig.canvas.draw()

    # Check all text boxes against the native figure canvas before any export.
    renderer = fig.canvas.get_renderer()
    canvas = fig.bbox
    for artist in fig.findobj(matplotlib.text.Text):
        if not artist.get_visible() or not artist.get_text():
            continue
        if artist.get_fontsize() < 8.0:
            raise ValueError(f"Text is smaller than 8 pt: {artist.get_text()}")
        box = artist.get_window_extent(renderer)
        if box.x0 < -1 or box.y0 < -1 or box.x1 > canvas.x1 + 1 or box.y1 > canvas.y1 + 1:
            raise ValueError(f"Text crosses the figure edge: {artist.get_text()}")
    # Text-only boxes avoid counting a label's leader as a label overlap.
    label_boxes = [(a.get_text(), matplotlib.text.Text.get_window_extent(a, renderer)) for a in locator_annotations]
    for (name_a, box_a), (name_b, box_b) in combinations(label_boxes, 2):
        if box_a.overlaps(box_b):
            raise ValueError(f"Locator labels overlap: {name_a}, {name_b}")
    for ax in axes[1:]:
        if ax._left_title.get_window_extent(renderer).overlaps(ax._right_title.get_window_extent(renderer)):
            raise ValueError(f"City title and site count overlap: {ax.get_title(loc='left')}")
    return fig, pairs


def md_table(headers, rows):
    def escape(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    return "\n".join([
        "| " + " | ".join(map(escape, headers)) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(map(escape, row)) + " |" for row in rows),
    ])


def write_report(sites, centers, metadata, fields, all_dates, rejected, pairs, dimensions):
    selected_keys = {(s["city"], s["station_id"]) for s in sites}
    excluded = sorted(set(all_dates) - selected_keys)
    city_counts = Counter(s["city"] for s in sites)
    study_dates = [date(year, month, day).isoformat()
                   for year in range(2019, 2025) for month in range(4, 11)
                   for day in range(1, monthrange(year, month)[1] + 1)]
    city_daily_counts = {
        city: Counter(day for s in sites if s["city"] == city for day in s["dates"])
        for city in city_counts
    }
    caption = (
        "Monitoring locations. Panels read left to right: top row, US locator, Atlanta (ATL), Chicago (CHI), "
        "Dallas (DAL); middle row, Denver (DEN), Houston (HOU), Los Angeles (LA), New York (NY); bottom row, "
        "Philadelphia (PHL), Phoenix (PHX), San Diego (SD), Seattle (SEA). Abbreviations identify cities in the "
        "locator. The 62 sites have at least one valid daily observation in April–October 2019–2024; n gives "
        "site counts. Colors and shapes indicate EPA Location Setting. Crosses mark city reference coordinates "
        "and dashed circles indicate 25 km radii. Local panels share approximate east–north offsets, with "
        "north upward. Close pairs are annotated without moving coordinates. The locator uses longitude "
        "and latitude; no boundaries or basemap are shown."
    )
    report = [
        "# Station locations: descriptive metadata report", "",
        f"Generated (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}", "",
        "## Suggested caption", "", caption, "",
        "## Selection and counts", "",
        f"Selected **{len(sites)} unique sites in {len(city_counts)} cities**, contributing {sum(s['days'] for s in sites):,} "
        "unique site-days. Inclusion requires at least one row dated in April–October of 2019–2024, "
        "a finite no2_ppb value and a positive finite observation_count in the supplied revision station_daily.csv. "
        "This is a union across the study window, not a claim that each site operated throughout all six years. "
        "No additional completeness rule or new measurement-quality filter was imposed.", "",
        f"The daily table contains {len(all_dates)} sites across all dates, and the metadata table contains {len(metadata)} rows. "
        f"All 62 selected sites have unique matching metadata and valid coordinates. In-window rows rejected by the "
        f"finite-value/count check: {rejected}.", "",
        md_table(["City", "Sites", "Site-days"], [(city, city_counts[city], sum(s["days"] for s in sites if s["city"] == city)) for city in sorted(city_counts)]), "",
        "Excluded sites in the daily input:", "",
        md_table(["City", "Site ID", "First available day", "Last available day", "Available days"],
                 [(c, sid, min(all_dates[c, sid]), max(all_dates[c, sid]), len(all_dates[c, sid])) for c, sid in excluded]), "",
        "## Observation coverage", "",
        f"April–October contains 214 calendar days per year, giving {len(study_dates):,} days across 2019–2024. "
        "A city's covered day has at least one selected site observation. Daily site counts include every "
        "study-window date, including zero-site days. The fixed-network site-day fraction divides observed "
        "site-days by selected sites × 1,284. This is a descriptive common-window denominator, not regulatory "
        "completeness or a claim that every site was scheduled to operate throughout the window.", "",
        md_table(["City", "Covered days / 1,284", "Days with no sites", "Daily sites min / median / max", "Site-days / fixed network (%)"],
                 [(city, len(city_daily_counts[city]), len(study_dates) - len(city_daily_counts[city]),
                   f"{min(city_daily_counts[city][d] for d in study_dates)} / "
                   f"{np.median([city_daily_counts[city][d] for d in study_dates]):g} / "
                   f"{max(city_daily_counts[city][d] for d in study_dates)}",
                   f"{100 * sum(city_daily_counts[city].values()) / (city_counts[city] * len(study_dates)):.2f}%")
                  for city in sorted(city_counts)]), "",
        "Distinct sites with observations in each April–October season:", "",
        md_table(["City"] + list(range(2019, 2025)),
                 [(city,) + tuple(sum(year in s["years"] for s in sites if s["city"] == city) for year in range(2019, 2025))
                  for city in sorted(city_counts)]), "",
        "Network totals by season:", "",
        md_table(["Year", "Distinct sites", "Observed site-days"],
                 [(year, sum(year in s["years"] for s in sites), sum(s["days_by_year"].get(year, 0) for s in sites))
                  for year in range(2019, 2025)]), "",
        "## Metadata category distributions", "",
        "Counts below use the 62 selected sites (one vote per site). EPA text is retained exactly; categories "
        "describe the supplied site metadata snapshot, not historical category stability or a citywide property. "
        "Land Use and Location Setting are separate fields. Missing includes blank values and explicit "
        "NA/N/A/NaN/null/none/unknown/not reported tokens; a blank field need not imply an error.", "",
    ]
    for field in ("Location Setting", "Land Use", "GMT Offset", "gmt_offset_hours", "Datum", "Extraction Date", "Owning Agency"):
        counts = Counter(category(s["meta"][field]) for s in sites)
        known = len(sites) - counts[MISSING]
        report.extend([f"### {field}", "", f"Known: {known}; missing: {counts[MISSING]}.", "",
                       md_table(["Category", "Sites", "Percent of 62"], [(key, value, f"{100 * value / len(sites):.1f}%") for key, value in sorted(counts.items())]), ""])
    report.extend(["## Metadata completeness", "",
                   "All non-key columns are counted separately; zero and negative GMT offsets are known values. "
                   "Site Closed Date and meteorological-site fields can legitimately be blank. A GMT offset is "
                   "reported as supplied and is not a date-specific daylight-saving-time conversion.", "",
                   md_table(["Field", "Known", "Missing"], [(field, sum(category(s["meta"][field]) != MISSING for s in sites), sum(category(s["meta"][field]) == MISSING for s in sites)) for field in fields if field not in ("city", "station_id")]), "",
                   "## Seattle: actual selected site information", "",
                   "Seattle contributes two sites. Both have known EPA Location Setting, Land Use, GMT Offset, "
                   "coordinates, datum and local site name. Both are URBAN AND CENTER CITY. Their distinct Land Use "
                   "labels are reproduced as recorded; BLIGHTED AREAS is an EPA metadata value, not an inference "
                   "about neighborhood conditions made for this figure.", ""])
    seattle = [s for s in sites if s["city"] == "Seattle"]
    report.extend(["Seattle observation coverage (same 1,284-day calendar denominator):", "",
                   md_table(["Site ID", "Observed days", "Fraction of 1,284"] + list(range(2019, 2025)),
                            [(s["station_id"], s["days"], f"{100 * s['days'] / len(study_dates):.2f}%") +
                             tuple(s["days_by_year"].get(year, 0) for year in range(2019, 2025)) for s in seattle]), ""])
    report.append(md_table(["Field"] + [s["station_id"] for s in seattle],
                           [(field,) + tuple(category(s["meta"][field]) for s in seattle) for field in fields if field not in ("city", "station_id")]))
    report.extend(["", "Seattle-only known versus missing counts:", "",
                   md_table(["Field", "Known", "Missing"], [(field, sum(category(s["meta"][field]) != MISSING for s in seattle), sum(category(s["meta"][field]) == MISSING for s in seattle)) for field in fields if field not in ("city", "station_id")]), ""])
    for key in excluded:
        if key[0] == "Seattle":
            meta = metadata[key]
            report.extend([f"Excluded Seattle site {key[1]} ({meta['Local Site Name']}): "
                           f"Location Setting = {meta['Location Setting']}; Land Use = {meta['Land Use']}; "
                           f"GMT Offset = {meta['GMT Offset']}. Its supplied observations run from "
                           f"{min(all_dates[key])} to {max(all_dates[key])}, outside the 2019–2024 selection. "
                           "Its SUBURBAN / INDUSTRIAL labels must not be attributed to the two selected Seattle sites.", ""])
    max_approx_error = max(abs(s["approx_radius_km"] - s["radius_km"]) for s in sites)
    report.extend([
        "## Coordinates, local geometry and limitations", "",
        "City reference coordinates are read from the previous release's provenance/city_metadata.json. "
        "They are study reference points; this script does not assert that they are administrative centroids, "
        "downtown boundaries or population centers. Site coordinates come from city_site_metadata.csv and "
        "are cross-checked against all selected daily coordinates.", "",
        "Offsets use R = 6371 km, x = R cos(latitude0) (longitude − longitude0) and "
        "y = R (latitude − latitude0), with angular differences in radians. x increases eastward and y "
        "northward. Local panels all span −28 to +28 km in each direction, have equal aspect, and draw a "
        "25 km circle in this approximate coordinate system. This is a local equirectangular approximation, "
        "not a surveyed distance or an ellipsoidal geodesic projection. The locator has angular axes and "
        "must not be used to measure distance or area. No geographic boundaries, coastlines, roads, land "
        "cover or other unsupported basemap features are drawn.", "",
        f"Maximum selected-site spherical distance from its reference point: {max(s['radius_km'] for s in sites):.6f} km. "
        f"Maximum approximate radius: {max(s['approx_radius_km'] for s in sites):.6f} km. "
        f"Maximum radial difference between the local approximation and spherical haversine: {1000 * max_approx_error:.3f} m. "
        "All selected sites are within 25 km by both calculations and in the supplied daily-distance column.", "",
        f"Maximum metadata-to-daily coordinate separation: {1000 * max(s['metadata_daily_difference_km'] for s in sites):.6f} m. "
        f"Sites with multiple coordinate pairs in the selected daily rows: {sum(s['coordinate_variants'] > 1 for s in sites)}. "
        f"Maximum difference from the source daily radius: {1000 * max(s['recorded_radius_difference_km'] for s in sites):.6f} m.", "",
        "The supplied coordinates include NAD83 and WGS84 datum labels. No datum transformation was performed; "
        "the coordinates are displayed as supplied for this city-scale locator. The approximation-error check "
        "does not quantify datum or source-coordinate uncertainty. Metadata is a snapshot, so the figure does "
        "not establish that the setting or land-use category was unchanged in every study year. "
        "Site density and category counts describe this selected monitoring network, not population exposure "
        "or representativeness of a whole city.", "",
        "Pairs separated by less than 2 km receive a '2 sites' callout. Markers remain at their true plotted "
        "coordinates; no site is jittered, merged, dropped or moved. Some glyphs consequently overlap at print size.", "",
        md_table(["City", "Site 1", "Site 2", "Separation (km)"], [(a["city"], a["station_id"], b["station_id"], f"{distance:.3f}") for a, b, distance in pairs]), "",
        "## City reference coordinates", "",
        md_table(["City", "Latitude", "Longitude"], [(city, f"{centers[city]['lat']:.4f}", f"{centers[city]['lon']:.4f}") for city in sorted(city_counts)]), "",
        "## Selected-site audit", "",
        md_table(["City", "Site ID", "Latitude", "Longitude", "Location Setting", "Land Use", "Radius (km)", "Days", "First selected date", "Last selected date", "Observed years"],
                 [(s["city"], s["station_id"], f"{s['lat']:.6f}", f"{s['lon']:.6f}", category(s["meta"]["Location Setting"]), category(s["meta"]["Land Use"]), f"{s['radius_km']:.3f}", s["days"], s["first"], s["last"], ", ".join(map(str, s["years"]))) for s in sites]), "",
        "## Rendering and provenance", "",
        f"Physical size: {WIDTH_MM} × {HEIGHT_MM} mm. PNG is rendered directly from the Matplotlib scene at "
        f"{NATIVE_DPI} dpi (no upsampling); preview is rendered independently at {PREVIEW_DPI} dpi. "
        "PDF, SVG and EPS contain vector marks and text; PDF/EPS use embedded TrueType fonts, and SVG keeps "
        "editable text with a DejaVu Sans font declaration. SVG appearance can depend on font availability. "
        "The layout has four columns and three rows, with the locator first and cities in alphabetical order. "
        "No figure-number title, panel letters or caption sentences are embedded. All figure type is at least "
        "8 pt. EPA settings use both color and shape. The compact 160 mm image height reserves manuscript "
        "space below the image for a separately typeset caption.", "",
        md_table(["Raster", "Width (px)", "Height (px)", "Recorded DPI"], [(name, *details) for name, details in dimensions.items()]), "",
        "Automated checks cover site count, city count, metadata uniqueness, daily-row uniqueness, coordinate "
        "validity, radius inclusion, text within the figure canvas, locator label overlap and raster dimensions. "
        "Visual inspection is a separate operator step; successful rendering alone does not verify layout.", "",
        f"Runtime versions: NumPy {np.__version__}; Matplotlib {matplotlib.__version__}.", "",
        "Read-only inputs (SHA-256 at generation):", "",
        md_table(["Input", "SHA-256"], [(str(path), hashlib.sha256(path.read_bytes()).hexdigest()) for path in (DAILY, METADATA, CITY_METADATA)]), "",
        "Generated outputs:", "",
        *[f"- {FIGURES / (STEM + suffix)}" for suffix in (".png", ".pdf", ".svg", ".eps", "_preview.png", "_metadata.md")], "",
    ])
    (FIGURES / f"{STEM}_metadata.md").write_text("\n".join(report), encoding="utf-8")


def main():
    sites, centers, metadata, fields, all_dates, rejected = load_inputs()
    fig, pairs = make_figure(sites, centers)
    FIGURES.mkdir(parents=True, exist_ok=True)
    # Deliberately omit bbox_inches='tight': exports must retain exactly 174 × 160 mm.
    for extension in ("pdf", "svg", "eps"):
        fig.savefig(FIGURES / f"{STEM}.{extension}", format=extension)
    fig.savefig(FIGURES / f"{STEM}_preview.png", dpi=PREVIEW_DPI)
    fig.savefig(FIGURES / f"{STEM}.png", dpi=NATIVE_DPI)
    plt.close(fig)
    dimensions = {}
    for suffix, dpi in ((".png", NATIVE_DPI), ("_preview.png", PREVIEW_DPI)):
        name = STEM + suffix
        # These are the exact PNGs just rendered here, with checked dimensions.
        # Scope the high-resolution image allowance to our own just-rendered outputs.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            with Image.open(FIGURES / name) as image:
                width, height = image.size
                expected = (round(WIDTH_MM / 25.4 * dpi), round(HEIGHT_MM / 25.4 * dpi))
                if abs(width - expected[0]) > 1 or abs(height - expected[1]) > 1:
                    raise ValueError(f"Unexpected raster dimensions: {image.size}")
                recorded = image.info.get("dpi", (0, 0))
                if any(abs(value - dpi) > 0.1 for value in recorded):
                    raise ValueError(f"Unexpected raster DPI: {recorded}")
                dimensions[name] = (width, height, f"{recorded[0]:.4f} × {recorded[1]:.4f}")
    write_report(sites, centers, metadata, fields, all_dates, rejected, pairs, dimensions)
    print(json.dumps({
        "sites": len(sites), "cities": len({s["city"] for s in sites}),
        "city_counts": dict(sorted(Counter(s["city"] for s in sites).items())),
        "settings": dict(Counter(s["meta"]["Location Setting"] for s in sites)),
        "land_use": dict(Counter(s["meta"]["Land Use"] for s in sites)),
        "dimensions": dimensions, "output_directory": str(FIGURES),
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--station-daily", type=Path, default=DAILY)
    parser.add_argument("--site-metadata", type=Path, default=METADATA)
    parser.add_argument("--city-metadata", type=Path, default=CITY_METADATA)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    disable_network()
    DAILY, METADATA, CITY_METADATA = (args.station_daily.resolve(), args.site_metadata.resolve(), args.city_metadata.resolve())
    names = [STEM + suffix for suffix in (".png", ".pdf", ".svg", ".eps", "_preview.png", "_metadata.md")]
    FIGURES = prepare_output(args.output, names, (DAILY, METADATA, CITY_METADATA))
    main()
