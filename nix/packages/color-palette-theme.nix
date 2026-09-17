{ pkgs, flake, ... }:
flake.lib.mkAddon { inherit pkgs; } "Color-Palette-Theme" { }
