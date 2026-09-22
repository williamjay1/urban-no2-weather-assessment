"""Offline UTC-hourly ERA5 -> EPA AQS local-standard-day reconstruction.

No network access, private modules, environment variables or machine paths.
With no --output or --report, verification is entirely read-only.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

import numpy as np
import pandas as pd

# Also works in Python isolated mode (-I), which omits the script directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from wasp_weather_aggregation import aggregate


PACKAGE = Path(__file__).resolve().parents[1]
HOURS = ["temperature_2m", "wind_speed_10m", "relative_humidity_2m",
         "precipitation", "shortwave_radiation", "wind_direction_10m"]
FIELDS = ["temperature_2m_max", "wind_speed_10m_mean", "relative_humidity_2m_mean",
          "wind_direction_10m_dominant", "precipitation_sum", "shortwave_radiation_sum"]
UNITS = dict(time="iso8601", temperature_2m="\u00b0C", wind_speed_10m="km/h",
             relative_humidity_2m="%", precipitation="mm", shortwave_radiation="W/m\u00b2",
             wind_direction_10m="\u00b0")
ATOL = 1e-10


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inside(root, relative):
    """Resolve only package-relative files; reject traversal and external symlinks."""
    rel = PurePosixPath(relative)
    require(not rel.is_absolute() and ".." not in rel.parts and "\\" not in relative
            and ":" not in relative, f"Not a safe relative path: {relative}")
    path = (root / relative).resolve()
    require(root.resolve() in path.parents, f"Path escapes package: {relative}")
    return path


def check_inputs(root):
    manifest = json.loads((root / "provenance/input_manifest.json").read_text(encoding="utf-8"))
    seen = set()
    for item in manifest["files"]:
        require(item["path"] not in seen, "Duplicate manifest path")
        seen.add(item["path"])
        path = inside(root, item["path"])
        require(path.stat().st_size == item["bytes"] and digest(path) == item["sha256"],
                f"Input checksum mismatch: {item['path']}")
    provenance = json.loads((root / "provenance/aggregation_source.json").read_text(encoding="utf-8"))
    require(digest(inside(root, provenance["portable_module"])) == provenance["portable_module_sha256"],
            "Aggregation module checksum mismatch")
    return len(seen)


def site_offsets(root, stations):
    audit = json.loads((root / "provenance/time_alignment_audit.json").read_text(encoding="utf-8"))
    sources = [r for r in audit["metadata"] if r["file"] == "aqs_sites_20260923.zip"]
    require(len(sources) == 1, "Expected one frozen EPA sites source")
    path = root / "data/aqs_metadata_sources" / sources[0]["file"]
    require(digest(path) == sources[0]["sha256"], "EPA sites ZIP checksum mismatch")
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
        require(len(names) == 1, "Expected one metadata CSV")
        with archive.open(names[0]) as stream:
            sites = pd.read_csv(stream, dtype=str, low_memory=False, encoding="utf-8-sig")
    sitecol = "Site Number" if "Site Number" in sites else "Site Num"
    sites["station_id"] = (sites["State Code"].str.zfill(2) + "-" +
                           sites["County Code"].str.zfill(3) + "-" + sites[sitecol].str.zfill(4))
    used = stations[["city", "station_id"]].drop_duplicates()
    merged = used.merge(sites[["station_id", "GMT Offset"]], on="station_id", how="left",
                        validate="many_to_one")
    merged["offset"] = pd.to_numeric(merged["GMT Offset"], errors="raise")
    require(merged.offset.notna().all(), "Missing AQS standard offset")
    require(merged.groupby("city").offset.nunique().eq(1).all(), "Conflicting within-city offsets")
    offsets = merged.groupby("city").offset.first().to_dict()
    expected = {r["city"]: r["epa_standard_offset_hours"] for r in audit["weather"]}
    require(offsets == expected and len(offsets) == 11, "AQS ZIP does not reproduce recorded city offsets")
    selected = pd.read_csv(root / "provenance/city_site_metadata.csv", dtype={"station_id": str})
    local = merged.merge(selected[["city", "station_id", "gmt_offset_hours"]],
                         on=["city", "station_id"], how="outer", validate="one_to_one", indicator=True)
    require(local._merge.eq("both").all() and local.offset.eq(local.gmt_offset_hours).all(),
            "Selected site metadata does not match the raw EPA ZIP")
    return offsets


def validate_hourly(payload):
    require(payload.get("utc_offset_seconds") == 0, "Source is not UTC")
    require(payload.get("timezone") in {"GMT", "UTC", "Etc/GMT", "Etc/UTC"}, "Unexpected source timezone")
    require(payload.get("hourly_units") == UNITS, "Unexpected hourly units or variables")
    hourly = pd.DataFrame(payload["hourly"])
    require(set(hourly.columns) == {"time", *HOURS}, "Unexpected hourly columns")
    values = hourly[HOURS].to_numpy(dtype=float)
    require(np.isfinite(values).all(), "Missing or nonfinite hourly value")
    stamps = pd.to_datetime(hourly.time, errors="raise")
    expected = pd.date_range("2018-12-31", "2026-01-01 23:00:00", freq="h")
    require(pd.DatetimeIndex(stamps).equals(expected), "Hourly source is incomplete, duplicated or unordered")
    return hourly


def compare_daily(daily, reference):
    """Compare every key and every serialized numerical value, not a sample."""
    expected_columns = ["date", *FIELDS, "city"]
    require(list(daily.columns) == expected_columns, "Unexpected reconstructed columns")
    require(list(reference.columns) == expected_columns, "Unexpected reference columns")
    rebuilt = daily.copy()
    rebuilt["date"] = pd.to_datetime(rebuilt.date).dt.strftime("%Y-%m-%d")
    order = ["city", "date"]
    rebuilt = rebuilt.sort_values(order).reset_index(drop=True)
    reference = reference.sort_values(order).reset_index(drop=True)
    require(len(reference) == len(rebuilt) == 28127, "Expected 28,127 daily records")
    require(not reference.duplicated(order).any() and not rebuilt.duplicated(order).any(), "Duplicate daily keys")
    require(rebuilt[order].equals(reference[order]), "Daily date/city keys differ")
    checks = {}
    for field in FIELDS:
        a, b = rebuilt[field].to_numpy(float), reference[field].to_numpy(float)
        require(np.isfinite(a).all() and np.isfinite(b).all(), "Missing daily value")
        delta = np.abs(a - b)
        checks[field] = dict(values=len(a), not_bit_equal=int(np.count_nonzero(a != b)),
                             max_absolute_difference=float(delta.max()),
                             above_tolerance=int(np.count_nonzero(delta > ATOL)))
        require(not (delta > ATOL).any(), f"Daily numeric mismatch: {field}: {delta.max()}")
    return checks


def output_target(root, output):
    output = output.resolve()
    require(output != root and output not in root.parents and output != Path(output.anchor),
            "Output must be a new dedicated directory")
    for part in ("data", "scripts", "provenance", "results", "figures", "manuscript"):
        protected = root / part
        require(output != protected and protected not in output.parents and output not in protected.parents,
                "Output overlaps package inputs or reference artifacts")
    require(not output.exists(), "Output already exists; choose a fresh directory")
    return output


def write_new(path, body):
    require(not path.exists(), f"Refusing to replace existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(body)


def rebuild(root, output=None, report=None):
    root = root.resolve()
    if output is not None:
        output = output_target(root, output)
    if report is not None:
        require(not report.exists(), "Report exists; choose a new report filename")
    verified = check_inputs(root)
    stations_path = root / "data/stations/station_daily.csv"
    stations = pd.read_csv(stations_path, dtype={"station_id": str}, float_precision="round_trip")
    require(not stations.duplicated(["city", "station_id", "date"]).any(), "Duplicate station day")
    require(stations.no2_ppb.notna().all(), "Missing station NO2")
    offsets = site_offsets(root, stations)
    audit = json.loads((root / "provenance/time_alignment_audit.json").read_text(encoding="utf-8"))
    pieces = []
    n_hours = 0
    for rec in audit["weather"]:
        path = inside(root, "data/weather_hourly_utc/" + rec["file"])
        require(digest(path) == rec["sha256"], "Weather source checksum mismatch")
        payload = json.loads(path.read_text(encoding="utf-8"))
        hourly = validate_hourly(payload)
        daily = aggregate(hourly, offsets[rec["city"]], accumulation_shift=True)
        daily["city"] = rec["city"]
        require(len(daily) == 2557 and daily[FIELDS].notna().all().all(), "Incomplete local-standard days")
        pieces.append(daily)
        n_hours += len(hourly)
    daily = pd.concat(pieces, ignore_index=True).sort_values(["city", "date"])
    reference_path = root / "data/weather/weather_daily.csv"
    reference = pd.read_csv(reference_path, float_precision="round_trip")
    checks = compare_daily(daily, reference)
    body = daily.to_csv(index=False).encode("utf-8")
    result = dict(status="PASS", scope="weather raw-to-derived and NO2 input identity only",
        input_files_hash_verified=verified, utc_hours=n_hours, city_days=len(daily),
        numeric_values_checked=len(daily) * len(FIELDS), absolute_tolerance=ATOL,
        all_values_bit_equal=all(c["not_bit_equal"] == 0 for c in checks.values()),
        csv_byte_identical=body == reference_path.read_bytes(), per_variable=checks,
        fixed_aqs_standard_offsets=offsets, station_days=len(stations),
        station_sites=int(stations.station_id.nunique()), station_sha256=digest(stations_path),
        reference_weather_sha256=digest(reference_path),
        rebuilt_weather_sha256=hashlib.sha256(body).hexdigest(),
        final_model_reproduction="NOT_RUN", publication="NOT_PERFORMED")
    # Recheck source hashes before writing any derived artifact.
    check_inputs(root)
    if output is not None:
        write_new(output / "weather/weather_daily.csv", body)
        write_new(output / "stations/station_daily.csv", stations_path.read_bytes())
        write_new(output / "provenance/time_alignment_audit.json",
                  (root / "provenance/time_alignment_audit.json").read_bytes())
        result["no2_action"] = "Byte-preserving copy of included derived NO2, not reconstruction of national AQS files"
    if report is not None:
        write_new(report, (json.dumps(result, indent=2, allow_nan=False) + "\n").encode("utf-8"))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, default=PACKAGE)
    parser.add_argument("--output", type=Path, help="Optional fresh derived-data directory")
    parser.add_argument("--report", type=Path, help="Optional new JSON report; never overwrite")
    args = parser.parse_args()
    print(json.dumps(rebuild(args.package_root, args.output, args.report), indent=2))


if __name__ == "__main__":
    main()
