# `pname` is set because the catalogue calls it `freecad.gears`, and the default —
# `lib.toLower name` — would put a dot in a derivation name.
#
# Its `package.xml` also declares `depend`, which is ignored: the dependency is numpy,
# already in FreeCAD's Python. An addon declaring one FreeCAD does not satisfy would need
# more than a copy.
{ pkgs, flake, ... }:
flake.lib.mkAddon { inherit pkgs; } "freecad.gears" {
  pname = "freecad-gears";
}
