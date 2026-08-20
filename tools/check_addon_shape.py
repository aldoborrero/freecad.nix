#!/usr/bin/env python3
"""Does this addon actually contain what its package.xml claims?

The failure this exists to prevent is the one that keeps happening around FreeCAD: a
build that succeeds while producing nothing. An addon whose entry point is missing
installs fine, `--module-path` points at it fine, FreeCAD starts fine, and the workbench
simply is not in the list. Nothing warns. So the claim is checked where it can still
fail loudly — during the build.

FreeCAD finds a workbench two different ways, and both are legitimate:

  * `InitGui.py` at the top of the module directory. `FreeCADInit.py` execs it directly.
    kicadStepUp and this repo's Timeline are shaped this way.
  * `freecad/<pkg>/init_gui.py`, with no `InitGui.py` anywhere. This works because every
    `--module-path` directory also lands on `sys.path`, so FreeCAD can walk
    `pkgutil.iter_modules(freecad.__path__)` and find the namespace package. Gridfinity,
    Curves and FusionLook are shaped this way.

A `preferencepack` is different again: `PreferencePackManager` scans module paths for a
directory containing a `<name>.cfg`, so what must exist is that pair, not an entry point.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def workbench_entry_point(root: Path) -> str | None:
    if (root / "InitGui.py").is_file():
        return "InitGui.py"
    namespace = root / "freecad"
    if namespace.is_dir():
        for package in sorted(namespace.iterdir()):
            if (package / "init_gui.py").is_file():
                return f"freecad/{package.name}/init_gui.py"
    return None


def preference_pack(root: Path) -> str | None:
    """A pack is a directory holding `<its own name>.cfg`."""
    for entry in sorted(root.iterdir()):
        if entry.is_dir() and (entry / f"{entry.name}.cfg").is_file():
            return f"{entry.name}/{entry.name}.cfg"
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True, type=Path, help="the installed module dir")
    ap.add_argument(
        "--content",
        action="append",
        default=[],
        help="a content kind package.xml declares; repeat",
    )
    args = ap.parse_args()

    root: Path = args.root
    kinds = list(args.content)

    # Prefer what the addon itself says, when it shipped a package.xml.
    manifest = root / "package.xml"
    if manifest.is_file():
        try:
            content = ET.parse(manifest).getroot().find("{*}content")
            if content is not None:
                kinds = sorted({child.tag.split("}")[-1] for child in content})
        except ET.ParseError as exc:
            print(f"  package.xml is present but unparseable: {exc}", file=sys.stderr)
            return 1

    if not kinds:
        print("  no content declared anywhere; nothing to verify")
        return 0

    problems: list[str] = []
    for kind in kinds:
        if kind == "workbench":
            found = workbench_entry_point(root)
            if found:
                print(f"  workbench -> {found}")
            else:
                problems.append(
                    "package.xml declares a workbench, but there is no InitGui.py at the\n"
                    "      top and no freecad/*/init_gui.py. FreeCAD would load this and\n"
                    "      show nothing."
                )
        elif kind == "preferencepack":
            found = preference_pack(root)
            if found:
                print(f"  preferencepack -> {found}")
            else:
                problems.append(
                    "package.xml declares a preferencepack, but no directory here holds a\n"
                    "      matching <name>.cfg, which is what PreferencePackManager looks for."
                )
        else:
            # macro, other, depend: no layout this can meaningfully assert.
            print(f"  {kind} -> not checked (no layout rule)")

    for problem in problems:
        print(f"  ERROR: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
