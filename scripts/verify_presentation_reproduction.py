"""Compare every regenerated figure/table; ignore only enumerated runtime metadata."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from PIL import Image

from release_cli import PACKAGE


VECTOR_DATE = {
    ".pdf": (rb"/CreationDate\s*\(D:[^)]*\)", b"/CreationDate (DATE)"),
    ".svg": (rb"<dc:date>[^<]*</dc:date>", b"<dc:date>DATE</dc:date>"),
    ".eps": (rb"(?m)^%%CreationDate:.*$", b"%%CreationDate: DATE"),
}
AUDIT_RUNTIME = {"started_utc", "completed_utc", "elapsed_seconds", "script_sha256", "tests"}


def digest(body):
    return hashlib.sha256(body).hexdigest()


def normalize_vector(body, suffix):
    pattern, replacement = VECTOR_DATE[suffix]
    values = re.findall(pattern, body)
    if len(values) != 1:
        raise ValueError("Expected exactly one known vector generation-date field")
    return re.sub(pattern, replacement, body), values[0].decode("ascii")


def normalize_station_report(text, package):
    timestamp = re.findall(r"(?m)^Generated \(UTC\): .+$", text)
    if len(timestamp) != 1:
        raise ValueError("Expected one station-report runtime timestamp")
    text = text.replace(timestamp[0], "Generated (UTC): RUNTIME_TIMESTAMP")
    head, marker, tail = text.partition("Read-only inputs (SHA-256 at generation):")
    if not marker:
        raise ValueError("Station report has no input-provenance section")
    source_paths = [package / "data/stations/station_daily.csv", package / "provenance/city_site_metadata.csv",
                    package / "provenance/city_metadata.json"]
    expected = {p.name: digest(p.read_bytes()) for p in source_paths}
    found, output_names, changes = {}, [], [timestamp[0]]
    lines = []
    for line in tail.splitlines():
        match = re.fullmatch(r"\| (.+) \| ([0-9a-f]{64}) \|", line)
        if match:
            source, sha = match.groups()
            name = source.replace("\\", "/").rsplit("/", 1)[-1]
            if name not in expected or sha != expected[name] or name in found:
                raise ValueError("Station-report input identities do not match the package")
            found[name] = sha
            changes.append(source)
            line = f"| INPUT/{name} | {sha} |"
        elif line.startswith("- "):
            name = line[2:].replace("\\", "/").rsplit("/", 1)[-1]
            output_names.append(name)
            changes.append(line[2:])
            line = "- OUTPUT/" + name
        lines.append(line)
    expected_outputs = {"fig1_station_locations" + s for s in
                        (".png", ".pdf", ".svg", ".eps", "_preview.png", "_metadata.md")}
    if found != expected or len(output_names) != 6 or set(output_names) != expected_outputs:
        raise ValueError("Station-report input/output inventory differs")
    return head + marker + "\n".join(lines), changes


def compare_ledger(left, right, reference_audit, reproduced_audit):
    if left["input_audit"] != reference_audit or right["input_audit"] != reproduced_audit:
        raise ValueError("Table ledger does not record its actual analysis audit")
    a, b = dict(reference_audit), dict(reproduced_audit)
    changes = []
    for key in sorted(AUDIT_RUNTIME):
        av, bv = a.pop(key), b.pop(key)
        if av != bv:
            changes.append(dict(field="input_audit." + key, reference=av, reproduced=bv))
    if a != b:
        raise ValueError("Scientific table input-audit fields differ")
    a, b = {k: v for k, v in left.items() if k != "input_audit"}, {k: v for k, v in right.items() if k != "input_audit"}
    if a != b:
        raise ValueError("At least one table/ledger scientific value differs")
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, default=PACKAGE)
    parser.add_argument("--reproduced", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    package, reproduced = args.package_root.resolve(), args.reproduced.resolve()
    if args.report.exists():
        raise FileExistsError("Do not replace an existing verification report")
    stage = json.loads((package / "provenance/presentation_staging.json").read_text(encoding="utf-8"))
    actual = {str(p.relative_to(reproduced)).replace("\\", "/") for d in ("figures", "tables")
              for p in (reproduced / d).iterdir() if p.is_file()}
    if actual != set(stage["artifacts"]):
        raise ValueError("Regenerated artifact inventory differs")
    audits = [json.loads(p.read_text(encoding="utf-8")) for p in
              (package / "results/analysis_audit.json", args.analysis / "analysis_audit.json")]
    results, metadata = [], []
    for name, item in sorted(stage["artifacts"].items()):
        a, b = package / name, reproduced / name
        left, right = a.read_bytes(), b.read_bytes()
        if digest(left) != item["sha256"] or len(left) != item["bytes"]:
            raise ValueError(f"Frozen presentation reference changed: {name}")
        record = dict(file=name, reference_sha256=digest(left), reproduced_sha256=digest(right),
                      byte_identical=left == right)
        if a.suffix in VECTOR_DATE:
            x, date_a = normalize_vector(left, a.suffix)
            y, date_b = normalize_vector(right, a.suffix)
            if x != y:
                raise ValueError(f"Vector content differs beyond its generation date: {name}")
            record["exact_after_generation_date_normalization"] = True
            metadata.append(dict(file=name, reference=date_a, reproduced=date_b, ignored="generation date only"))
        elif name == "tables/result_ledger.json":
            metadata.extend(compare_ledger(json.loads(left), json.loads(right), *audits))
            record["all_scientific_fields_exact"] = True
        elif name.endswith("_metadata.md"):
            x, meta_a = normalize_station_report(left.decode("utf-8"), package)
            y, meta_b = normalize_station_report(right.decode("utf-8"), package)
            if x != y:
                raise ValueError("Station metadata report differs beyond timestamp and verified I/O paths")
            record["all_scientific_text_exact"] = True
            metadata.append(dict(file=name, reference=meta_a, reproduced=meta_b,
                                 ignored="runtime timestamp and hash-validated input/output locations only"))
        elif left != right:
            raise ValueError(f"Byte mismatch: {name}")
        if a.suffix == ".png":
            # Byte equality already entails equality of every pixel and metadata field.
            with Image.open(b) as picture:
                record.update(pixel_equality="EXACT_FROM_IDENTICAL_PNG_BYTES", dimensions=list(picture.size),
                              dpi=picture.info.get("dpi"))
        record["status"] = "PASS"
        results.append(record)
    report = dict(status="PASS", figures=3, markdown_tables=10, png_files_byte_identical=6,
                  vector_files_exact_except_generation_date=9, artifacts_compared=27,
                  scientific_ledger_and_station_metadata_exact=True, numerical_tolerance=None,
                  execution_metadata_differences=metadata, files=results,
                  manuscript_included=False, published=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"files", "execution_metadata_differences"}}, indent=2))


if __name__ == "__main__":
    main()
