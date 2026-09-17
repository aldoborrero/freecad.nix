# Rewrites README.md's extensions table. The writing half of `readme-current`.
#
# The metadata is baked in at build time, and is the same `nix/lib/addon-meta.nix` the
# check compares against, so the two cannot render different tables. Run it from the
# repository root:
#
#     nix run .#gen-readme
#
# No `version`, so `tools/discovery.py` exempts it: there is nothing upstream to bump.
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
pkgs.writeShellApplication {
  name = "gen-readme";
  runtimeInputs = [ pkgs.python3 ];
  text = ''
    if [ ! -f README.md ]; then
      echo "no README.md here — run this from the repository root" >&2
      exit 1
    fi
    exec python3 ${../../tools/gen_readme.py} \
      --meta ${pkgs.writeText "addon-meta.json" (builtins.toJSON meta)} \
      --readme README.md \
      --write
  '';
}
