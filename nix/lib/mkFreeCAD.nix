# Both variants keep the same build fixes and test the binary they actually ship.
{ pkgs }:
{
  pname,
  version,
  hash,
  extraPatches ? [ ],
  passthru ? { },
}:
let
  freecad = pkgs.freecad-wayland.overrideAttrs (old: {
    inherit pname version;

    src = pkgs.fetchFromGitHub {
      owner = "FreeCAD";
      repo = "FreeCAD";
      rev = "weekly-${version}";
      fetchSubmodules = true;
      inherit hash;
    };

    # The other nixpkgs patch is already upstream. Assert the retained patch still
    # exists so a nixpkgs rename cannot silently remove PYTHONPATH support.
    patches =
      let
        pythonPath = builtins.filter (
          p: builtins.match ".*NIXOS-don-t-ignore-PYTHONPATH.*" (toString p) != null
        ) (old.patches or [ ]);
      in
      assert builtins.length pythonPath == 1;
      pythonPath ++ extraPatches;

    # The tag date identifies the snapshot, while --version reports version.json.
    # Derive the expected application version from that same source on every update.
    preVersionCheck = (old.preVersionCheck or "") + ''
          snapshotVersion="$version"
          version="$(${pkgs.python3}/bin/python3 -c '
      import json, sys
      with open(sys.argv[1]) as source:
          data = json.load(source)
      print(".".join(str(data["version_" + part]) for part in ("major", "minor", "patch")))
      ' "$src/version.json")"
    '';
    postVersionCheck = ''
      version="$snapshotVersion"
    ''
    + (old.postVersionCheck or "");

    # Two things main's build wants that the release derivation does not provide: gtest,
    # and defusedxml, which the Addon Manager now checks for at configure time.
    nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ pkgs.gtest ];
    buildInputs = (old.buildInputs or [ ]) ++ [ pkgs.python3Packages.defusedxml ];

    # Rebind the inherited tests to the weekly; retaining them unchanged tests the
    # stable nixpkgs package. Filter callPackage's helper attributes before exposing them.
    passthru =
      (old.passthru or { })
      // passthru
      // {
        tests = pkgs.lib.mapAttrs (_: test: test.override { inherit freecad; }) (
          pkgs.lib.filterAttrs (_: pkgs.lib.isDerivation) (old.passthru.tests or { })
        );
      };

    meta = old.meta // {
      description = "${old.meta.description}, built from an upstream weekly snapshot";
    };
  });
in
freecad
