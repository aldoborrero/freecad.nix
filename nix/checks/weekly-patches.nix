{ pkgs, perSystem, ... }:
let
  freecad = perSystem.self.freecad-weekly;
in
pkgs.runCommand "weekly-patches"
  {
    nativeBuildInputs = [
      pkgs.python3
      pkgs.patch
    ];
  }
  ''
    python3 ${../../tools/check_patches.py} \
      --source ${freecad.src} \
      ${pkgs.lib.concatMapStringsSep " " (p: "--patch ${p}") freecad.patches}
    touch $out
  ''
