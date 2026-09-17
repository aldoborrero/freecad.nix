# This repairs a consequence of packaging, not a missing feature. nixpkgs builds
# `kicad-packages3d` with `compressStep ? true` (pkgs/by-name/ki/kicad/package.nix:26),
# zipping every `.step` into a `.stpZ` — 7241 of them, against 0 upstream. So every
# nixpkgs user is in this position and nobody outside Nix is. kicadStepUp then calls
# `stepZ.insert()` (kicadStepUptools.py:4937 and :16218), FreeCAD has no importer for the
# extension, and a board imports with its outline and not one component.
#
# Upstream's addon of that name — easyw/stepZ, last touched 2018 — cannot fill the gap
# twice over: it opens the container with *gzip* where nixpkgs writes a PKZIP archive, and
# the `gzip_utf8` helper it imports at module scope begins `import __builtin__`, so on the
# CPython 3.14 FreeCAD embeds it does not import at all.
#
# The better fix is upstream and is not blocked on anything: `kicadStepUptools.py` already
# does `import zipfile as zf` at line 469. If that lands, this package can go.
#
# What ships is the `module/` subtree alone: its top level is what `--module-path` puts on
# `sys.path`, so `import stepZ` resolves and the tests and pyproject never land there.
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
