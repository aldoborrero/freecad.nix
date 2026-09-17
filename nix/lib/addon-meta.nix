# Everything the README's extension list needs, from `meta`, `passthru` and the tree.
{
  lib,
  perSystem,
  inputs,
}:
lib.mapAttrs (
  name: entry:
  let
    inherit (entry) package;
    # `nix/packages/<name>.nix` unless the package has sibling files, in which case it is
    # a directory. Asked rather than assumed, so the link cannot rot when one changes.
    flat = ../packages + "/${name}.nix";
  in
  {
    inherit (entry) category;
    version = package.version or "0";
    description = package.meta.description or "";
    # `spdxId` when nixpkgs knows the licence, `shortName` for the ones `mkAddon`
    # synthesises from an identifier nixpkgs has no attribute for.
    license = package.meta.license.spdxId or package.meta.license.shortName or "unknown";
    homepage = package.meta.homepage or null;
    modulePath = package.passthru.modulePath or null;
    sourceFile =
      if builtins.pathExists flat then "nix/packages/${name}.nix" else "nix/packages/${name}/default.nix";
    # `catalogName` is set by `mkAddon` and by nothing else, so it is the honest test for
    # "came from FreeCAD's catalogue" — better than a list here that could fall behind.
    origin =
      if (package.passthru.catalogName or null) != null then
        "catalogue"
      else if inputs ? ${name} then
        "own repo"
      else
        "upstream";
  }
) (import ./addons.nix perSystem)
