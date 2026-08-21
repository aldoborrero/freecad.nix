# Every addon, checked at the path FreeCAD would actually be pointed at.
#
# This is not the same claim `mkAddon` makes in its own `installCheckPhase`. That one
# checks `$out` for an addon built here. This one checks `$out` *plus its modulePath*, for
# every addon regardless of where it came from — including the two that arrive as flake
# inputs and are never built by this repo at all.
#
# The distinction is the whole point, because the two disagree:
#
#   freecad-timeline   modulePath = Mod/Timeline   the store root is a container
#   slicercad          modulePath = null           the store root *is* the module
#
# FreeCAD takes a module's name from its directory name (`DirMod.name` is `path.name` in
# FreeCADInit.py), so handing it the wrong one of those does not fail — it loads an addon
# called `xxxxxxxx-freecad-timeline-1.0.0`, or loads nothing at all and says nothing.
{
  pkgs,
  perSystem,
  ...
}:
let
  inherit (pkgs) lib;

  # Listed rather than discovered: a check that enumerates whatever it finds cannot fail
  # when something stops being found.
  addons = {
    inherit (perSystem.self)
      gridfinity
      curves
      kicad-stepup
      freecad-timeline
      slicercad
      ;
  };

  modulePath =
    addon:
    let
      sub = addon.passthru.modulePath or null;
    in
    "${addon}" + lib.optionalString (sub != null) "/${sub}";
in
pkgs.runCommand "addon-shapes" { nativeBuildInputs = [ pkgs.python3 ]; } ''
  ${lib.concatStringsSep "\n" (
    lib.mapAttrsToList (name: addon: ''
      echo "== ${name}"
      test -d ${lib.escapeShellArg (modulePath addon)} \
        || { echo "  ERROR: modulePath does not exist" >&2; exit 1; }
      python3 ${../../tools/check_addon_shape.py} --root ${lib.escapeShellArg (modulePath addon)}
    '') addons
  )}
  touch $out
''
