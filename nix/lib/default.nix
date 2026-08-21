# What blueprint exposes as `flake.lib`.
#
# It is not optional: blueprint treats `nix/lib` as one of its directories and looks for
# `default.nix` in it, so adding `mkAddon.nix` beside it without this made evaluation fail
# with "Path 'nix/lib/default.nix' does not exist in Git repository" — an error that names
# a file nothing here ever asked for.
#
# `mkAddon` is re-exported rather than defined here because a package needs it at
# evaluation time, and `flake.lib` is not in a package's scope. The packages therefore
# `import ../../lib/mkAddon.nix` directly; this is for anything consuming the flake from
# outside.
_: {
  mkAddon = import ./mkAddon.nix;
}
