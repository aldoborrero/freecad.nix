# Re-exposed from its own repository, so this flake can assemble FreeCAD with every
# addon in one place. Nothing is rebuilt here: the derivation is the one that repo's
# own gate — ruff, mypy strict, 270 tests across three tiers — already passed.
#
# Its store root is *not* the module directory. FreeCAD takes a module's name from the
# directory name, so `--module-path` wants the `Mod/Timeline` inside; `passthru.modulePath`
# carries that rather than leaving it to be rediscovered.
{ inputs, system, ... }:
inputs.freecad-timeline.packages.${system}.freecad-timeline
