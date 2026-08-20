# kicadStepUp: imports a .kicad_pcb into FreeCAD with its component models.
#
# Needed beside `stepz`, not instead of it: every 3D model in nixpkgs' KiCad library is
# a `.stpZ`, and StepUp reaches those through `stepZ.insert()`, a module FreeCAD does
# not ship.
{ pkgs, ... }:
import ../../lib/mkAddon.nix { inherit pkgs; } "kicadStepUpMod" {
  pname = "kicad-stepup";

  # Declared by hand because the catalogue's string is `AGPLv3.0`, which names a version
  # but not whether it is `-only` or `-or-later`. Read off the source rather than the
  # manifest, and the source is not tidy: there is **no LICENSE file** at all, the README
  # links to <https://www.gnu.org/licenses/agpl-3.0.en.html>, and the header of
  # `kicadStepUptools.py` invokes the Affero licence "as published by the Free Software
  # Foundation" with no "or any later version" clause — while its closing boilerplate
  # still refers to the *Library* GPL, evidently left over from a template.
  #
  # No later-version grant anywhere, so the narrow reading is the honest one. If upstream
  # ever adds a LICENSE, check this again.
  license = "AGPL-3.0-only";
}
