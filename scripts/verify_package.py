"""Read-only verification of every inventoried file and untracked payload."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

EXCLUDE = {".git", "__pycache__", "verification_runs", "reproduced_data",
           "reproduced_results", "reproduced_figures", "reproduced_tables", "reproduced_presentation"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.package_root.resolve()
    manifest = json.loads((root / "SHA256SUMS.json").read_text(encoding="utf-8"))
    for name, expected in manifest.items():
        rel = PurePosixPath(name)
        if rel.is_absolute() or ".." in rel.parts or ":" in name or "\\" in name:
            raise ValueError("Invalid manifest path")
        path = root / name
        if path.is_symlink() or root not in path.resolve().parents:
            raise ValueError("External/symlink artifact")
        with path.open("rb") as stream:
            found = hashlib.file_digest(stream, "sha256").hexdigest()
        if found != expected:
            raise ValueError(f"Checksum mismatch: {name}")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*")
              if p.is_file() and not any(x in EXCLUDE for x in p.relative_to(root).parts)
              and p.name != "SHA256SUMS.json"}
    if actual != set(manifest):
        raise ValueError(f"Inventory differs: {sorted(actual ^ set(manifest))}")
    print(json.dumps(dict(status="PASS", files=len(manifest), published=False)))


if __name__ == "__main__":
    main()
