"""Build and verify an inventory-only local ZIP. Never push or publish."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import zipfile

from verify_package import EXCLUDE


def sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    package, archive = args.package_root.resolve(), args.archive.resolve()
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    if archive.suffix != ".zip" or archive.name != package.name + ".zip":
        raise ValueError("Archive must use the package-directory name and .zip suffix")
    if archive == package or package in archive.parents:
        raise ValueError("Create the archive outside the source package")
    if archive.exists() or checksum.exists():
        raise FileExistsError("Do not overwrite an existing archive/checksum")
    status = json.loads((package / "RELEASE_STATUS.json").read_text(encoding="utf-8"))
    if status["artifact_complete"] is not True or status["local_verification"] != "PASS":
        raise ValueError("The local verification gates have not passed")
    for report in ("weather_reconstruction_check.json", "analysis_reproduction_check.json", "presentation_reproduction_check.json"):
        if json.loads((package / "provenance" / report).read_text(encoding="utf-8"))["status"] != "PASS":
            raise ValueError(f"Verification is not PASS: {report}")
    manifest_file = package / "SHA256SUMS.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    actual = {p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()
              and not any(x in EXCLUDE for x in p.relative_to(package).parts) and p.name != "SHA256SUMS.json"}
    if actual != set(manifest):
        raise ValueError("Package contents no longer match the sealed inventory")
    figure_pdfs = {"figures/" + stem + ".pdf" for stem in
                   ("fig1_station_locations", "fig2_city_contrasts", "fig3_sensitivity")}
    records = []
    for name, expected in sorted(manifest.items()):
        rel = PurePosixPath(name)
        if rel.is_absolute() or ".." in rel.parts or ":" in name or "\\" in name:
            raise ValueError("Invalid inventory path")
        path = package / name
        if path.is_symlink() or package not in path.resolve().parents or sha256(path) != expected:
            raise ValueError(f"Changed/external inventory artifact: {name}")
        if path.suffix.lower() == ".docx" or (path.suffix.lower() == ".pdf" and name not in figure_pdfs):
            raise ValueError("Unpublished full-text document is outside this package's scope")
        if any(part.lower() in {"manuscript", "submission"} for part in rel.parts):
            raise ValueError("Unpublished manuscript/submission material must not be packaged")
        records.append(dict(file=name, bytes=path.stat().st_size, sha256=expected))
    records.append(dict(file="SHA256SUMS.json", bytes=manifest_file.stat().st_size, sha256=sha256(manifest_file)))
    total = sum(r["bytes"] for r in records)
    if not archive.parent.is_dir() or shutil.disk_usage(archive.parent).free < 2 * total:
        raise RuntimeError("Archive parent must exist and have at least twice the uncompressed package size free")
    # Stable ZIP container timestamps are bookkeeping, not a publication date.
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as container:
        for record in records:
            body = (package / record["file"]).read_bytes()
            if hashlib.sha256(body).hexdigest() != record["sha256"]:
                raise RuntimeError("A source changed during compression; do not publish this partial archive")
            info = zipfile.ZipInfo(package.name + "/" + record["file"], (2026, 9, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            container.writestr(info, body, compresslevel=9)
    with zipfile.ZipFile(archive) as container:
        expected_names = {package.name + "/" + r["file"] for r in records}
        if set(container.namelist()) != expected_names or len(container.namelist()) != len(expected_names):
            raise ValueError("ZIP member inventory mismatch or duplicate member")
        for record in records:
            with container.open(package.name + "/" + record["file"]) as handle:
                if hashlib.file_digest(handle, "sha256").hexdigest() != record["sha256"]:
                    raise ValueError("ZIP member checksum mismatch")
    archive_sha = sha256(archive)
    with checksum.open("x", encoding="ascii", newline="\n") as handle:
        handle.write(archive_sha + "  " + archive.name + "\n")
    largest = max(records, key=lambda r: r["bytes"])
    print(json.dumps(dict(status="INVENTORY_VERIFIED_ARCHIVE", archive=str(archive),
        archive_bytes=archive.stat().st_size, archive_sha256=archive_sha, checksum_file=str(checksum),
        package_uncompressed_bytes=total, archived_files=len(records), largest_file=largest,
        files_over_100_decimal_MB=[r for r in records if r["bytes"] > 100_000_000],
        files_over_100_binary_MiB=[r for r in records if r["bytes"] > 100 * 1024**2],
        all_archived_members_sha256_verified=True, unpublished_full_text_excluded=True,
        publication_performed_by_this_command=False), indent=2))


if __name__ == "__main__":
    main()
