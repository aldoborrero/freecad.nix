#!/usr/bin/env python3
"""Does this addon actually contain what its package.xml claims?

The failure this exists to prevent is the one that keeps happening around FreeCAD: a
build that succeeds while producing nothing. An addon whose entry point is missing
installs fine, `--module-path` points at it fine, FreeCAD starts fine, and the workbench
simply is not in the list. Nothing warns. So the claim is checked where it can still
fail loudly — during the build.

FreeCAD finds a workbench three different ways, and all are legitimate:

  * `InitGui.py` at the top of the module directory. `FreeCADInit.py` execs it directly.
    kicadStepUp and this repo's Timeline are shaped this way.
  * `<subdir>/InitGui.py`, where `DirModGui.process_metadata` computes `<subdir>` from
    `package.xml` as `Subdirectory or Name`. Such an addon's root looks exactly like the
    broken shape this file exists to catch, so the manifest is parsed for more than its
    content kinds. Nothing packaged here is shaped this way today; the catalogue has
    them, and without the rule adding one is a false failure.
  * `freecad/<pkg>/init_gui.py`, with no `InitGui.py` anywhere. This works because every
    `--module-path` directory also lands on `sys.path`, so FreeCAD can walk
    `pkgutil.iter_modules(freecad.__path__)` and find the namespace package. Gridfinity,
    Curves and FusionLook are shaped this way.

A `preferencepack` is different again: `PreferencePackManager` scans module paths for a
directory containing a `<name>.cfg`, so what must exist is that pair, not an entry point.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def workbench_subdirs(root: ET.Element | None) -> tuple[str, ...]:
    """Where each `<workbench>` in a package.xml says its `InitGui.py` lives.

    Mirrors `DirModGui.process_metadata`: `Subdirectory or Name`, split on either
    separator so `./Code` resolves the same way FreeCAD resolves it.
    """
    if root is None:
        return ()
    content = root.find("{*}content")
    if content is None:
        return ()
    found = []
    for workbench in content.findall("{*}workbench"):
        raw = (workbench.findtext("{*}subdirectory") or "").strip()
        if not raw:
            raw = (workbench.findtext("{*}name") or "").strip()
        if raw:
            found.append(str(Path(*re.split(r"[/\\]+", raw))))
    return tuple(found)


def workbench_entry_point(root: Path, subdirs: tuple[str, ...] = ()) -> str | None:
    if (root / "InitGui.py").is_file():
        return "InitGui.py"
    for subdir in subdirs:
        if (root / subdir / "InitGui.py").is_file():
            return f"{subdir}/InitGui.py"
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
    subdirs: tuple[str, ...] = ()

    # Prefer what the addon itself says, when it shipped a package.xml. It is also the
    # only place the entry point's subdirectory can come from, so parse the whole root
    # rather than just `<content>`.
    manifest = root / "package.xml"
    if manifest.is_file():
        try:
            declared = ET.parse(manifest).getroot()
        except ET.ParseError as exc:
            print(f"  package.xml is present but unparseable: {exc}", file=sys.stderr)
            return 1
        subdirs = workbench_subdirs(declared)
        content = declared.find("{*}content")
        if content is not None:
            kinds = sorted({child.tag.split("}")[-1] for child in content})

    if not kinds:
        # Nothing declared *and* no entry point means this is not a module directory at
        # all — which is exactly what pointing at the wrong path looks like. Timeline's
        # store root, for instance, is a container holding `Mod/Timeline`; checking it
        # instead of the module used to pass here with "nothing to verify", so the check
        # could not catch the one mistake it exists for.
        found = workbench_entry_point(root, subdirs)
        if found is None:
            print(
                f"  ERROR: {root} declares no content and has no entry point.\n"
                f"      This is not a FreeCAD module directory. If the package keeps its\n"
                f"      module below the root, point at that path — see passthru.modulePath.",
                file=sys.stderr,
            )
            return 1
        print(f"  no content declared, but an entry point is present: {found}")
        return 0

    problems: list[str] = []
    for kind in kinds:
        if kind == "workbench":
            found = workbench_entry_point(root, subdirs)
            if found:
                print(f"  workbench -> {found}")
            else:
                problems.append(
                    "package.xml declares a workbench, but there is no InitGui.py at the\n"
                    "      top, none under "
                    + (f"{list(subdirs)}" if subdirs else "any declared subdirectory")
                    + ", and no\n"
                    "      freecad/*/init_gui.py. FreeCAD would load this and show nothing."
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
            # macro, other, depend: no layout rule to assert, but say what is actually
            # there. The kinds are not applied consistently in the wild — two addons
            # that both add UI from an InitGui.py without registering a Gui::Workbench
            # can declare `workbench` and `other` respectively — so the entry point is
            # worth printing even where nothing is required.
            found = workbench_entry_point(root, subdirs)
            print(f"  {kind} -> no layout rule; entry point is {found or 'none'}")

    for problem in problems:
        print(f"  ERROR: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
