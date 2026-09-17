# Unlike Timeline, the store root *is* the module directory: a native namespace package,
# found through `freecad/slicercad/init_gui.py`, so there is no `Mod/<name>` step and
# `modulePath` stays null.
{ inputs, system, ... }:
inputs.slicercad.packages.${system}.slicercad
