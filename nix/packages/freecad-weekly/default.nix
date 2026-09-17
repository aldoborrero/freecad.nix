# Kept independent of the visual patches so their drift cannot block a weekly.
{ pkgs, flake, ... }:
flake.lib.mkFreeCAD { inherit pkgs; } {
  pname = "freecad-weekly";
  version = "2026.08.20";
  hash = "sha256-lXcHg86qkDAZcC5xv013gEvY+mfAtz+v9NadWU3/7SA=";
}
