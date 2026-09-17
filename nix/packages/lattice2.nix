{ pkgs, flake, ... }:
flake.lib.mkAddon { inherit pkgs; } "lattice2" { }
