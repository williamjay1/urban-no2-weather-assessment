"""Render manuscript Figures 2 and 3 from the completed WASP analysis only.

Figure 2 cities: estimate_ppb and jackknife_lower/upper from the weather-adjusted
city table. Six delete-year fits are required; missing diagnostics retain the
point and an NA label. The bottom diamond uses model_summary.csv's supplied
cross_city_summary_lower/upper, not the city jackknife or bootstrap fields.

Figure 3: all 17 episode specifications from the frozen 20-model list after
excluding two phase models and four_weather_regimes. The latter estimates
compound-day contrasts, not episode contrasts: explain this exclusion in the
manuscript caption. Figure 3 intervals use cross_city_summary_lower/upper.
An unavailable fixed 11-city target is always NA, never an available-city mean.
The n/11 columns display n_estimable_cities; a short dash means not defined.

Cross-city t summaries describe dispersion (df=10); the source does not claim
guaranteed 95% coverage for the fixed heterogeneous 11-city target. City
delete-year intervals are diagnostics with six year blocks (t, df=5).
The main manuscript author handles captions. No captions are drawn here.

Writes only fig2_city_contrasts and fig3_sensitivity in the requested figures
directory, each as a native 1200 dpi PNG, PDF/SVG/EPS vectors and a preview PNG.
No model fitting, source edits, downloads, or other project imports occur.
"""

from __future__ import annotations

import csv
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from release_cli import PACKAGE, disable_network, plotting_environment, prepare_output

plotting_environment()
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
import numpy as np
from PIL import Image


ANALYSIS, FIGURES = PACKAGE / "results", PACKAGE / "reproduced_figures"
WIDTH_MM = 165
NATIVE_DPI, PREVIEW_DPI = 1200, 240
FIG2_HEIGHT_MM, FIG3_HEIGHT_MM = 137, 170
CITIES = ("Atlanta", "Chicago", "Dallas", "Denver", "Houston", "Los Angeles",
          "New York", "Philadelphia", "Phoenix", "San Diego", "Seattle")
CONTRASTS = ("episode_vs_reference", "episode_vs_wind_only")
AXIS_LABELS = ("Episode vs neither\nNO₂ difference (ppb)",
               "Episode vs wind only\nNO₂ difference (ppb)")
COLORS = ("#0072B2", "#D55E00")
EXCLUSIONS = {
    "phase_calendar_secondary": "Secondary phase estimand; excluded as requested.",
    "phase_adjusted_secondary": "Secondary phase estimand; excluded as requested.",
    "four_weather_regimes": "Compound-day, not episode, contrasts; separate Table 4 candidate.",
}
LABELS = {
    "calendar_only": "Calendar only",
    "weather_adjusted": "Weather adjusted",
    "direct_episode_neither": "Direct vs neither",
    "direct_episode_wind": "Direct vs wind only",
    "persistent_wind_comparator": "Persistent wind only",
    "direct_wind_spline": "Direct + wind spline",
    "core_monitors": "Core monitors",
    "equal_station_weights": "Equal site weights",
    "exclude_2020": "Exclude 2020",
    "period_2019_2022": "2019–2022",
    "period_2023_2024": "2023–2024",
    "extension_2025": "2025 extension",
    "city_median": "City median",
    "p85_p30_min2_sep7": "Heat threshold: 85th",
    "p80_p20_min2_sep7": "Wind threshold: 20th",
    "p80_p30_min3_sep7": "Duration ≥3 days",
    "p80_p30_min2_allruns": "All eligible runs",
}
DIRECT_CONTRASTS = {
    "direct_episode_neither": ("episode_vs_neither", None),
    "direct_episode_wind": (None, "episode_vs_wind_only"),
    "persistent_wind_comparator": (None, "episode_vs_persistent_wind_only"),
    "direct_wind_spline": (None, "episode_vs_wind_only"),
}


def number(value):
    if value is None or str(value).strip().lower() in {"", "na", "nan", "n/a", "none", "null"}:
        return math.nan
    return float(value)


def read_table(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def index_rows(rows, fields):
    index = {tuple(row[field] for field in fields): row for row in rows}
    if len(index) != len(rows):
        raise ValueError(f"Duplicate input rows for {fields}")
    return index


def limits_from(row, prefix):
    lower, upper = number(row[prefix + "_lower"]), number(row[prefix + "_upper"])
    if math.isfinite(lower) != math.isfinite(upper):
        raise ValueError(f"Only one interval endpoint exists: {row.get('model')}, {row.get('contrast')}")
    if math.isfinite(lower) and lower > upper:
        raise ValueError("Interval endpoints are reversed")
    return lower, upper


def load_inputs():
    paths = [ANALYSIS / "weather_adjusted_city_estimates.csv",
             ANALYSIS / "model_summary.csv", ANALYSIS / "model_specifications.json"]
    # In-memory snapshots prevent mixing different reads if other tasks run nearby.
    initial_hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    city_rows = read_table(paths[0])
    summary_rows = read_table(paths[1])
    with paths[2].open(encoding="utf-8-sig") as handle:
        specifications = json.load(handle)
    models = [row["model"] for row in specifications]
    if len(models) != 20 or len(set(models)) != 20:
        raise ValueError("Expected the complete frozen list of 20 unique models")
    if set(models) != set(LABELS) | set(EXCLUSIONS):
        raise ValueError("The model list changed: update the explicit scope and human labels")
    if set(row["model"] for row in summary_rows) != set(models):
        raise ValueError("Model summary does not cover the frozen specification list")
    if any(row["model"] != "weather_adjusted" for row in city_rows):
        raise ValueError("Unexpected model in the weather-adjusted city table")
    city_index = index_rows(city_rows, ("city", "contrast"))
    summary_index = index_rows(summary_rows, ("model", "contrast"))
    if {row["city"] for row in city_rows} != set(CITIES):
        raise ValueError("Weather-adjusted table does not contain the required 11 cities")

    fig2 = []
    for contrast in CONTRASTS:
        column = []
        for city in CITIES:
            source = city_index[city, contrast]
            point = number(source["estimate_ppb"])
            if (source["estimable"].lower() == "true") != math.isfinite(point):
                raise ValueError(f"Inconsistent city estimability: {city}, {contrast}")
            if int(source["n_year_blocks"]) != 6:
                raise ValueError("Figure 2 requires six year blocks")
            lower, upper = limits_from(source, "jackknife")
            if math.isfinite(lower) and source["jackknife_status"] != "delete_year_jackknife_diagnostic_t_df_5":
                raise ValueError("Figure 2 city interval is not the six-year delete-year diagnostic")
            if not math.isfinite(point) and math.isfinite(lower):
                raise ValueError("A missing point must not have an interval")
            column.append(dict(label=city, point=point, lower=lower, upper=upper,
                               interval_source="jackknife_lower/upper",
                               interval_status=source["jackknife_status"], marker="o"))
        mean = summary_cell(summary_index["weather_adjusted", contrast])
        if mean["status"] == "estimable":
            points = [cell["point"] for cell in column]
            if not all(map(math.isfinite, points)) or not math.isclose(float(np.mean(points)), mean["point"], abs_tol=1e-10):
                raise ValueError("The supplied 11-city mean differs from the full set of city estimates")
        mean.update(label="11 city mean", marker="D")
        column.append(mean)
        fig2.append(column)

    shown_models = [model for model in models if model not in EXCLUSIONS]
    if len(shown_models) != 17:
        raise ValueError("Expected 17 episode specifications")
    fig3 = []
    for model in shown_models:
        keys = DIRECT_CONTRASTS.get(model, CONTRASTS)
        row = []
        for contrast in keys:
            if contrast is None:
                row.append(dict(model=model, label=LABELS[model], status="not_defined", n=None,
                                point=math.nan, lower=math.nan, upper=math.nan))
            else:
                cell = summary_cell(summary_index[model, contrast])
                cell.update(label=LABELS[model])
                row.append(cell)
        fig3.append(row)

    for path in paths:
        if hashlib.sha256(path.read_bytes()).hexdigest() != initial_hashes[str(path)]:
            raise RuntimeError(f"Input changed while loading: {path}")
    return fig2, fig3, initial_hashes


def summary_cell(source):
    n = int(source["n_estimable_cities"])
    if int(source["n_cities"]) != 11 or not 0 <= n <= 11:
        raise ValueError("Figure target must be the fixed set of 11 cities")
    point = number(source["estimate_ppb"])
    lower, upper = limits_from(source, "cross_city_summary")
    missing = [city for city in source["missing_cities"].split(";") if city]
    if len(set(missing)) != 11 - n or set(missing) - set(CITIES):
        raise ValueError("Missing-city identities disagree with n_estimable_cities")
    if n == 11:
        if source["status"] != "estimable_all_11_cities" or not math.isfinite(point):
            raise ValueError("Inconsistent estimable all-city target")
        status = "estimable"
    else:
        if source["status"] != "unavailable_all_11_city_target" or any(map(math.isfinite, (point, lower, upper))):
            raise ValueError("Unavailable 11-city targets must retain missing points and intervals")
        status = "unavailable"
    return dict(model=source["model"], contrast=source["contrast"], status=status, n=n,
                point=point, lower=lower, upper=upper, missing_cities=missing,
                interval_source="cross_city_summary_lower/upper")


def set_style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.5,
        "axes.labelsize": 9.0, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
        "axes.linewidth": 0.6, "axes.unicode_minus": True,
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "svg.hashsalt": "wasp-result-figures-20260923",
    })


def add_axes_mm(fig, left, bottom, width, height, total_height):
    return fig.add_axes([left / WIDTH_MM, bottom / total_height, width / WIDTH_MM, height / total_height])


def setup_forest(ax, *, positions, labels, xlim, xticks, ylim, column):
    ax.set(xlim=xlim, ylim=ylim)
    ax.set_xticks(xticks)
    ax.set_yticks(positions, labels if column == 0 else [""] * len(labels))
    ax.tick_params(axis="y", length=0, pad=5)
    ax.tick_params(axis="x", length=3, pad=3)
    ax.set_xlabel(AXIS_LABELS[column], labelpad=6, linespacing=1.25)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color="#E6E8EA", linewidth=0.4)
    for y in positions:
        ax.axhline(y, color="#ECEEEF", linewidth=0.4, zorder=0)
    ax.axvline(0, color="#737373", linewidth=0.8, linestyle=(0, (3, 3)), zorder=1)
    for name in ("top", "left", "right"):
        ax.spines[name].set_visible(False)
    ax.spines["bottom"].set_color("#82878B")


def draw_point(ax, cell, y, color, *, marker="o", size=4.7):
    point, lower, upper = cell["point"], cell["lower"], cell["upper"]
    if not math.isfinite(point):
        ax.text(0.5, y, "NA", transform=ax.get_yaxis_transform(), ha="center", va="center",
                fontsize=8.5, color="#4D4D4D", bbox=dict(facecolor="white", edgecolor="none", pad=1), zorder=5)
        return
    if not ax.get_xlim()[0] < point < ax.get_xlim()[1]:
        raise ValueError("Point lies outside its plotting axis")
    if math.isfinite(lower):
        if not lower <= point <= upper:
            raise ValueError("The supplied interval does not contain the point estimate")
        if not (ax.get_xlim()[0] < lower <= upper < ax.get_xlim()[1]):
            raise ValueError("Interval would be clipped")
        ax.errorbar(point, y, xerr=[[point - lower], [upper - point]], fmt="none",
                    ecolor=color, elinewidth=0.9, capsize=2.2, capthick=0.9, zorder=3)
    ax.plot(point, y, marker=marker, linestyle="none", markersize=size, markerfacecolor=color,
            markeredgecolor="white", markeredgewidth=0.4, zorder=4)
    if not math.isfinite(lower):
        # A visible point plus NA means the prescribed interval is unavailable.
        side = -1 if point > sum(ax.get_xlim()) / 2 else 1
        ax.annotate("NA", (point, y), xytext=(side * 6, 0), textcoords="offset points",
                    ha="right" if side < 0 else "left", va="center", fontsize=8.5, color="#4D4D4D")


def figure2(cells):
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, FIG2_HEIGHT_MM / 25.4), dpi=PREVIEW_DPI)
    positions = list(range(11)) + [11.6]
    axes = []
    for col, left in enumerate((29, 101)):
        ax = add_axes_mm(fig, left, 28, 58, 103, FIG2_HEIGHT_MM)
        axes.append(ax)
        setup_forest(ax, positions=positions, labels=[cell["label"] for cell in cells[col]],
                     xlim=(-4.5, 12.5), xticks=[-4, 0, 4, 8, 12], ylim=(12.3, -0.7), column=col)
        ax.axhline(10.8, color="#A2A6AA", linewidth=0.65, zorder=1)
        for cell, y in zip(cells[col], positions, strict=True):
            is_mean = cell["marker"] == "D"
            draw_point(ax, cell, y, "#292929" if is_mean else COLORS[col],
                       marker=cell["marker"], size=5.6 if is_mean else 4.7)
    axes[0].get_yticklabels()[-1].set_fontweight("bold")
    handles = [
        Line2D([], [], color="#444444", marker="o", linestyle="none", markersize=4.7, label="City estimate"),
        Line2D([], [], color="#292929", marker="D", linestyle="none", markersize=5.3, label="11 city mean"),
    ]
    if any(math.isfinite(c["point"]) and not math.isfinite(c["lower"]) for column in cells for c in column):
        handles.append(Line2D([], [], color="white", linestyle="none", label="NA: interval unavailable"))
    fig.legend(handles=handles, loc="center", bbox_to_anchor=(0.56, 4.5 / FIG2_HEIGHT_MM),
               ncol=len(handles), frameon=False, fontsize=8.5, columnspacing=2, handletextpad=0.5)
    return fig


def figure3(cells):
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, FIG3_HEIGHT_MM / 25.4), dpi=PREVIEW_DPI)
    positions = list(range(len(cells)))
    for col, left in enumerate((43, 106)):
        ax = add_axes_mm(fig, left, 25, 43, 134, FIG3_HEIGHT_MM)
        setup_forest(ax, positions=positions, labels=[row[col]["label"] for row in cells],
                     xlim=(-2, 6.5), xticks=[-2, 0, 2, 4, 6], ylim=(16.7, -0.7), column=col)
        ax.text(1.14, 1.025, "n/11", transform=ax.transAxes, ha="center", va="bottom", fontsize=8.5)
        for row, y in zip(cells, positions, strict=True):
            cell = row[col]
            if cell["status"] == "not_defined":
                # Text at the column center, not a zero estimate.
                ax.text(0.5, y, "–", transform=ax.get_yaxis_transform(), ha="center", va="center",
                        fontsize=9, color="#575757", bbox=dict(facecolor="white", edgecolor="none", pad=1), zorder=5)
                count = "–"
            else:
                main = cell["model"] == "weather_adjusted"
                draw_point(ax, cell, y, COLORS[col], marker="D" if main else "o", size=5.5 if main else 4.5)
                count = f"{cell['n']}/11"
            ax.text(1.14, y, count, transform=ax.get_yaxis_transform(), ha="center", va="center", fontsize=8.5)
        if col == 0:
            for tick, row in zip(ax.get_yticklabels(), cells, strict=True):
                if row[col]["model"] == "weather_adjusted":
                    tick.set_fontweight("bold")
    # Compact symbol legend, not a caption or methods footnote.
    handles = [
        Line2D([], [], marker="D", color="#444444", linestyle="none", markersize=5.3, label="Main specification"),
        Line2D([], [], color="white", linestyle="none", label="NA  Unavailable"),
        Line2D([], [], color="white", linestyle="none", label="–  Not defined"),
    ]
    fig.legend(handles=handles, loc="center", bbox_to_anchor=(0.55, 3.7 / FIG3_HEIGHT_MM),
               ncol=3, frameon=False, fontsize=8.5, handlelength=1.0, columnspacing=1.2, handletextpad=0.5)
    return fig


def visual_bounds_check(fig):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = []
    for text in fig.findobj(Text):
        if not text.get_visible() or not text.get_text():
            continue
        if not 8 <= text.get_fontsize() <= 10:
            raise ValueError(f"Font outside 8–10 pt: {text.get_text()}")
        if "_" in text.get_text():
            raise ValueError(f"Code identifier leaked into the figure: {text.get_text()}")
        box = Text.get_window_extent(text, renderer)
        canvas = fig.bbox
        if box.x0 < -0.5 or box.y0 < -0.5 or box.x1 > canvas.x1 + 0.5 or box.y1 > canvas.y1 + 0.5:
            raise ValueError(f"Figure text is clipped: {text.get_text()}")
        boxes.append((text.get_text(), box))
    for i, (label, box) in enumerate(boxes):
        for other_label, other_box in boxes[i + 1:]:
            # Bounding boxes may touch but must not have a positive-area overlap.
            width = min(box.x1, other_box.x1) - max(box.x0, other_box.x0)
            height = min(box.y1, other_box.y1) - max(box.y0, other_box.y0)
            if width > 0.5 and height > 0.5:
                raise ValueError(f"Figure text overlaps: {label!r} and {other_label!r}")


def export(fig, stem, height_mm):
    visual_bounds_check(fig)
    FIGURES.mkdir(parents=True, exist_ok=True)
    for extension in ("pdf", "svg", "eps"):
        fig.savefig(FIGURES / f"{stem}.{extension}", format=extension)
    sizes = {}
    # No tight bounding box, raster upsampling, or image embedding in the vectors.
    for suffix, dpi in (("_preview.png", PREVIEW_DPI), (".png", NATIVE_DPI)):
        path = FIGURES / f"{stem}{suffix}"
        fig.savefig(path, dpi=dpi)
        with Image.open(path) as image:
            expected = (WIDTH_MM / 25.4 * dpi, height_mm / 25.4 * dpi)
            if any(abs(actual - goal) > 1 for actual, goal in zip(image.size, expected, strict=True)):
                raise ValueError(f"Unexpected raster size: {image.size}")
            if any(abs(recorded - dpi) > 0.1 for recorded in image.info["dpi"]):
                raise ValueError("Unexpected PNG resolution metadata")
            sizes[path.name] = image.size
    plt.close(fig)
    return sizes


def clean_json(value):
    if isinstance(value, dict):
        return {key: clean_json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean_json(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def main():
    fig2_cells, fig3_cells, hashes = load_inputs()
    set_style()
    fig2_sizes = export(figure2(fig2_cells), "fig2_city_contrasts", FIG2_HEIGHT_MM)
    fig3_sizes = export(figure3(fig3_cells), "fig3_sensitivity", FIG3_HEIGHT_MM)
    for path, expected in hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Input changed during rendering: {path}; rerun against a stable release")
    unavailable = [cell for row in fig3_cells for cell in row if cell["status"] == "unavailable"]
    print(json.dumps(clean_json({
        "figure2_mm": [WIDTH_MM, FIG2_HEIGHT_MM], "figure3_mm": [WIDTH_MM, FIG3_HEIGHT_MM],
        "figure2_sizes": fig2_sizes, "figure3_sizes": fig3_sizes,
        "figure2_city_contrasts": 22,
        "figure2_city_intervals_available": sum(math.isfinite(c["lower"]) for col in fig2_cells for c in col[:-1]),
        "figure2_mean_rows": [col[-1] for col in fig2_cells],
        "figure3_specs": len(fig3_cells),
        "figure3_cell_counts": dict(Counter(cell["status"] for row in fig3_cells for cell in row)),
        "figure3_unavailable": unavailable, "excluded_models": EXCLUSIONS,
        "interval_sources": {
            "figure2_cities": "jackknife_lower/upper; delete-year diagnostic, six blocks, t df=5",
            "figure2_mean_and_figure3": "cross_city_summary_lower/upper; cross-city dispersion summary, t df=10",
        }, "source_sha256": hashes,
    }), indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, default=ANALYSIS)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    disable_network()
    ANALYSIS = args.analysis.resolve()
    names = [stem + suffix for stem in ("fig2_city_contrasts", "fig3_sensitivity")
             for suffix in (".png", ".pdf", ".svg", ".eps", "_preview.png")]
    FIGURES = prepare_output(args.output, names, (ANALYSIS,))
    main()
