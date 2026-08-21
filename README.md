# freecad.nix

FreeCAD, its extensions, and the patches that make it look like a 2026 CAD program.

Two tracks, on purpose:

| | what it is | how it moves |
|---|---|---|
| `freecad` | the release nixpkgs packages, plus this repo's patches, addons and preferences | with the `nixpkgs` input |
| `freecad-unstable` | an upstream **weekly tag**, plus the title bar | `nix-update`, on its own schedule |

**Only the weekly build has the custom title bar**, and it gets it from upstream's own
pull request — [FreeCAD#26766](https://github.com/FreeCAD/FreeCAD/pull/26766), by
PaddleStroke, the same work AstoCAD carries. Against the pinned tag that diff applies
exactly: 0 failed hunks, 0 fuzz, largest offset 0 lines. It does *not* apply to the
release, where 7 hunks fail, so the release simply does without until the PR lands.

This repo used to carry a 130-line backport of it written against 1.1.1, with 5497 lines
of vendored `customtitlebarkit` beside it. That is gone. It was a subset — no preferences
page, so the feature could only be switched on from Nix, and none of the
`ToolBarManager.h` change that may be the toolbar docking the review is waiting on — and
maintaining a worse copy of an open PR was not worth it.

Extensions are packages here, not `flake = false` inputs. A bare source tree has no
`meta`, so its licence has to be written down by hand and kept honest by hand, and
nothing can bump it because it has no version to compare.

## Checks

`nix flake check` builds both FreeCADs, which is two long C++ compiles. The check worth
running on every change is much cheaper:

```
nix build .#checks.x86_64-linux.patches-apply
```

It applies every patch to the fetched source and judges how it landed. **Offsets are
noise** — upstream inserted lines above the anchor and `patch` found it anyway; they
reach 415 lines already and nothing breaks. **Fuzz is signal**: the context did not
match and the hunk was placed by approximation, which is how a change lands in the wrong
function while the build stays green. Every fuzzed hunk must be declared in
`nix/patches/expected.json` with a note saying somebody looked at where it went, and a
declaration that stops being needed also fails, so stale exemptions cannot pile up.

## The extensions

Five so far, from two different places:

| Addon | Where it comes from | Licence | Layout |
| --- | --- | --- | --- |
| `gridfinity` | FreeCAD's catalogue | LGPL-2.1-or-later | `freecad/gridfinity_workbench/init_gui.py` |
| `curves` | FreeCAD's catalogue | LGPL-2.1-or-later | `freecad/Curves/init_gui.py` |
| `kicad-stepup` | FreeCAD's catalogue | AGPL-3.0-only ¹ | `InitGui.py` |
| `freecad-timeline` | [its own repo](https://github.com/aldoborrero/freecad-timeline) | LGPL-2.1-or-later | `InitGui.py`, under `Mod/Timeline` |
| `slicercad` | [its own repo](https://github.com/aldoborrero/slicercad) | AGPL-3.0-only | `freecad/slicercad/init_gui.py` |
| `freecad-mcp` | [neka-nat](https://github.com/neka-nat/freecad-mcp) | MIT | `InitGui.py`, under `share/freecad-mcp/FreeCADMCP` |

`stepz` sits beside them and is **not** an addon — it is a plain importable module, so it
is absent from the table and from the shape check, which rejects it correctly. It exists
only to repair a consequence of packaging: nixpkgs builds `kicad-packages3d` with
`compressStep ? true`, leaving 7241 `.stpZ` and no `.step`, and kicadStepUp reaches those
through a `stepZ` addon that opens gzip where `zip -j -9` writes PKZIP — and which does
not import on Python 3 regardless. Without it a board imports with its outline and not one
component. The better fix is upstream, and is not blocked on anything:
`kicadStepUptools.py:469` already does `import zipfile as zf`, so reading the archive
there needs no new dependency. If that lands, this package can go.

<sub>¹ declared by hand: its manifest says `AGPLv3.0`, which names a version but not
whether it is `-only` or `-or-later`.</sub>

`freecad-mcp` is the odd one: a Python *application* — the MCP server a client runs
outside FreeCAD — that also carries a workbench answering it over XML-RPC. That half
cannot be a Python module of the package, since it only imports inside FreeCAD, so it
ships as data and `passthru.modulePath` points at it. From the check's side that makes it
indistinguishable from any other addon, which is the point of the field.

The two written here come in as **flakes**, not as source trees, so what arrives already
has a version, a `meta` and its own gate behind it. The three from the catalogue are built
by `nix/lib/mkAddon.nix` out of `nix/addons.json`.

`nix flake check` runs `addon-shapes` over all five **at the path FreeCAD would be pointed
at**, which is not the same as the store root for all of them: Timeline keeps its module
in `Mod/Timeline` and says so through `passthru.modulePath`, while Slicercad's store root
*is* the module. Getting that wrong does not fail loudly on its own — FreeCAD would load
an addon called `xxxxxxxx-freecad-timeline-1.0.0`, or load nothing and say nothing.

## Adding an extension from the catalogue

FreeCAD 1.1 publishes a catalogue of every addon it knows about — 173 of them — which
`tools/catalog.py` reads:

```
tools/catalog.py list --content workbench     # what exists
tools/catalog.py add Gridfinity               # lock it at what the catalogue pins
tools/catalog.py update                       # move locked addons forward
```

The catalogue gives `repository` and a pinned `git_hash` for all 173. It does not give a
content hash, so `add` prefetches one and writes `nix/addons.json` — the same shape
nixpkgs uses for terraform providers, where a generated `providers.json` holds
owner/repo/rev/hash/spdx and a constructor is mapped over it.

**On filtering.** The catalogue's compatibility fields cannot do it: 3 of 173 declare a
`freecad_max` and none declare a `freecad_min` below 0.20. The only real signal is how
long ago upstream last touched the addon — median 126 days, but 29 have not been touched
in two years — and that is a warning, not a verdict, because an addon that needs no
commits is not thereby broken. What an addon does have to pass is the shape check: if
its `package.xml` claims a `workbench`, then `InitGui.py` or `freecad/*/init_gui.py` has
to exist, or FreeCAD will start with the addon installed and nothing on screen.

**On licences.** 45 of 173 cannot be resolved automatically. 27 declare none at all. The
rest name a version without saying whether it is `-only` or `-or-later` — `LGPL-3`,
`LGPLv2.1`, `AGPLv3.0` — and that difference is whether a user may move the work to a
later licence, so it is not inferred from a string. (`GPLv2.1` is in there too, and no
such licence exists.) Those stay null in the lock and must be declared where the addon
is packaged, with the evidence; see `nix/packages/kicad-stepup` for what that looks like
when upstream ships no LICENSE file at all.

## Keeping it current

`tools/discovery.py` works out what can move and how; `tools/update.py` moves one thing.
Both print their result and set GitHub Actions outputs only when `GITHUB_OUTPUT` happens
to be set, so they run the same under a workflow, a self-hosted runner, or a terminal.
`.github/workflows/update.yml` is one driver, and is deletable — nothing decides anything
there.

```
$ tools/discovery.py
11 targets: {'catalog': 3, 'nix-update': 2, 'flake-input': 5, 'manual': 1}
```

**Four routes, because there are four kinds of thing here:**

| Route | Who | Moved by |
| --- | --- | --- |
| `flake-input` | nixpkgs, blueprint, treefmt-nix, and the two addons with their own repos | `nix flake update <input>` |
| `nix-update` | a package pinning its own `src` | `nix-update`, plus `nix/packages/<name>/nix-update-args` |
| `catalog` | an addon from `nix/addons.json` | `tools/catalog.py update <CatalogName>` |
| `manual` | upstream's title-bar PR, fetched at two pinned SHAs | reported, never acted on |

**A versioned package with no route is an error.** That is the point of discovering
rather than listing: adding a package and forgetting to say how it moves stops the job
instead of leaving it pinned forever. `stepz` has no `version` and is exempt — its source
is here, so there is nothing upstream to compare against.

**Nothing auto-merges.** The bump job runs `patches-apply`, `addon-shapes` and
`stepz-python` — seconds, and the ones that actually guard a bump — but not
`nix flake check`, which builds FreeCAD. A weekly tag can move code out from under three
patches while every one of those still passes, because they check that the patches
*apply*, not that the result behaves.
