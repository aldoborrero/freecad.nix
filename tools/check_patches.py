#!/usr/bin/env python3
"""Apply this repo's patches to a FreeCAD tree and judge how well they landed.

Run from `nix flake check` and from whatever else wants the answer; it takes paths
and prints a report, so it needs no CI in particular.

The distinction it draws is the whole point:

  * **A failed hunk** is unambiguous — the patch no longer applies. Fail.
  * **An offset** is noise. Upstream inserted lines above the anchor and `patch`
    found it anyway. Reported, never fatal; they reach 415 lines already.
  * **Fuzz** is the dangerous middle. It means the context did *not* match and the
    hunk was positioned by approximation, which is how a change lands in the wrong
    function while the build stays green. Every fuzzed hunk has to be declared in
    `expected.json` — i.e. somebody looked at where it went — and any fuzz that is
    not declared fails the check.

So a bump that merely shifts line numbers passes silently, and a bump that starts
guessing where our code goes stops and asks for eyes.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# "Hunk #1 succeeded at 26 with fuzz 2." / "Hunk #2 succeeded at 1471 (offset 24 lines)."
HUNK = re.compile(
    r"Hunk #(?P<hunk>\d+) succeeded at (?P<line>\d+)"
    r"(?: with fuzz (?P<fuzz>\d+))?"
    r"(?: \(offset (?P<offset>-?\d+) lines?\))?"
)
FILE = re.compile(r"^patching file (?P<path>.+)$", re.MULTILINE)
FAILED = re.compile(r"Hunk #(?P<hunk>\d+) FAILED")
# A patch reached through the Nix store is named `<32 hash chars>-custom-titlebar.patch`,
# and the same file read from the work tree is not. Keys have to survive both, or every
# entry in expected.json goes stale the moment the check runs under `nix flake check`.
STORE_PREFIX = re.compile(r"^[0-9a-df-np-sv-z]{32}-")


class Landing:
    """Where one hunk ended up."""

    def __init__(
        self, patch: str, file: str, hunk: int, line: int, fuzz: int, offset: int
    ):
        self.patch, self.file, self.hunk = patch, file, hunk
        self.line, self.fuzz, self.offset = line, fuzz, offset

    @property
    def key(self) -> str:
        return f"{self.patch}::{self.file}::{self.hunk}"


def apply_one(tree: Path, patch: Path) -> tuple[list[Landing], list[str]]:
    """Apply `patch` inside `tree`, returning where each hunk landed and what failed."""
    proc = subprocess.run(
        ["patch", "-p1", "--forward", "--no-backup-if-mismatch", "-i", str(patch)],
        cwd=tree,
        capture_output=True,
        text=True,
        check=False,
    )
    out = proc.stdout + proc.stderr

    landings: list[Landing] = []
    failures: list[str] = []
    current = "?"
    for line in out.splitlines():
        if m := FILE.match(line):
            current = m.group("path")
            continue
        if m := FAILED.search(line):
            name = STORE_PREFIX.sub("", patch.name)
            failures.append(f"{name}::{current}::{m.group('hunk')}")
            continue
        if m := HUNK.search(line):
            landings.append(
                Landing(
                    STORE_PREFIX.sub("", patch.name),
                    current,
                    int(m.group("hunk")),
                    int(m.group("line")),
                    int(m.group("fuzz") or 0),
                    int(m.group("offset") or 0),
                )
            )
    return landings, failures


def check(source: Path, patches: list[Path], expected: dict[str, str]) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "tree"
        shutil.copytree(source, tree, symlinks=True)
        subprocess.run(["chmod", "-R", "u+w", str(tree)], check=True)

        landings: list[Landing] = []
        failures: list[str] = []
        for patch in patches:
            got, bad = apply_one(tree, patch)
            landings += got
            failures += bad

    worst = max((abs(x.offset) for x in landings), default=0)
    fuzzed = [x for x in landings if x.fuzz]
    print(f"  {len(landings)} hunks applied, largest offset {worst} lines")

    problems: list[str] = []
    for name in failures:
        problems.append(f"hunk did not apply at all: {name}")

    for x in fuzzed:
        why = expected.get(x.key)
        if why is None:
            problems.append(
                f"undeclared fuzz {x.fuzz} at {x.key} (landed at line {x.line}).\n"
                f"      patch guessed where this goes. Look at where it landed, and if it is\n"
                f"      right, add it to expected.json with a note saying you looked."
            )
        else:
            print(f"  fuzz {x.fuzz} at {x.key} — declared: {why}")

    stale = set(expected) - {x.key for x in fuzzed}
    for key in sorted(stale):
        problems.append(
            f"expected.json declares fuzz at {key}, but it applied cleanly.\n"
            f"      Drop the entry: a stale exemption hides the next real one."
        )

    sys.stdout.flush()  # or the errors below land above the summary
    for problem in problems:
        print(f"  ERROR: {problem}", file=sys.stderr)
    return 1 if problems else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, type=Path, help="unpacked FreeCAD tree")
    ap.add_argument("--patch", required=True, action="append", type=Path)
    ap.add_argument("--expected", type=Path, help="JSON of declared, looked-at fuzz")
    args = ap.parse_args()

    expected: dict[str, str] = {}
    if args.expected and args.expected.exists():
        expected = json.loads(args.expected.read_text(encoding="utf-8"))
        # The file carries its own explanation; that is prose, not an exemption.
        expected.pop("_comment", None)

    return check(args.source, args.patch, expected)


if __name__ == "__main__":
    sys.exit(main())
