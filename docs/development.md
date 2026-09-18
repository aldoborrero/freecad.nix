# Development and updates

[← Back to the README](../README.md)

Run these commands from the repository root, inside `nix develop`.

## Development

```bash
nix flake check          # everything, including both FreeCAD C++ builds
nix fmt                 # treefmt
nix run .#gen-readme     # rewrite the extensions table
```

The check worth running on every change is much cheaper than the full set:

```bash
nix build .#checks.x86_64-linux.patches-apply
```

It applies every patch to the fetched source and judges how it landed. **Offsets are
noise** — upstream inserted lines above the anchor and `patch` found it anyway; they reach
415 lines and nothing breaks. **Fuzz is signal**: the context did not match and the hunk
was placed by approximation, which is how a change lands in the wrong function while the
build stays green. Every fuzzed hunk must be declared in `nix/patches/expected.json` with a
note saying somebody looked at where it went, and a declaration that stops being needed
also fails, so stale exemptions cannot pile up.

`addon-shapes` runs over all nineteen **at the path FreeCAD would be pointed at**, which is
not the store root for all of them. Getting that wrong does not fail loudly on its own —
FreeCAD would load an addon called `xxxxxxxx-freecad-timeline-1.0.0`, or load nothing and
say nothing.

See [AGENTS.md](../AGENTS.md) for repository conventions.

## Keeping it current

`tools/discovery.py` works out what can move and how; `tools/update.py` moves one thing.
Both set GitHub Actions outputs only when `GITHUB_OUTPUT` is set, so they run the same
under a workflow, a self-hosted runner, or a terminal.

```
$ tools/discovery.py
25 targets: {'catalog': 16, 'nix-update': 3, 'flake-input': 5, 'manual': 1}
```

| Route | Who | Moved by |
| --- | --- | --- |
| `flake-input` | nixpkgs, blueprint, treefmt-nix, and the two addons with their own repos | `nix flake update <input>` |
| `nix-update` | a package pinning its own `src` | `nix-update`, plus `nix/packages/<name>/nix-update-args` |
| `catalog` | an addon from `nix/addons.json` | `tools/catalog.py update <CatalogName>` |
| `manual` | upstream's title-bar PR, fetched at two pinned SHAs | reported, never acted on |

**A versioned package with no route is an error.** That is the point of discovering rather
than listing: adding a package and forgetting to say how it moves stops the job instead of
leaving it pinned forever.

**Nothing auto-merges.** The general bump job runs the cheap checks and opens a pull
request. It excludes `freecad-weekly`, which has its own
[publishing workflow](weekly-channel.md).
