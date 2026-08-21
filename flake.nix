{
  description = "FreeCAD, its extensions, and the patches that make it look like a 2026 CAD program";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    blueprint = {
      url = "github:numtide/blueprint";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # This repo's own addons, each in its own repository because each is a project
    # rather than a packaging detail — they carry their own tests, their own gate and
    # their own README, and both are installable by FreeCAD's Addon Manager with no Nix
    # involved. They come in as *flakes*, so what arrives is a package with a version
    # and a `meta`, not a source tree needing both written down here.
    freecad-timeline = {
      url = "github:aldoborrero/freecad-timeline";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    slicercad = {
      url = "github:aldoborrero/slicercad";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  # Deliberately no `flake = false` addon inputs. An addon pinned as a bare source tree
  # has no `meta`, so its licence has to be written down by hand and kept honest by
  # hand — and nothing can bump it, because it has no version to compare. Every addon
  # here is a package under nix/packages with `src`, `version` and `meta`, which makes
  # the licence table derivable and `nix-update` able to move it.

  outputs =
    inputs:
    inputs.blueprint {
      inherit inputs;
      prefix = "nix";
      systems = [
        "aarch64-linux"
        "x86_64-linux"
      ];
    };
}
