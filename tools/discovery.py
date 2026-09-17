#!/usr/bin/env python3
"""Work out what can be moved forward, and how.

Emits one matrix entry per target, so a CI job can fan out over them and open a pull
request each. Prints JSON; sets `matrix` and `has-updates` as GitHub Actions outputs when
run under one, and logs them otherwise.

**Four routes, not one.** This is where it differs from the repositories this pattern
comes from, which have a single kind of package:

  `flake-input`  nixpkgs, blueprint, treefmt-nix, and the two addons that live in their
                 own repositories — moved with `nix flake update <input>`.
  `nix-update`   a package with a `src` this repo pins itself, declaring its quirks in
                 `nix/packages/<name>/nix-update-args`.
  `catalog`      an addon built from `nix/addons.json`, which FreeCAD's own catalogue
                 pins; moved with `tools/catalog.py update <CatalogName>`.
  `manual`       something no script can decide. Reported, never acted on.

**A versioned package with no route is an error**, not a silence. That is the whole point
of discovering rather than listing: adding a package and forgetting to say how it moves
should stop the job, not quietly leave it pinned forever. A package with no `version` at
all — `stepz`, whose source is in this repository — is exempt, because there is nothing
upstream to compare against.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

# Before importing `lib`: this is a script, run by path, and the CI that calls it has no
# reason to have set PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import ROOT, run, write_output

log = logging.getLogger("discovery")

# Pinned by hand on purpose, and reported so it cannot be forgotten: upstream's title-bar
# pull request is fetched at a `compare/<base>...<head>` URL, and moving it means reading
# what changed rather than taking whatever the branch now holds.
MANUAL = {
    "freecad-unstable-titlebar": (
        "FreeCAD#26766 is fetched at two pinned SHAs. Check the PR, then update both in "
        "nix/packages/freecad-unstable/default.nix. patches-apply reports the day it "
        "stops fitting the tag."
    ),
}


def flake_metadata() -> dict[str, Any]:
    result = run(["nix", "flake", "metadata", "--json"], capture=True)
    return dict(json.loads(result.stdout))


def root_inputs() -> list[str]:
    meta = flake_metadata()
    locks = meta["locks"]
    return sorted(locks["nodes"][locks["root"]].get("inputs", {}))


def packages(system: str) -> dict[str, dict[str, Any]]:
    """Every package, with the two passthru fields that decide its route."""
    expr = (
        "ps: builtins.mapAttrs (_: p: {"
        " version = p.version or null;"
        " catalogName = p.catalogName or null;"
        " }) ps"
    )
    result = run(
        ["nix", "eval", "--json", f".#packages.{system}", "--apply", expr],
        capture=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"could not read packages:\n{result.stderr}")
    return dict(json.loads(result.stdout))


def route(name: str, info: dict[str, Any], inputs: list[str]) -> str | None:
    """How this package moves, or None when it does not need to."""
    if info["version"] is None:
        return None  # local source; nothing upstream to track
    if name in inputs:
        return "flake-input"
    if info["catalogName"]:
        return "catalog"
    if (ROOT / "nix" / "packages" / name / "nix-update-args").is_file():
        return "nix-update"
    return "unroutable"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--system", default=None, help="defaults to this machine's")
    ap.add_argument(
        "--only", nargs="*", default=None, help="restrict to these target names"
    )
    ap.add_argument(
        "--exclude", nargs="*", default=[], help="targets handled by another workflow"
    )
    args = ap.parse_args()

    system = (
        args.system
        or subprocess.run(
            ["nix", "eval", "--impure", "--raw", "--expr", "builtins.currentSystem"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )

    inputs = root_inputs()
    found = packages(system)

    entries: list[dict[str, Any]] = []
    unroutable: list[str] = []

    for name, info in sorted(found.items()):
        kind = route(name, info, inputs)
        if kind is None:
            log.info("%s: no version, nothing to track", name)
            continue
        if kind == "unroutable":
            unroutable.append(name)
            continue
        entry = {"kind": kind, "name": name, "current": info["version"]}
        if kind == "catalog":
            entry["catalogName"] = info["catalogName"]
        entries.append(entry)

    # Inputs that are not also packages: nixpkgs and the build machinery.
    package_inputs = {e["name"] for e in entries if e["kind"] == "flake-input"}
    for name in inputs:
        if name not in package_inputs:
            entries.append({"kind": "flake-input", "name": name, "current": None})

    for name, why in MANUAL.items():
        entries.append({"kind": "manual", "name": name, "current": None, "note": why})

    if unroutable:
        raise SystemExit(
            "these packages declare a version but nothing says how to move them:\n  "
            + "\n  ".join(unroutable)
            + "\n\nGive each one a nix/packages/<name>/nix-update-args, or an entry in\n"
            "nix/addons.json, or make it a flake input. Leaving a package pinned by\n"
            "accident is the failure this check exists to prevent."
        )

    if args.only:
        entries = [e for e in entries if e["name"] in args.only]
    entries = [e for e in entries if e["name"] not in args.exclude]

    matrix = {"include": entries}
    print(json.dumps(matrix, indent=2))
    write_output("matrix", json.dumps(matrix))
    write_output("has-updates", "true" if entries else "false")

    by_kind: dict[str, int] = {}
    for entry in entries:
        by_kind[entry["kind"]] = by_kind.get(entry["kind"], 0) + 1
    log.info("%d targets: %s", len(entries), by_kind)
    return 0


if __name__ == "__main__":
    sys.exit(main())
