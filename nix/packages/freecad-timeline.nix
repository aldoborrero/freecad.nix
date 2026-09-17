# Its store root is *not* the module directory. FreeCAD takes a module's name from the
# directory name, so `--module-path` wants the `Mod/Timeline` inside; `passthru.modulePath`
# carries that rather than leaving it to be rediscovered.
{ inputs, system, ... }:
inputs.freecad-timeline.packages.${system}.freecad-timeline
