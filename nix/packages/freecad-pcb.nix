{ pkgs, flake, ... }:
flake.lib.mkAddon { inherit pkgs; } "pcb" {
  pname = "freecad-pcb";

  # Declared by hand, and *against* the manifest rather than merely beyond it — the one
  # case here where the two sources disagree outright.
  #
  # `package.xml` says `<license file="LICENSE">AGPLv3.0</license>`, which is unusable
  # twice over: `AGPLv3.0` names a version without saying -only or -or-later, and there
  # is no LICENSE file in the repository, so the attribute points at nothing.
  #
  # The README's licence section and the header of every source file say instead: "GNU
  # Lesser General Public License (LGPL) ... either version 2 of the License, or (at your
  # option) any later version" — a complete grant, which the manifest is not. If upstream
  # ever adds the LICENSE it promises, check this again.
  license = "LGPL-2.0-or-later";
}
