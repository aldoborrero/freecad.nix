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
  # Only the ones every tree shares. The title bar differs per tree and is named below:
  # the release build carries this repo's backport, the weekly one carries upstream's own
  # pull request, which does not apply to the release at all (7 failed hunks).
  patches = [
    ../patches/freecad-tabs-north/tabs-north.patch
    ../patches/astocad-home-icon/home-icon.patch
  ];

  # The two trees drift independently, and hide-start-tab has a copy per tree, so each
  # gets its own run rather than one averaged answer.
  trees = {
    unstable = {
      src = perSystem.self.freecad-unstable.src;
      startTab = ../patches/freecad-start-tab/hide-start-tab-weekly.patch;
      # The same fetched diff the package applies, so this checks what is actually built
      # rather than a second copy of it.
      titleBar = perSystem.self.freecad-unstable.titleBarPatch;
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
        ${pkgs.lib.concatMapStringsSep " " (p: "--patch ${p}") (
          patches
          ++ [
            t.startTab
            t.titleBar
          ]
        )}
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
