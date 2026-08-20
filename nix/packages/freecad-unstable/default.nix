# FreeCAD's development line, beside the release rather than instead of it.
#
# The two answer different questions. `freecad` is the release, and what this repo's
# preferences, addons and patches are written against; `freecad-unstable` is where you
# go to see whether something you want is already upstream.
#
# Pinned to a *weekly tag*, not to `main`: upstream cuts those as snapshots it considers
# buildable, so moving forward is a deliberate edit rather than catching the tree
# mid-refactor. They land on Wednesdays — 2026.08.05, .12, .20 — so a date that is not
# a Wednesday is not a tag. Ask the remote rather than guessing; a hand-written pin that
# never existed is exactly the mistake `nix-update` exists to prevent.
#
# `version` is the bare date and `rev` derives the tag from it, which is the shape
# `nix-update` rewrites: it replaces `version` and `hash` and nothing else. See
# ./nix-update-args for the regex that turns `weekly-2026.08.20` into `2026.08.20`.
#
# `fetchFromGitHub` with `fetchSubmodules`, not a flake input: a `git+https` input clones
# the repository — 596k objects and 5 GB of cache, measured — to build one tag. The
# submodules are not optional, because main moved Coin, Pivy and OndselSolver out of the
# tree into them, and without them CMake stops at "the OndselSolver git submodule is not
# available".
{ pkgs, ... }:
let
  version = "2026.08.20";
in
pkgs.freecad-wayland.overrideAttrs (old: {
  pname = "freecad-unstable";
  inherit version;

  src = pkgs.fetchFromGitHub {
    owner = "FreeCAD";
    repo = "FreeCAD";
    rev = "weekly-${version}";
    fetchSubmodules = true;
    hash = "sha256-lXcHg86qkDAZcC5xv013gEvY+mfAtz+v9NadWU3/7SA=";
  };

  # nixpkgs carries two patches: its own PYTHONPATH fix, and a cherry-picked upstream
  # commit already in this tree. Only the first is kept, matched by name so a nixpkgs
  # rename fails loudly here instead of silently dropping one that still matters.
  #
  # This repo's four follow. All apply against the pinned tag — measured with `patch -p1`
  # on the fetched tree: offsets of up to 415 lines and no failed hunk. One hunk is
  # placed with *fuzz 2*, custom-titlebar's first on `src/Gui/MainWindow.h`, because
  # upstream added <QByteArray> and <QString> around the include block it anchors on.
  # `nix flake check` re-measures this; see nix/checks/patches-apply.nix.
  patches =
    builtins.filter (p: builtins.match ".*NIXOS-don-t-ignore-PYTHONPATH.*" (toString p) != null) (
      old.patches or [ ]
    )
    ++ [
      ../../patches/astocad-titlebar/custom-titlebar.patch
      # Its own copy for this tree: the release variant costs a second fuzzed hunk here.
      ../../patches/freecad-start-tab/hide-start-tab-weekly.patch
      ../../patches/freecad-tabs-north/tabs-north.patch
      ../../patches/astocad-home-icon/home-icon.patch
    ];

  postPatch = (old.postPatch or "") + ''
    cp -r ${../../patches/astocad-titlebar/customtitlebarkit} src/3rdParty/customtitlebarkit
    chmod -R u+w src/3rdParty/customtitlebarkit
  '';

  # Two things main's build wants that the release derivation does not provide: gtest,
  # and defusedxml, which the Addon Manager now checks for at configure time.
  nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ pkgs.gtest ];
  buildInputs = (old.buildInputs or [ ]) ++ [ pkgs.python3Packages.defusedxml ];

  # blueprint exposes every `passthru.tests` entry as a flake check, and nixpkgs' set is
  # not all derivations: `callPackage` adds `override` (a set) and `overrideDerivation`
  # (a lambda) beside the real `modules` and `python-path`. `nix flake check` then stops
  # at "flake attribute 'checks.<system>.pkgs-freecad-unstable-override' is not a
  # derivation" — an error about *our* flake, produced entirely by upstream's plumbing.
  # Keep the two that are tests.
  passthru = (old.passthru or { }) // {
    tests = pkgs.lib.filterAttrs (_: pkgs.lib.isDerivation) (old.passthru.tests or { });
  };

  meta = old.meta // {
    description = "${old.meta.description}, built from an upstream weekly snapshot";
  };
})
