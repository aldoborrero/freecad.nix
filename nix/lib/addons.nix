# Every addon this repo ships, with the category it is documented under.
#
# Listed rather than discovered: a check that enumerates whatever it finds cannot fail
# when something stops being found.
#
# One list, not two. `addon-shapes` verifies these and `readme-current` documents them,
# and a second copy would eventually disagree — the symptom being a README describing an
# addon nothing checks. The category lives here for the same reason: keeping it beside
# the name makes it impossible to add one without saying where it belongs.
perSystem:
builtins.mapAttrs
  (name: category: {
    package = perSystem.self.${name};
    inherit category;
  })
  {
    gridfinity = "3D printing";
    slicercad = "3D printing";

    fasteners = "Assemblies and mechanical parts";
    freecad-gears = "Assemblies and mechanical parts";
    sheetmetal = "Assemblies and mechanical parts";

    kicad-stepup = "KiCad and electronics";
    kiconnect = "KiCad and electronics";
    free2ki = "KiCad and electronics";
    freecad-pcb = "KiCad and electronics";

    curves = "Modelling";
    silk = "Modelling";
    lattice2 = "Modelling";
    dynamicdata = "Modelling";
    meshremodel = "Modelling";

    freecad-ribbon = "Interface";
    piemenu = "Interface";
    color-palette-theme = "Interface";
    freecad-timeline = "Interface";

    # Not an addon package as such — a Python application that happens to carry a workbench
    # in `share/`. It is in this list precisely because `modulePath` makes that
    # indistinguishable from here.
    freecad-mcp = "Automation";
  }
