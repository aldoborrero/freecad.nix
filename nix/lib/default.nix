# What blueprint exposes as `flake.lib`.
#
# It is not optional: blueprint treats `nix/lib` as one of its directories and looks for
# `default.nix` in it, so adding `mkAddon.nix` beside it without this made evaluation fail
# with "Path 'nix/lib/default.nix' does not exist in Git repository" — an error that names
# a file nothing here ever asked for.
#
# Keep this ignoring its argument. The packages reach `mkAddon` through `flake.lib`, so
# anything here that touched `perSystem` or the packages would make all sixteen recurse.
_: {
  mkAddon = import ./mkAddon.nix;
  mkFreeCAD = import ./mkFreeCAD.nix;
}
