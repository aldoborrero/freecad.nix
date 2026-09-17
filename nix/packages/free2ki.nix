# The direction `kicad-stepup` and `stepz` do not cover: FreeCAD solids out to a KiCad
# 3D model, rather than KiCad in.
{ pkgs, flake, ... }:
flake.lib.mkAddon { inherit pkgs; } "free2ki" { }
