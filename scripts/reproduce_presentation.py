"""Regenerate all three figures and ten article tables offline; no model fitting."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from release_cli import PACKAGE, disable_network, prepare_output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, default=PACKAGE / "results")
    parser.add_argument("--station-daily", type=Path, default=PACKAGE / "data/stations/station_daily.csv")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    disable_network()
    if args.output.exists():
        raise FileExistsError("Use a fresh output directory")
    source_record = json.loads((PACKAGE / "provenance/presentation_staging.json").read_text(encoding="utf-8"))
    for name, item in source_record["scripts"].items():
        if hashlib.sha256((PACKAGE / "scripts" / name).read_bytes()).hexdigest() != item["portable_sha256"]:
            raise ValueError(f"Generation code changed since reviewed path-only adaptation: {name}")
    analysis, daily = args.analysis.resolve(), args.station_daily.resolve()
    out = prepare_output(args.output, ["run_manifest.json"], (analysis, daily))
    jobs = [
        ("wasp_article_tables.py", ["--analysis", str(analysis), "--output", str(out / "tables")]),
        ("wasp_station_map.py", ["--station-daily", str(daily), "--output", str(out / "figures")]),
        ("wasp_result_figures.py", ["--analysis", str(analysis), "--output", str(out / "figures")]),
    ]
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(out / "matplotlib_cache")
    env["PYTHONIOENCODING"] = "utf-8"
    records = []
    for script, arguments in jobs:
        print(f"Reproducing {script}", flush=True)
        command = [sys.executable, "-B", str(PACKAGE / "scripts" / script), *arguments]
        run = subprocess.run(command, env=env, capture_output=True, text=True, encoding="utf-8")
        (out / (script + ".stdout.log")).write_text(run.stdout, encoding="utf-8")
        (out / (script + ".stderr.log")).write_text(run.stderr, encoding="utf-8")
        records.append(dict(script=script, returncode=run.returncode))
        if run.returncode:
            print(run.stderr, file=sys.stderr)
            raise RuntimeError(f"Generation failed: {script}; see output logs")
    record = dict(status="GENERATED_NOT_YET_COMPARED", jobs=records, published=False,
                  analysis=str(analysis), station_daily=str(daily), model_fitting=False)
    (out / "run_manifest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
