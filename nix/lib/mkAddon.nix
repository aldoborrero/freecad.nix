# One FreeCAD addon, built from what `tools/catalog.py` locked.
#
# Imported directly rather than through `flake.lib` — `import ../../lib/mkAddon.nix
# { inherit pkgs; }` — because a package needs it at evaluation time and blueprint's
# `flake.lib` is not in a package's scope.
#
# What lands in the store is the module directory itself: the thing `--module-path`
# points at, which is also exactly what the Addon Manager would clone into
# `~/.local/share/FreeCAD/Mod/`. One layout serves both installs.
{ pkgs }:
let
  lock = builtins.fromJSON (builtins.readFile ../addons.json);
  inherit (pkgs) lib;
in
name: overrides:
let
  entry =
    lock.${name} or (throw ''
      no addon called '${name}' in nix/addons.json.
      Add it with: tools/catalog.py add ${name}
    '');

  # Never inferred. `tools/catalog.py` resolves what it safely can and leaves the rest
  # null: 32 of the catalogue's 173 addons cannot be resolved, 27 because they declare no
  # licence at all and the rest because they write things like `LGPL-3`, which does not
  # say -only or -or-later. Guessing changes what the licence permits, so this stops.
  declared = overrides.license or entry.spdx or null;
  spdx =
    if declared != null then
      declared
    else
      throw ''
        ${name} does not declare a licence this can resolve${
          lib.optionalString (
            entry.license or null != null
          ) " (its package.xml says ${builtins.toJSON entry.license})"
        }.
        Read its LICENSE file and pass the SPDX identifier explicitly:
          mkAddon "${name}" { license = "LGPL-2.1-or-later"; }
      '';

  # By exclusion, never by inclusion. An include-list silently drops a module the addon
  # adds later, and the place you find out is the GUI — the same trap this repo already
  # paid for once.
  excluded = [
    ".git"
    ".github"
    ".gitignore"
    ".gitattributes"
  ]
  ++ (overrides.exclude or [ ]);
in
pkgs.stdenvNoCC.mkDerivation {
  pname = overrides.pname or (lib.toLower name);
  version = overrides.version or entry.version or "0";

  src = pkgs.fetchgit {
    url = entry.repository;
    rev = entry.rev;
    hash = entry.hash;
    fetchSubmodules = overrides.fetchSubmodules or false;
  };

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall
    mkdir -p $out
    cp -r . $out/
    ${lib.concatMapStringsSep "\n" (p: "rm -rf \"$out/${p}\"") excluded}
    runHook postInstall
  '';

  # Run here rather than as a separate flake check, so a broken addon cannot be built at
  # all. A check alongside would let the package exist and merely report on it, and the
  # whole point is that this failure is otherwise invisible until the GUI is open.
  doInstallCheck = true;
  nativeInstallCheckInputs = [ pkgs.python3 ];
  installCheckPhase = ''
    runHook preInstallCheck
    python3 ${../../tools/check_addon_shape.py} --root $out \
      ${lib.concatMapStringsSep " " (k: "--content ${k}") (entry.content or [ ])}
    runHook postInstallCheck
  '';

  passthru = {
    # The key in nix/addons.json, which is the catalogue's name for the addon and is not
    # the package name: `Gridfinity` against `gridfinity`, `kicadStepUpMod` against
    # `kicad-stepup`. tools/discovery.py reads this to know that the way to move this
    # package forward is the catalogue, and which entry to look at.
    catalogName = name;

    # What FreeCAD should be pointed at. Almost always $out, but an addon whose module
    # directory sits below the root says so, the way Timeline installs as Mod/Timeline.
    modulePath = overrides.modulePath or null;
    content = entry.content or [ ];
    catalogRev = entry.rev;
  };

  meta = {
    description = overrides.description or entry.description or "FreeCAD addon ${name}";
    homepage = overrides.homepage or entry.homepage;
    # Matched on spdxId rather than by mangling the string into an attribute name:
    # nixpkgs' own names for these do not follow from the identifier (`lgpl21Plus`,
    # not `lgpl_2_1_or_later`). Unknown ones get a minimal licence rather than an
    # eval error, since the identifier itself came from the addon.
    license = lib.findFirst (l: (l.spdxId or null) == spdx) {
      shortName = spdx;
      spdxId = spdx;
      free = true;
    } (lib.attrValues lib.licenses);
    platforms = lib.platforms.all;
  };
}
