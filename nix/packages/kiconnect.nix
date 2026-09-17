# Beside `kicad-stepup`, not instead of it. StepUp reads board files off disk and reaches
# KiCad's `.stpZ` models through `stepz`; KiConnect talks to a running KiCad over its IPC
# API. Which one works depends on the KiCad you have.
{ pkgs, flake, ... }:
flake.lib.mkAddon { inherit pkgs; } "KiConnect" { }
