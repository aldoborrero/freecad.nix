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

  # The title bar: upstream's own pull request, FreeCAD#26766 by PaddleStroke — the same
  # work AstoCAD carries. Against this tag it applies **exactly**: 0 failed hunks, 0 fuzz,
  # largest offset 0 lines.
  #
  # This repo used to carry a 130-line backport of it written against 1.1.1, because the
  # PR fails on the release with 7 hunks across three files. That backport is gone. It was
  # a subset — no preferences page, so the feature could only be turned on from Nix; no
  # `CommandWindow.cpp`; no `WorkbenchSelector` integration; and none of the change to
  # `ToolBarManager.h`, which may be the toolbar docking the review is still waiting on.
  # Keeping a worse copy of an open PR, plus 5497 lines of vendored kit, to serve a
  # release that upstream will supersede was not worth the maintenance.
  #
  # The consequence, stated plainly: **the release build has no custom title bar.** It
  # arrives when #26766 lands and a FreeCAD carrying it is packaged.
  #
  # Pinned to a `compare/<base>...<head>` URL rather than `pull/26766.diff`, which
  # follows the branch: PaddleStroke pushes to it, and a patch that silently becomes a
  # different patch is worse than one that stops applying. When the PR moves, update both
  # SHAs deliberately. `nix flake check`'s patches-apply is what reports the day this
  # stops fitting the tag.
  titleBar = pkgs.fetchurl {
    name = "freecad-pr-26766-custom-title-bar.diff";
    url =
      "https://github.com/FreeCAD/FreeCAD/compare/"
      + "b2da06bfe0521773f302c8be977b31dc27f60203..."
      + "9ee0200042cbb496315de0fd4a56d12897178645.diff";
    hash = "sha256-k7hQDgKVZ207F3IakhwNqqL9vr/zKxwjHO0nrQdA6YM=";
  };
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
  # Then upstream's title-bar PR and this repo's own three. All four apply against the
  # pinned tag with no failed hunk and no fuzz — measured with `patch -p1` on the fetched
  # tree, and re-measured by `nix flake check`; see nix/checks/patches-apply.nix.
  #
  # The fuzz that the release build carries is absent here precisely because the title bar
  # is upstream's own diff rather than a backport of it: it anchors on a tree it was
  # written against.
  patches =
    builtins.filter (p: builtins.match ".*NIXOS-don-t-ignore-PYTHONPATH.*" (toString p) != null) (
      old.patches or [ ]
    )
    ++ [
      titleBar
      # Its own copy for this tree: the release variant costs a second fuzzed hunk here.
      ../../patches/freecad-start-tab/hide-start-tab-weekly.patch
      ../../patches/freecad-tabs-north/tabs-north.patch
      ../../patches/astocad-home-icon/home-icon.patch
    ];

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
    # So nix/checks/patches-apply.nix measures the diff this package actually applies,
    # rather than a second declaration of it that could drift.
    titleBarPatch = titleBar;
  };

  meta = old.meta // {
    description = "${old.meta.description}, built from an upstream weekly snapshot";
  };
})
