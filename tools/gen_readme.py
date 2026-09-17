#!/usr/bin/env python3
"""The extensions table in README.md, built from what the flake actually contains.

This table used to be typed by hand, and it drifted the first time anyone touched it —
rows naming licences and repositories nobody re-read. Everything in it now comes from
`meta` and `passthru`, via `nix/lib/addon-meta.nix`, so a row can only say what the
package says.

Two modes, one renderer:

    gen_readme.py --meta m.json --readme README.md --write
    gen_readme.py --meta m.json --readme README.md --check

`--check` is what runs in `nix flake check` and in CI. `--write` is what you run after
adding an addon. They render from the same function, so a README that passes the check is
byte-identical to one the writer would produce.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BEGIN = "<!-- BEGIN GENERATED EXTENSIONS -->"
END = "<!-- END GENERATED EXTENSIONS -->"


def origin_cell(origin: str, homepage: str | None) -> str:
    """The "Where it comes from" column.

    Three answers, because there are three ways an addon gets here: FreeCAD's catalogue,
    a repository of this project's own that arrives as a flake input, or somebody else's
    that is packaged directly. The third is credited by name, read off the URL rather
    than written down, so it cannot name the wrong person.
    """
    if origin == "catalogue":
        return "FreeCAD's catalogue"
    if not homepage:
        return origin
    if origin == "own repo":
        return f"[its own repo]({homepage})"
    owner = homepage.rstrip("/").split("/")
    return (
        f"[{owner[-2]}]({homepage})" if len(owner) >= 2 else f"[upstream]({homepage})"
    )


# Categories in this order, then any that appear in the data but not here — so adding one
# in `nix/lib/addons.nix` shows up rather than being dropped, but the established order
# does not reshuffle.
CATEGORY_ORDER = [
    "Modelling",
    "Assemblies and mechanical parts",
    "3D printing",
    "KiCad and electronics",
    "Interface",
    "Automation",
]

REPO = "github:aldoborrero/freecad.nix"


def entry(name: str, info: dict) -> str:
    """One addon, as a collapsed block."""
    lines = [
        "<details>",
        f"<summary><strong>{name}</strong> — {info['description']}</summary>",
        "",
        f"- **Source**: {origin_cell(info['origin'], info.get('homepage'))}",
        f"- **Version**: {info['version']}",
        f"- **Licence**: {info['license']}",
    ]

    # What you actually type. An addon is not run, it is handed to FreeCAD — and for the
    # ones whose module sits below the store root, the path has a suffix.
    path = f'"$(nix build --no-link --print-out-paths {REPO}#{name})'
    path += f'/{info["modulePath"]}"' if info.get("modulePath") else '"'
    lines += [
        f"- **Use**: `nix run {REPO}#freecad-unstable -- --module-path {path}`",
        f"- **Nix**: [{info['sourceFile']}]({info['sourceFile']})",
        "",
        "</details>",
    ]
    return "\n".join(lines)


def render(meta: dict) -> str:
    seen = {info["category"] for info in meta.values()}
    ordered = [c for c in CATEGORY_ORDER if c in seen]
    ordered += sorted(c for c in seen if c not in CATEGORY_ORDER)

    blocks = []
    for category in ordered:
        blocks.append(f"### {category}\n")
        # Alphabetical within a category, so adding one does not move the others.
        for name in sorted(n for n, i in meta.items() if i["category"] == category):
            blocks.append(entry(name, meta[name]))
            blocks.append("")
    return "\n".join(blocks).rstrip("\n")


def splice(readme: str, block: str) -> str:
    if BEGIN not in readme or END not in readme:
        raise SystemExit(f"README has no {BEGIN} / {END} markers")
    before = readme.split(BEGIN)[0]
    after = readme.split(END)[-1]
    return f"{before}{BEGIN}\n\n{block}\n\n{END}{after}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--meta", required=True, type=Path, help="eval-time facts, as JSON")
    ap.add_argument("--readme", required=True, type=Path)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = ap.parse_args()

    meta = json.loads(args.meta.read_text(encoding="utf-8"))
    readme = args.readme.read_text(encoding="utf-8")
    wanted = splice(readme, render(meta))

    if args.check:
        if wanted != readme:
            print(
                "README.md's extensions table is out of date.\n"
                "  Regenerate it with:  nix run .#gen-readme",
                file=sys.stderr,
            )
            return 1
        print(f"README.md is current ({len(meta)} addons)")
        return 0

    if wanted == readme:
        print("README.md already current")
        return 0
    args.readme.write_text(wanted, encoding="utf-8")
    print(f"rewrote {args.readme} ({len(meta)} addons)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
