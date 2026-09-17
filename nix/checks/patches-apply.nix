# The cheap guard, and the one that matches the actual risk.
#
# Building FreeCAD to find out a patch drifted costs half an hour; applying the patches
# to the fetched tree costs seconds and answers the same question. So this runs on every
# `nix flake check`, and the full build does not have to.
#
# It fetches sources but compiles nothing: `.src` of each FreeCAD is a fixed-output
# derivation, already in the cache once anyone has built either package.
{ pkgs, perSystem, ... }:
let
  # One tree today, because `freecad-unstable` is the only FreeCAD this flake builds. The
  # shape is per-tree anyway: patches drift against each source independently, and one
  # averaged answer over several would say nothing useful about any of them.
  trees = {
    unstable = {
      src = perSystem.self.freecad-unstable.src;
      # Keep both the list and its order identical to the actual build.
      patches = perSystem.self.freecad-unstable.patches;
    };
  };

  args =
    name:
    let
      t = trees.${name};
    in
    ''
      echo "== ${name}"
      ${pkgs.python3}/bin/python3 ${../../tools/check_patches.py} \
        --source ${t.src} \
        --expected ${../patches/expected.json} \
        ${pkgs.lib.concatMapStringsSep " " (p: "--patch ${p}") t.patches}
    '';
in
pkgs.runCommand "patches-apply"
  {
    nativeBuildInputs = [
      pkgs.python3
      pkgs.patch
    ];
  }
  ''
    ${pkgs.lib.concatMapStringsSep "\n" args (builtins.attrNames trees)}
    touch $out
  ''
