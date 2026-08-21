# Re-exposed from its own repository. Unlike Timeline, the store root *is* the module
# directory: Slicercad is a native namespace package, found through
# `freecad/slicercad/init_gui.py` rather than an `InitGui.py`, so there is no
# `Mod/<name>` step.
{ inputs, system, ... }:
inputs.slicercad.packages.${system}.slicercad
