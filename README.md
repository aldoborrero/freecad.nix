# freecad.nix

FreeCAD, its extensions, and the patches that make it look like a 2026 CAD program.

Two tracks, on purpose:

| | what it is | how it moves |
|---|---|---|
| `freecad` | the release nixpkgs packages, plus this repo's patches, addons and preferences | with the `nixpkgs` input |
| `freecad-unstable` | an upstream **weekly tag**, same patches | `nix-update`, on its own schedule |

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

## Adding an extension

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

**On licences.** 32 of 173 cannot be resolved automatically. 27 declare none at all; the
rest write things like `LGPL-3`, which does not say `-only` or `-or-later`, or `GPLv2.1`,
which is not a licence that exists. Those are left null in the lock and must be declared
where the addon is packaged. Guessing a licence is not a rounding error.
