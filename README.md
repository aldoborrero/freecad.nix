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
