# Repository Guidelines

## Project Structure

- Root: `flake.nix`, `flake.lock`, `README.md`, `LICENSE`.
- `nix/packages/` — one file per package. A **directory** only when the package has
  sibling files (`freecad-mcp/`, `freecad-weekly/` and `freecad-unstable/` carry
  `nix-update-args`, `stepz/`
  carries `module/`, `tests/` and `pyproject.toml`). Everything else is `<name>.nix`.
- `nix/lib/` — `mkAddon.nix` (exported as `flake.lib.mkAddon`), `addons.nix` (the list two
  checks share), `addon-meta.nix` (what the README table needs at eval time).
- `nix/checks/`, `nix/patches/`, `nix/addons.json` (the catalogue lock).
- `tools/` — all automation, in Python. No other language.

## Commands

```bash
nix flake check                                   # everything (two long C++ compiles)
nix build .#checks.x86_64-linux.patches-apply     # the cheap one worth running always
nix build .#checks.x86_64-linux.addon-shapes      # every addon's entry point
nix fmt                                           # treefmt (nixfmt)
nix run .#gen-readme                              # rewrite the README extensions table
tools/discovery.py                                # what can move, and how
```

`nix develop` (or `direnv allow`) puts `python3`, `ruff`, `nix-prefetch-git`, `nix-update`,
`jq` and `treefmt` on PATH — everything `tools/` shells out to. The scripts are executable
and run by path:

```bash
tools/catalog.py add <Name>
```

## Adding an addon

1. `tools/catalog.py add <CatalogName>` — prefetches the hash, writes `nix/addons.json`.
2. Write `nix/packages/<name>.nix`:

   ```nix
   { pkgs, flake, ... }:
   flake.lib.mkAddon { inherit pkgs; } "<CatalogName>" { }
   ```

   The first argument is the **catalogue key**, not the package name. They differ often
   (`kicadStepUpMod` → `kicad-stepup`), and `pname` is what fixes that.
3. Add it to `nix/lib/addons.nix`, with the category it belongs under. That file is the
   only list — `addon-shapes` verifies from it and the README is generated from it, so
   there is no second place to forget.
4. `nix run .#gen-readme`.
5. `nix build .#<name>` — `mkAddon`'s install check resolves the entry point and fails if
   the addon does not contain what its `package.xml` claims.

Reach `mkAddon` through `flake.lib`, not a relative `import`. Blueprint passes every
package a `flake` argument, so the packages exercise the same export an outside consumer
gets — a break in it fails the build here rather than only somewhere else.

## Licences

**Never infer one from a string.** `tools/catalog.py` resolves what it safely can and
leaves the rest null; 45 of 173 addons cannot be resolved and 27 declare none at all. A
name without `-only` or `-or-later` (`AGPLv3.0`, `LGPL-3`) is not resolvable, because the
difference is whether a user may move the work to a later licence.

When the lock has `"spdx": null`, read the source and declare it where the addon is
packaged, **with the evidence in a comment**. Two worked examples:

- `nix/packages/kicad-stepup.nix` — upstream ships no LICENSE at all.
- `nix/packages/freecad-pcb.nix` — the manifest and the source contradict each other.

A licence resolved by hand is a decision; `catalog.py update` deliberately keeps it rather
than dropping back to null.

## Updating

Every versioned package must have a route, or `tools/discovery.py` reports it as
`unroutable` and the job stops. Four routes:

| Route | How it is detected | Moved by |
| --- | --- | --- |
| `flake-input` | the name is a flake input | `nix flake update <input>` |
| `catalog` | `passthru.catalogName` is set (i.e. built by `mkAddon`) | `tools/catalog.py update <CatalogName>` |
| `nix-update` | `nix/packages/<name>/nix-update-args` exists | `nix-update` |
| `manual` | declared in `discovery.py` | reported, never acted on |

A package with no `version` is exempt — `stepz` and `gen-readme` have none, because there
is nothing upstream to compare against.

Running `tools/update.py --kind catalog --name <n> --catalog-name <N>` really does bump
things. It re-downloads the catalogue, so it can pick up an unrelated upstream move; keep
those out of structural commits.

`freecad-weekly` has an independent pin and no visual patches. `tools/weekly.py` queries
upstream without changing files by default; `--publish` is restricted to a clean Actions
checkout of the default branch. It builds and tests the candidate, uploads its signed
closure to the configured native Nix cache, then atomically publishes `weekly` and an
immutable tag. The general PR updater excludes it. The two FreeCAD packages share
`flake.lib.mkFreeCAD`; changes there must preserve both variants' runtime tests.

## Style

- `nix fmt` runs treefmt, configured entirely in `nix/formatter.nix`: deadnix → statix →
  nixfmt for `*.nix` (in that order, by explicit priority), ruff-format, jsonfmt, yamlfmt,
  taplo, plus actionlint, shellcheck and ruff-check as report-only.
- **Python is 88 columns everywhere, ruff's default.** Do not set `lineLength` in
  `nix/formatter.nix`: treefmt passes it as `--line-length`, a flag beats a config file,
  and it reaches every Python file — including `nix/packages/stepz/`, which its own gate
  then fails at 88. Nothing needs a `ruff.toml`.
- **`ruff-check` runs with `--fix` forced off.** treefmt hardcodes the fix; a lint autofix
  is not formatting, and its first run here deleted four `# noqa` directives and the prose
  explaining one of them. `settings.formatter.ruff-check.options` overrides it.
- No Markdown formatter: README.md holds a generated block that `readme-current` compares
  byte for byte, and a reflow would fight it.
- Python: type hints, `from __future__ import annotations`, ruff's default rule set.
  `nix/packages/stepz/` is the exception and keeps its own `pyproject.toml` — it is a
  publishable module with its own gate, and ruff resolves the nearest config per file.
- **Comments say why, not what.** A comment restating `meta.description`, or narrating
  history that `git log` already carries, gets deleted. The ones worth keeping explain a
  decision that the code cannot: a licence read off the source, why `pname` differs from
  the catalogue key, why `stepz` exists at all.
- **A claim nothing checks is a claim that drifts.** Prefer asserting it. See
  `freecad-mcp`'s `postPatch`, which fails when upstream's `pyproject.toml` disagrees with
  the packaged version, and `readme-current`, which fails when the table does.

## Testing changes

- `nix build .#<package>` for one package; its install check is the real gate.
- `nix flake check` before pushing.
- When a change should not alter what is built — renames, moves, comments — prove it by
  comparing `drvPath` before and after:

  ```bash
  nix eval --json .#packages.x86_64-linux --apply 'ps: builtins.mapAttrs (_: p: p.drvPath) ps'
  ```

  Comments cannot affect a derivation, but `mkAddon` takes `tools/check_addon_shape.py` as
  a build input, so editing that script legitimately moves all sixteen catalogue addons.

## Commits

- `<package>: summary`; version bumps as `<package>: X -> Y`; new packages as
  `<package>: init at X.Y.Z`.
- Run `nix fmt` and `nix flake check` before pushing.
- Nothing auto-merges.
