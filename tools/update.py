#!/usr/bin/env python3
"""Move one target forward, whichever way it moves.

Takes a single matrix entry from `discovery.py` and applies it, leaving the change in the
working tree. It commits nothing and pushes nothing: what to do with the result is the
calling CI's business, and this repository's CI is not GitHub's.

    tools/update.py --kind nix-update --name freecad-mcp
    tools/update.py --kind catalog --name gridfinity --catalog-name Gridfinity
    tools/update.py --kind flake-input --name nixpkgs
    tools/update.py --entry '{"kind": "...", "name": "..."}'      # straight from the matrix

Exit codes are the contract: **0 with changes, 0 without**, and non-zero only when the
attempt itself failed. `changed` is written as an output and printed, so a caller can
decide without parsing logs.

The one thing this does *not* do is decide whether the result is good. A bump that builds
is not a bump that works, and for `freecad-unstable` in particular a new weekly tag can
move code out from under three patches. That is what `nix flake check` is for, and why
the workflow that calls this must not auto-merge that target.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import ROOT, run, tree_state, write_output  # noqa: E402

log = logging.getLogger("update")


def nix_update_args(name: str) -> list[str]:
    """Per-package flags, from `nix/packages/<name>/nix-update-args`.

    Comment lines are for the reader; nix-update would choke on them.
    """
    path = ROOT / "nix" / "packages" / name / "nix-update-args"
    if not path.is_file():
        return []
    args: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            args += line.split()
    log.info("%s: extra nix-update args %s", name, args)
    return args


def by_nix_update(name: str) -> None:
    run(["nix-update", "--flake", name, *nix_update_args(name)])


def by_catalog(name: str, catalog_name: str) -> None:
    """The catalogue is the authority for these, not a tag guess.

    `tools/catalog.py update` re-downloads FreeCAD's catalogue, moves the addon to
    whatever commit it now pins, and prefetches the hash. It also keeps a licence that was
    resolved by hand rather than silently dropping it back to null.
    """
    run([sys.executable, str(ROOT / "tools" / "catalog.py"), "update", catalog_name])


def by_flake_input(name: str) -> None:
    run(["nix", "flake", "update", name])


def apply(entry: dict[str, Any]) -> None:
    kind, name = entry["kind"], entry["name"]
    if kind == "nix-update":
        by_nix_update(name)
    elif kind == "catalog":
        by_catalog(name, entry["catalogName"])
    elif kind == "flake-input":
        by_flake_input(name)
    elif kind == "manual":
        # Reported by discovery so it is not forgotten; acting on it needs a human to read
        # what changed upstream, which is exactly what a script must not guess at.
        raise SystemExit(f"{name} is pinned by hand and will not be moved here.")
    else:
        raise SystemExit(f"unknown kind {kind!r}")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--entry", help="a matrix entry as JSON")
    ap.add_argument("--kind")
    ap.add_argument("--name")
    ap.add_argument("--catalog-name", dest="catalogName")
    args = ap.parse_args()

    if args.entry:
        entry = json.loads(args.entry)
    elif args.kind and args.name:
        entry = {"kind": args.kind, "name": args.name, "catalogName": args.catalogName}
    else:
        ap.error("give --entry, or --kind and --name")

    head_before = run(["git", "rev-parse", "HEAD"], capture=True).stdout.strip()
    tree_before = tree_state()

    apply(entry)

    changed = tree_state() != tree_before
    if changed:
        diff = run(["git", "diff", "HEAD", "--stat"], capture=True).stdout.strip()
        log.info("%s moved:\n%s", entry["name"], diff)
    else:
        log.info("%s: already current", entry["name"])

    write_output("changed", "true" if changed else "false")
    write_output("target", entry["name"])
    print("true" if changed else "false")

    # A bump must not quietly rewrite history; this only ever touches the work tree.
    if run(["git", "rev-parse", "HEAD"], capture=True).stdout.strip() != head_before:
        raise SystemExit("something moved HEAD; this script must not commit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
