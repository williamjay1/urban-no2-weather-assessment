"""Strict complete-table/array comparison of two completed WASP analyses.

Scientific CSV, NPZ and JSON values must be identical. Only explicitly named
execution metadata may differ; every such difference is recorded in the report.
Neither reference nor reproduced results are edited by this verifier.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


RUNTIME_FIELDS = {
    "analysis_audit.json": {"started_utc", "completed_utc", "elapsed_seconds", "script_sha256", "tests"},
    "run_specification.json": {"started_utc", "script_sha256", "tests"},
    "verification_audit.json": {"audit_script_sha256", "executed_analysis_script_sha256"},
}
SOURCE_ONLY_PROVENANCE = {"FINAL_CODE_FREEZE.json"}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def check_manifest(root):
    items = json.loads((root / "output_manifest.json").read_text(encoding="utf-8"))
    for name, record in items.items():
        if Path(name).name != name:
            raise ValueError("Invalid output manifest path")
        path = root / name
        if path.stat().st_size != record["bytes"] or digest(path) != record["sha256"]:
            raise ValueError(f"Output manifest mismatch: {root.name}/{name}")


def assert_values(a, b):
    if a.shape != b.shape or a.dtype != b.dtype:
        raise ValueError(f"Array shape/dtype differs: {a.shape}/{a.dtype} versus {b.shape}/{b.dtype}")
    if np.issubdtype(a.dtype, np.number):
        same = np.array_equal(a, b, equal_nan=True)
    else:
        same = np.array_equal(a, b)
    if not same:
        raise ValueError("At least one array value differs (exact comparison)")


def compare(reference, reproduced, report):
    if report.exists():
        raise FileExistsError("Do not replace an existing verification report")
    check_manifest(reference)
    check_manifest(reproduced)
    audits = [json.loads((root / "analysis_audit.json").read_text(encoding="utf-8"))
              for root in (reference, reproduced)]
    for audit in audits:
        if not (audit["completed"] and audit["models"] == 20 and audit["pooled_contrasts"] == 98
                and audit["bootstrap_attempts"] == 5000 and audit["seed"] == 20260923
                and audit["all_input_hashes_unchanged"] and audit["all_bootstrap_attempts_accounted"]):
            raise ValueError("Incomplete analysis or mismatched fixed reproduction protocol")
        if (audit["tests"]["failures"] or audit["tests"]["errors"]
                or not all(audit["tests"]["legacy_tests"].values())):
            raise ValueError("Source or reproduced self-tests did not pass")
    freeze = json.loads((reference / "FINAL_CODE_FREEZE.json").read_text(encoding="utf-8"))
    if (audits[1]["script_sha256"] != freeze["sha256"]["wasp_analysis.py"]
            or audits[0]["script_sha256"] != freeze["original_executed_wasp_analysis_sha256"]
            or any(a["legacy_helper_sha256"] != freeze["sha256"]["calendar_station_analysis.py"] for a in audits)
            or audits[1]["tests"]["tests_run"] < audits[0]["tests"]["tests_run"]
            or audits[1]["tests"]["legacy_tests"] != audits[0]["tests"]["legacy_tests"]):
        raise ValueError("Owner-confirmed source identity or test continuity differs")
    scientific = lambda root: {p.name for p in root.iterdir() if p.is_file()
                               and p.suffix in {".csv", ".npz", ".json"}
                               and p.name != "output_manifest.json" and p.name not in SOURCE_ONLY_PROVENANCE}
    expected, actual = scientific(reference), scientific(reproduced)
    if expected != actual:
        raise ValueError(f"Scientific output file set differs: {sorted(expected ^ actual)}")
    results, runtime_changes, failures = [], [], []
    numeric_csv_cells = array_values = 0
    for name in sorted(expected):
        left, right = reference / name, reproduced / name
        result = dict(file=name, byte_identical=digest(left) == digest(right))
        try:
            if left.suffix == ".csv":
                a, b = [pd.read_csv(p, float_precision="round_trip", low_memory=False) for p in (left, right)]
                pd.testing.assert_frame_equal(a, b, check_exact=True, check_dtype=True, check_like=False)
                count = int(a.select_dtypes(include="number").size)
                numeric_csv_cells += count
                result.update(rows=len(a), columns=len(a.columns), numeric_cells=count)
            elif left.suffix == ".npz":
                with np.load(left, allow_pickle=False) as a, np.load(right, allow_pickle=False) as b:
                    if set(a.files) != set(b.files):
                        raise ValueError("NPZ key set differs")
                    count = 0
                    for key in a.files:
                        assert_values(a[key], b[key])
                        count += a[key].size
                    array_values += count
                    result.update(arrays=len(a.files), array_values=int(count))
            else:
                a, b = [json.loads(p.read_text(encoding="utf-8")) for p in (left, right)]
                for key in sorted(RUNTIME_FIELDS.get(name, set())):
                    av, bv = a.pop(key, None), b.pop(key, None)
                    if av != bv:
                        runtime_changes.append(dict(file=name, field=key, reference=av, reproduced=bv,
                            reason="Execution timestamp/runtime, confirmed portable script revision, or expanded passing tests; not a scientific result"))
                if a != b:
                    raise ValueError("Scientific JSON fields differ")
            result["status"] = "PASS"
        except (AssertionError, ValueError) as exc:
            result.update(status="FAIL", detail=str(exc)[:1600])
            failures.append(name)
        results.append(result)
    summary = pd.read_csv(reproduced / "model_summary.csv")
    if not summary.loc[summary.n_estimable_cities.lt(11), "estimate_ppb"].isna().all():
        failures.append("unavailable_11_city_estimates_not_preserved")
    result = dict(status="PASS" if not failures else "FAIL", comparison="exact; no numeric tolerance",
        files_compared=len(results), csv_files=sum(r["file"].endswith(".csv") for r in results),
        npz_files=sum(r["file"].endswith(".npz") for r in results),
        json_files=sum(r["file"].endswith(".json") for r in results),
        numeric_csv_cells_checked=numeric_csv_cells, npz_array_values_checked=int(array_values),
        source_and_reproduced_manifest_verified=True, models=20, pooled_contrasts=98,
        source_only_provenance=[dict(file=name, sha256=digest(reference / name),
            reason="Owner-authored freeze provenance; verified against run identities, not a generated scientific result")
            for name in sorted(SOURCE_ONLY_PROVENANCE)],
        seed=20260923, bootstrap_attempts_per_scheme=5000, episode_counts=audits[1]["episode_counts"],
        all_unavailable_11_city_points_preserved=not any("unavailable_" in f for f in failures),
        input_sha256=audits[1]["input_sha256"], source_analysis_script_sha256=audits[0]["script_sha256"],
        reproduced_analysis_script_sha256=audits[1]["script_sha256"],
        execution_metadata_differences=runtime_changes, failed_files=failures, files=results,
        figures_reproduced=False, manuscript_verified=False, published=False)
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"files", "execution_metadata_differences"}}, indent=2))
    return not failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--reproduced", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not compare(args.reference, args.reproduced, args.report):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
