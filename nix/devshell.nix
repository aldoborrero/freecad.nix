# Everything `tools/` needs, so the scripts run without a `nix shell` in front of them.
#
# The tools are deliberately plain Python with no third-party dependencies — the standard
# library plus whatever is on PATH — so this is a list of executables rather than a Python
# environment. `nix-prefetch-git` is the one thing `catalog.py add` cannot do itself: the
# catalogue publishes a revision but no content hash.
{
  pkgs,
  perSystem,
  ...
}:
pkgs.mkShellNoCC {
  name = "freecad-nix";

  packages = [
    pkgs.python3
    pkgs.ruff
    pkgs.nix-prefetch-git
    pkgs.nix-update
    pkgs.jq

    # The same formatter `nix fmt` runs, so `treefmt` in the shell cannot disagree with
    # the one CI uses.
    perSystem.self.formatter
  ];

  shellHook = ''
    echo "freecad.nix — tools/*.py are on PATH-adjacent paths, run them directly:"
    echo "  tools/catalog.py list --content workbench   what the catalogue offers"
    echo "  tools/discovery.py                          what can move, and how"
    echo "  nix run .#gen-readme                        rewrite the extensions table"
    echo "  nix fmt                                     treefmt"
  '';
}
