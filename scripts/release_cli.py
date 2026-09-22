"""Local-only I/O helpers; no statistical or rendering transformations."""
from __future__ import annotations

import os
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[1]


def plotting_environment():
    # Do not put Matplotlib's cache in a machine-specific user directory.
    # Users can supply MPLCONFIGDIR, e.g. when this package is read-only.
    os.environ.setdefault("MPLCONFIGDIR", str(PACKAGE / "verification_runs" / "matplotlib"))


def disable_network():
    def audit(event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto", "socket.bind"}:
            raise RuntimeError("This reproduction entry point does not permit network access")
    sys.addaudithook(audit)


def prepare_output(output, names, inputs=()):
    """Allow a shared fresh destination, but never overwrite a target or input."""
    output = Path(output).resolve()
    protected = [PACKAGE / name for name in ("data", "scripts", "provenance", "results", "figures", "tables")]
    protected.extend(Path(p).resolve() for p in inputs)
    if output == PACKAGE or output in PACKAGE.parents:
        raise ValueError("Output must not be the package or an ancestor")
    for source in protected:
        source = source.resolve()
        if output == source or output in source.parents or source in output.parents:
            raise ValueError(f"Output overlaps an input or distributed artifact: {source}")
    for name in names:
        if Path(name).name != name or name in {".", ".."}:
            raise ValueError("Output names must be simple filenames")
        if (output / name).exists() or (output / name).is_symlink():
            raise FileExistsError(f"Refusing to overwrite: {output / name}")
    output.mkdir(parents=True, exist_ok=True)
    return output
