{ pkgs, flake, ... }:
flake.lib.mkAddon { inherit pkgs; } "Silk" { }
