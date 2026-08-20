# Gridfinity, from the catalogue. Everything but the name comes out of nix/addons.json.
{ pkgs, ... }:
import ../../lib/mkAddon.nix { inherit pkgs; } "Gridfinity" { }
