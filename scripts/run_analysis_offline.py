"""Run frozen WASP code with explicit paths and Python-level networking disabled."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys


def main():
    package = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=package / "data")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test and args.output.exists():
        raise FileExistsError("Choose a fresh analysis output directory; existing work is never replaced")
    freeze = json.loads((package / "provenance/analysis_staging.json").read_text(encoding="utf-8"))
    for name, expected in freeze["confirmed_scripts"].items():
        found = hashlib.sha256((package / "scripts" / name).read_bytes()).hexdigest()
        if found != expected:
            raise ValueError(f"Owner-confirmed frozen script changed: {name}")

    def no_network(event, arguments):
        if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto", "socket.bind"}:
            raise RuntimeError("Networking is disabled during packaged analysis reproduction")

    sys.addaudithook(no_network)
    sys.path.insert(0, str(package / "scripts"))
    script = package / "scripts/wasp_analysis.py"
    sys.argv = [str(script), "--input-root", str(args.input_root.resolve()),
                "--output", str(args.output.resolve()), "--bootstrap", "5000"]
    if args.self_test:
        sys.argv.append("--self-test")
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
