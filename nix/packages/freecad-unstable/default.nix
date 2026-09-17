# Pinned to a *weekly tag*, not to `main`: upstream cuts those as snapshots it considers
# buildable, so moving forward is a deliberate edit rather than catching the tree
# mid-refactor. Ask the remote for tags rather than guessing their release dates.
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
{ pkgs, flake, ... }:
let
  version = "2026.08.20";

  # The title bar: upstream's own pull request, FreeCAD#26766 by PaddleStroke. Against
  # this tag it applies exactly — 0 failed hunks, 0 fuzz, largest offset 0 lines — and it
  # does not apply to the release, which is why only this build has it.
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
flake.lib.mkFreeCAD { inherit pkgs; } {
  pname = "freecad-unstable";
  inherit version;
  hash = "sha256-lXcHg86qkDAZcC5xv013gEvY+mfAtz+v9NadWU3/7SA=";
  extraPatches = [
    titleBar
    ../../patches/freecad-tabs-north/tabs-north.patch
  ];
  passthru.titleBarPatch = titleBar;
}
