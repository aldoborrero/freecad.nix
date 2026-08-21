# The stepZ module's Python: ruff for the rules in its pyproject.toml, mypy strict, and
# the tests — which stand in for `ImportGui` and so run with no FreeCAD at all.
#
# That they can is a property of the module rather than of the test: `stepZ.py` imports
# `ImportGui` *inside* its functions instead of at module scope, because it only exists in
# a running FreeCAD GUI. Keeping it out of the import path is what lets the packing and
# unpacking be exercised here.
{ pkgs, ... }:
pkgs.runCommand "stepz-python"
  {
    nativeBuildInputs = [
      pkgs.ruff
      pkgs.mypy
      (pkgs.python3.withPackages (ps: [ ps.pytest ]))
    ];
  }
  ''
    cp -r ${../packages/stepz} source
    chmod -R u+w source
    cd source
    rm -f default.nix

    ruff check .
    ruff format --check .
    # Init.py is a startup script FreeCAD runs, not a module: ruff checks it, mypy does
    # not, since that would mean modelling the environment FreeCAD injects into it.
    HOME=$TMPDIR mypy module/stepZ.py tests
    python -m pytest -q tests

    touch $out
  ''
