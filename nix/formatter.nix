{
  pkgs,
  inputs,
  flake,
  ...
}:
let
  module = inputs.treefmt-nix.lib.evalModule pkgs {
    projectRootFile = "flake.nix";

    programs = {
      deadnix.enable = true;
      statix.enable = true;
      nixfmt.enable = true;
      # No `lineLength` here, and no `ruff.toml` either — 88 everywhere, which is ruff's
      # default and already what `nix/packages/stepz/pyproject.toml` asks for.
      #
      # Setting it here does not work: treefmt passes `--line-length` on the command line,
      # a flag beats a config file, and it would reach *every* Python file. stepz would be
      # formatted to 95 by `nix fmt` and then failed at 88 by its own gate, each undoing the
      # other. A per-directory `ruff.toml` would avoid that, but only by buying a whole file
      # to keep two trees disagreeing.
      ruff-format.enable = true;
      taplo.enable = true;

      yamlfmt = {
        enable = true;
        settings.formatter = {
          type = "basic";
          indent = 2;
        };
      };

      # `nix/addons.json` is also written by `tools/catalog.py`, so the two have to agree or
      # every update and every format would undo the other. They do — jsonfmt matches its
      # 2-space indent and leaves its `\uXXXX` escapes alone. See `write_lock` there.
      jsonfmt.enable = true;

      # Report-only, so a finding fails `nix fmt` instead of being applied behind your back.
      # `ruff-check` is one of these only because its `--fix` is forced off below.
      ruff-check.enable = true;
      actionlint.enable = true;
      shellcheck.enable = true;
      shfmt.enable = true;

      # No Markdown formatter: README.md carries a generated block that `readme-current`
      # compares byte for byte, and a reflow would fight it.
    };

    # Three formatters claim `*.nix`, so this is the only place order matters, and treefmt
    # writes no priority unless asked. deadnix deletes bindings, statix rewrites what is left
    # into idiom, nixfmt lays out the result — so nixfmt goes last or its output is re-edited.
    settings.formatter = {
      deadnix.priority = 1;
      statix.priority = 2;
      nixfmt.priority = 3;

      # treefmt-nix hardcodes `check --fix`, and a lint autofix is not formatting: on its
      # first run here it deleted four `# noqa` directives and the prose explaining one of
      # them. Forced back to a bare `check`, it reports and never edits — which is the only
      # shape a linter belongs in `nix fmt` at all. Add rules with
      # `programs.ruff-check.extendSelect`; they land in `options` before this and would be
      # dropped, so put them here instead if you need both.
      ruff-check.options = pkgs.lib.mkForce [ "check" ];
    };

    settings.global.excludes = [
      # Agent skills, installed per-checkout and not ours to format.
      ".agents/**"
      ".claude/**"
      "skills-lock.json"
      # Patches are bytes that have to apply, not text to tidy.
      "*.patch"
      "*.diff"
    ];
  };
  wrapper = module.config.build.wrapper;
in
wrapper
// {
  passthru = (wrapper.passthru or { }) // {
    tests.check = module.config.build.check flake;
  };
}
