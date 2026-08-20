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
  patches = [
    ../patches/astocad-titlebar/custom-titlebar.patch
    ../patches/freecad-tabs-north/tabs-north.patch
    ../patches/astocad-home-icon/home-icon.patch
  ];

  # The two trees drift independently, and hide-start-tab has a copy per tree, so each
  # gets its own run rather than one averaged answer.
  trees = {
    unstable = {
      src = perSystem.self.freecad-unstable.src;
      startTab = ../patches/freecad-start-tab/hide-start-tab-weekly.patch;
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
        ${pkgs.lib.concatMapStringsSep " " (p: "--patch ${p}") (patches ++ [ t.startTab ])}
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
