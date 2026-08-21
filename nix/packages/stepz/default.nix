# A `.stpZ` importer for FreeCAD, which ships none.
#
# **This exists to repair a consequence of packaging, not to add a feature**, and it is
# worth knowing which packaging. nixpkgs builds `kicad-packages3d` with
# `compressStep ? true` (pkgs/by-name/ki/kicad/package.nix:26), which runs
# `zip -j -9 {.}.stpZ {} && rm {}` over every `.step` and then seds the footprint library
# to match. The result, measured on the library this flake resolves:
#
#     kicad-packages3d   7241 .stpZ, 0 .step
#     KiCad upstream        0 .stpZ  (1.2 GB of .step)
#
# So every nixpkgs user is in this position and nobody outside Nix is. kicadStepUp calls
# `stepZ.insert()` for a model whose path ends in `.stpZ` (kicadStepUptools.py:4937 and
# :16218), FreeCAD has no importer for the extension, and a board therefore imports with
# its outline and not one component.
#
# Upstream's addon of that name — easyw/stepZ, last touched 2018 — cannot fill the gap
# twice over: it opens the container with *gzip* where nixpkgs writes a PKZIP archive, and
# the `gzip_utf8` helper it imports at module scope begins `import __builtin__`, so on the
# CPython 3.14 FreeCAD embeds it does not import at all.
#
# The better fix is upstream and is not blocked on anything: `kicadStepUptools.py` already
# does `import zipfile as zf` at line 469, so reading the archive there needs no new
# dependency. If that lands, this package can go.
#
# What ships is the `module/` subtree alone: its top level is what `--module-path` puts on
# `sys.path`, so `import stepZ` resolves and the tests and pyproject beside it never land
# there.
{ pkgs, ... }:
pkgs.runCommand "stepz"
  {
    passthru.reason = "kicadStepUp needs it while nixpkgs compresses KiCad's 3D models";
    meta = {
      description = "Import KiCad's .stpZ (a ZIP holding one STEP) into FreeCAD";
      homepage = "https://github.com/aldoborrero/freecad.nix";
      license = pkgs.lib.licenses.lgpl21Plus;
      platforms = pkgs.lib.platforms.all;
    };
  }
  ''
    mkdir -p $out
    cp ${./module}/* $out/

    # It is a module, not an addon: no package.xml, no InitGui.py, nothing FreeCAD's
    # addon machinery looks at. What has to be true is that `import stepZ` works from a
    # module path, which means exactly this file at exactly this name.
    test -f $out/stepZ.py
    test -f $out/Init.py
  ''
