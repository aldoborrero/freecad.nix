# Two things in one repository, and they are not the same kind of thing.
#
#   * A **Python application** — the MCP server, which a client outside FreeCAD runs.
#   * A **FreeCAD addon** — `addon/FreeCADMCP`, which imports `FreeCAD` and `FreeCADGui`
#     and answers the server over XML-RPC.
#
# The second cannot be a Python module of this package: it is only importable inside
# FreeCAD. So it ships as data under `share/`, and `passthru.modulePath` points at it the
# same way Timeline's does — which is what lets `nix/checks/addon-shapes.nix` verify it
# without knowing anything special about this package.
#
# `fetchFromGitHub` rather than a `flake = false` input, for the reason in flake.nix: a
# source tree pinned as an input carries no version and no meta, so both would have to be
# written here and kept honest by hand. Upstream tags its releases (`v0.1.21` is the
# pinned rev), so `nix-update` can move this on its own.
{ pkgs, ... }:
let
  inherit (pkgs) lib python3Packages;
  version = "0.1.21";
in
python3Packages.buildPythonApplication {
  pname = "freecad-mcp";
  inherit version;
  pyproject = true;

  src = pkgs.fetchFromGitHub {
    owner = "neka-nat";
    repo = "freecad-mcp";
    rev = "v${version}";
    hash = "sha256-c6eyJPQzRV/ajIFhEmdXb+Y5LQiZj714yuJd5UDfnhw=";
  };

  build-system = [ python3Packages.hatchling ];

  # pyproject asks for mcp[cli]; the extra is only typer and the `mcp` command, neither
  # of which `src/freecad_mcp` imports.
  dependencies = with python3Packages; [
    mcp
    validators
  ];

  # The version above is what `nix-update` rewrites and what `rev` is built from, so it
  # cannot be a comment asking someone to keep it in step with upstream's pyproject —
  # a claim nothing checks is a claim that drifts. Assert it instead.
  postPatch = ''
    declared=$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -1)
    if [ "$declared" != "${version}" ]; then
      echo "this package says ${version}, upstream's pyproject.toml says $declared" >&2
      exit 1
    fi
  '';

  pythonImportsCheck = [ "freecad_mcp" ];

  postInstall = ''
    mkdir -p $out/share/freecad-mcp
    cp -r addon/FreeCADMCP $out/share/freecad-mcp/FreeCADMCP
  '';

  passthru.modulePath = "share/freecad-mcp/FreeCADMCP";

  meta = {
    description = "MCP server for FreeCAD: drives a running FreeCAD over XML-RPC";
    homepage = "https://github.com/neka-nat/freecad-mcp";
    license = lib.licenses.mit;
    mainProgram = "freecad-mcp";
    platforms = lib.platforms.unix;
  };
}
