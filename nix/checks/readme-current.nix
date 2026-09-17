# README.md's extensions table describes what the flake contains — verified, not trusted.
#
# The table is generated, and this is the half that fails when the committed one has
# fallen behind. It exists as a flake check rather than only as a CI job so the answer
# arrives before the push, on the same `nix flake check` as everything else.
#
# Everything it renders comes from `meta` and `passthru`, via `nix/lib/addon-meta.nix`,
# so a row can only say what the package says. Regenerate with `nix run .#gen-readme`.
{
  pkgs,
  perSystem,
  inputs,
  ...
}:
let
  meta = import ../lib/addon-meta.nix {
    inherit (pkgs) lib;
    inherit perSystem inputs;
  };
in
pkgs.runCommand "readme-current" { nativeBuildInputs = [ pkgs.python3 ]; } ''
  python3 ${../../tools/gen_readme.py} \
    --meta ${pkgs.writeText "addon-meta.json" (builtins.toJSON meta)} \
    --readme ${../../README.md} \
    --check
  touch $out
''
