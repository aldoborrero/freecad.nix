# CurvesWB: NURBS surfacing, blend curves, and the sketch-on-surface tools.
{ pkgs, ... }:
import ../../lib/mkAddon.nix { inherit pkgs; } "Curves" { }
