# Packaging extensions

[← Back to the README](../README.md)

## Adding an extension from the catalogue

Use the catalogue tools from the repository root, inside `nix develop`:

```bash
tools/catalog.py list --content workbench     # what exists
tools/catalog.py add Gridfinity               # lock it at what the catalogue pins
tools/catalog.py update                       # move locked addons forward
```

Then write the package — three lines, because everything else is in the lock:

```nix
# nix/packages/gridfinity.nix
{ pkgs, flake, ... }:
flake.lib.mkAddon { inherit pkgs; } "Gridfinity" { }
```

Add it to `nix/lib/addons.nix` and run `nix run .#gen-readme`.

The catalogue gives `repository` and a pinned `git_hash` for all 173, but no content hash,
so `add` prefetches one and writes `nix/addons.json`.

**On filtering.** The catalogue's compatibility fields cannot do it: 3 of 173 declare a
`freecad_max` and none declare a `freecad_min` below 0.20. Staleness is reported and never
acted on, because an addon that needs no commits is not thereby broken. What an addon must
pass is the shape check: if its `package.xml` claims a `workbench`, then one of the three
places FreeCAD looks has to have it — `InitGui.py` at the root, `<subdirectory>/InitGui.py`
where the manifest says, or `freecad/*/init_gui.py` for a namespace package. Otherwise
FreeCAD starts with the addon installed and nothing on screen.

What does disqualify one is upstream targeting something else. Assembly4 is maintained,
but its `InitGui.py` accepts FreeCAD 0.19–0.21 and 2.x and prints an error on everything
between, and the "2.x" it points at is a fork rather than upstream — whose current release
is 1.1. FreeCAD 1.x ships an Assembly workbench anyway, so it is not packaged.

**On licences.** 45 of 173 cannot be resolved automatically, and 27 declare none at all.
The rest name a version without saying `-only` or `-or-later`, and that difference is
whether a user may move the work to a later licence — so it is never inferred from a
string. Those stay null in the lock and must be declared where the addon is packaged, with
the evidence.

## Package-specific notes

Two licences are declared by hand, because their manifests cannot be trusted:

- **`kicad-stepup`** says `AGPLv3.0`, which names a version but not whether it is `-only`
  or `-or-later`. There is no LICENSE file at all; no source header grants a later
  version, so the narrow reading is the honest one.
- **`freecad-pcb`** says `AGPLv3.0` in a `<license file="LICENSE">` pointing at a file
  **that does not exist**, while its README and every source header grant "LGPL … either
  version 2 … or (at your option) any later version". The grants the code carries win.

`stepz` is in the flake but **not** in the table, because it is not an addon — it is a
plain importable module. nixpkgs builds `kicad-packages3d` with `compressStep ? true`,
zipping every `.step` into a `.stpZ`; kicadStepUp then calls `stepZ.insert()`, FreeCAD has
no importer for the extension, and a board imports with its outline and not one component.
Upstream's addon of that name opens gzip where nixpkgs writes PKZIP, and does not import
on Python 3 anyway. The better fix is upstream — `kicadStepUptools.py:469` already does
`import zipfile as zf` — and if it lands, this package goes.

`freecad-mcp` is the other odd one: a Python *application* (an MCP server run outside
FreeCAD) that also carries a workbench answering it over XML-RPC. That half only imports
inside FreeCAD, so it ships as data and `passthru.modulePath` points at it.
