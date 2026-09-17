# freecad.nix

FreeCAD's weekly development build and nineteen extensions, packaged for Nix.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## About

FreeCAD's Addon Manager installs extensions by cloning them into
`~/.local/share/FreeCAD/Mod/`, which leaves you with a directory nothing pins and nothing
reproduces. This flake packages them instead: every extension is a derivation with a
version, a licence and a content hash, and a build that fails when an addon stops
containing what it claims to.

What you get:

- **`freecad-weekly`** — an upstream *weekly tag*, with the fixes needed for Nix.
  Its automated channel builds and tests each new snapshot before publishing it.
- **`freecad-unstable`** — an independently pinned weekly, with the custom title bar from
  [FreeCAD#26766](https://github.com/FreeCAD/FreeCAD/pull/26766) applied.
- **Nineteen extensions**, sixteen resolved from FreeCAD's own addon catalogue and three
  packaged directly. They are ordinary derivations and work with any FreeCAD, including
  the `freecad` in nixpkgs.
- **A bump engine** that knows how each of the 25 moving parts updates, and refuses to
  leave a new one pinned forever.

There is deliberately **no combined package**. Addons are exposed one by one so you
choose what to load, which is also how `--module-path` works.

## Requirements

Nix with flakes enabled:

```
experimental-features = nix-command flakes
```

## Usage

Once the [weekly channel is enabled](#the-automatic-weekly-channel), run its latest
successfully tested build:

```bash
nix run github:aldoborrero/freecad.nix/weekly#freecad-weekly
```

The default branch also exposes `#freecad-weekly` at its maintenance pin. Use
`#freecad-unstable` for the separately maintained title-bar and tab-position patches.
That variant can lag behind the automatic channel when its patches need adapting.

Add extensions with `--module-path`, which FreeCAD accepts more than once:

```bash
nix run github:aldoborrero/freecad.nix#freecad-unstable -- \
  --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#gridfinity)" \
  --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#curves)"
```

Two extensions keep their module below the store root, and `--module-path` wants that
inner directory rather than `$out`. `passthru.modulePath` says which:

```bash
nix eval --raw .#freecad-timeline.modulePath   # Mod/Timeline
nix eval --raw .#freecad-mcp.modulePath        # share/freecad-mcp/FreeCADMCP
```

### As a flake input

```nix
{
  inputs.freecad-nix.url = "github:aldoborrero/freecad.nix/weekly";

  outputs = { nixpkgs, freecad-nix, ... }: {
    # e.g. in a NixOS module
    environment.systemPackages = [
      freecad-nix.packages.x86_64-linux.freecad-weekly
      freecad-nix.packages.x86_64-linux.gridfinity
    ];
  };
}
```

`freecad-nix.lib.mkAddon` is exported too, if you want to build an addon from this repo's
catalogue lock in your own tree.

A flake input stays pinned until you run `nix flake update freecad-nix` in the consuming
repository. Follow a published `weekly-<date>-<system>-<recipe>` tag instead of `weekly`
when you want to retain a particular tested build.

## The extensions

<!-- BEGIN GENERATED EXTENSIONS -->

### Modelling

<details>
<summary><strong>curves</strong> — A collection of tools mainly dedicated to NURBS curves and surfaces modeling.</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 0.6.75
- **Licence**: LGPL-2.1-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#curves)"`
- **Nix**: [nix/packages/curves.nix](nix/packages/curves.nix)

</details>

<details>
<summary><strong>dynamicdata</strong> — Container object for holding custom properties, alternative to spreadsheet</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 2.78
- **Licence**: LGPL-2.1-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#dynamicdata)"`
- **Nix**: [nix/packages/dynamicdata.nix](nix/packages/dynamicdata.nix)

</details>

<details>
<summary><strong>lattice2</strong> — Tools and arrays of all sorts and kinds, and local coordinate systems</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 1.1
- **Licence**: LGPL-2.0-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#lattice2)"`
- **Nix**: [nix/packages/lattice2.nix](nix/packages/lattice2.nix)

</details>

<details>
<summary><strong>meshremodel</strong> — Workbench for remodeling and repairing mesh objects.</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 1.11.0
- **Licence**: LGPL-2.1-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#meshremodel)"`
- **Nix**: [nix/packages/meshremodel.nix](nix/packages/meshremodel.nix)

</details>

<details>
<summary><strong>silk</strong> — NURBS Surface modeling tools focused on low degree and seam continuity</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 0.4.0
- **Licence**: GPL-3.0-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#silk)"`
- **Nix**: [nix/packages/silk.nix](nix/packages/silk.nix)

</details>

### Assemblies and mechanical parts

<details>
<summary><strong>fasteners</strong> — Some common fasteners and fastener tools for FreeCAD.</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 0.5.64
- **Licence**: GPL-2.0-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#fasteners)"`
- **Nix**: [nix/packages/fasteners.nix](nix/packages/fasteners.nix)

</details>

<details>
<summary><strong>freecad-gears</strong> — A gear workbench for FreeCAD</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 1.3
- **Licence**: GPL-3.0-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#freecad-gears)"`
- **Nix**: [nix/packages/freecad-gears.nix](nix/packages/freecad-gears.nix)

</details>

<details>
<summary><strong>sheetmetal</strong> — A simple sheet metal tools workbench for FreeCAD.</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 0.8.21
- **Licence**: LGPL-2.1-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#sheetmetal)"`
- **Nix**: [nix/packages/sheetmetal.nix](nix/packages/sheetmetal.nix)

</details>

### 3D printing

<details>
<summary><strong>gridfinity</strong> — This Workbench will generate several variations of parametric Gridfinity bins and baseplates that can be easily customized.</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 0.12.4
- **Licence**: LGPL-2.1-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#gridfinity)"`
- **Nix**: [nix/packages/gridfinity.nix](nix/packages/gridfinity.nix)

</details>

<details>
<summary><strong>slicercad</strong> — FreeCAD addon: printer-bed preview, fit checking, and export to a slicer</summary>

- **Source**: [its own repo](https://github.com/aldoborrero/slicercad)
- **Version**: 0.1.0
- **Licence**: AGPL-3.0-only
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#slicercad)"`
- **Nix**: [nix/packages/slicercad.nix](nix/packages/slicercad.nix)

</details>

### KiCad and electronics

<details>
<summary><strong>free2ki</strong> — Export your 3D models to VRML files, with correctly applied rotation and scaling, for use in KiCad as well as Blender.</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 1.1.2
- **Licence**: GPL-3.0-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#free2ki)"`
- **Nix**: [nix/packages/free2ki.nix](nix/packages/free2ki.nix)

</details>

<details>
<summary><strong>freecad-pcb</strong> — Printed Circuit Board (PCB) Workbench for FreeCAD</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 6.2023.1
- **Licence**: LGPL-2.0-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#freecad-pcb)"`
- **Nix**: [nix/packages/freecad-pcb.nix](nix/packages/freecad-pcb.nix)

</details>

<details>
<summary><strong>kicad-stepup</strong> — A bidirectional ECAD/MCAD collaboration between KiCAD and FreeCAD.</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 11.09.5
- **Licence**: AGPL-3.0-only
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#kicad-stepup)"`
- **Nix**: [nix/packages/kicad-stepup.nix](nix/packages/kicad-stepup.nix)

</details>

<details>
<summary><strong>kiconnect</strong> — PCB Syncronization with KiCAD v9+</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 1.0.1
- **Licence**: LGPL-2.1-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#kiconnect)"`
- **Nix**: [nix/packages/kiconnect.nix](nix/packages/kiconnect.nix)

</details>

### Interface

<details>
<summary><strong>color-palette-theme</strong> — Choose your colors with the "ColorPalette" Theme and increase the focus on objects and texts(FreeCAD v1.1.0 ≥)</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 2.3.3
- **Licence**: LGPL-2.1-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#color-palette-theme)"`
- **Nix**: [nix/packages/color-palette-theme.nix](nix/packages/color-palette-theme.nix)

</details>

<details>
<summary><strong>freecad-ribbon</strong> — A Ribbon interface for FreeCAD</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 1.11.3
- **Licence**: GPL-3.0-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#freecad-ribbon)"`
- **Nix**: [nix/packages/freecad-ribbon.nix](nix/packages/freecad-ribbon.nix)

</details>

<details>
<summary><strong>freecad-timeline</strong> — FreeCAD addon: a Fusion-style feature timeline docked under the 3D view</summary>

- **Source**: [its own repo](https://github.com/aldoborrero/freecad-timeline)
- **Version**: 1.0.0
- **Licence**: LGPL-2.1-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#freecad-timeline)/Mod/Timeline"`
- **Nix**: [nix/packages/freecad-timeline.nix](nix/packages/freecad-timeline.nix)

</details>

<details>
<summary><strong>piemenu</strong> — The PieMenu module is a tool to accelerate and simplify your workflow in usage of FreeCAD.</summary>

- **Source**: FreeCAD's catalogue
- **Version**: 1.13
- **Licence**: LGPL-2.1-or-later
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#piemenu)"`
- **Nix**: [nix/packages/piemenu.nix](nix/packages/piemenu.nix)

</details>

### Automation

<details>
<summary><strong>freecad-mcp</strong> — MCP server for FreeCAD: drives a running FreeCAD over XML-RPC</summary>

- **Source**: [neka-nat](https://github.com/neka-nat/freecad-mcp)
- **Version**: 0.1.21
- **Licence**: MIT
- **Use**: `nix run github:aldoborrero/freecad.nix#freecad-unstable -- --module-path "$(nix build --no-link --print-out-paths github:aldoborrero/freecad.nix#freecad-mcp)/share/freecad-mcp/FreeCADMCP"`
- **Nix**: [nix/packages/freecad-mcp/default.nix](nix/packages/freecad-mcp/default.nix)

</details>

<!-- END GENERATED EXTENSIONS -->

**That list is generated** — `nix run .#gen-readme` writes it, and `nix flake check` fails
when it drifts. Every field comes from the package's own `meta` and `passthru`, so an entry
can only say what the package says.

Two licences are declared by hand, because their manifests cannot be trusted:

- **`kicad-stepup`** says `AGPLv3.0`, which names a version but not whether it is `-only`
  or `-or-later`. There is no LICENSE file at all; no source header grants a later
  version, so the narrow reading is the honest one.
- **`freecad-pcb`** says `AGPLv3.0` in a `<license file="LICENSE">` pointing at a file
  **that does not exist**, while its README and every source header grant "LGPL … either
  version 2 … or (at your option) any later version". The grants the code carries win.

`stepz` is in the flake but **not** in the table, because it is not an addon — it is a
plain importable module. nixpkgs builds `kicad-packages3d` with `compressStep ? true`,
zipping every `.step` into a `.stpZ`; kicadStepUp then calls `stepZ.insert()`, FreeCAD has
no importer for the extension, and a board imports with its outline and not one component.
Upstream's addon of that name opens gzip where nixpkgs writes PKZIP, and does not import
on Python 3 anyway. The better fix is upstream — `kicadStepUptools.py:469` already does
`import zipfile as zf` — and if it lands, this package goes.

`freecad-mcp` is the other odd one: a Python *application* (an MCP server run outside
FreeCAD) that also carries a workbench answering it over XML-RPC. That half only imports
inside FreeCAD, so it ships as data and `passthru.modulePath` points at it.

## Adding an extension from the catalogue

FreeCAD publishes a catalogue of every addon it knows about — 173 of them — which
`tools/catalog.py` reads:

```bash
tools/catalog.py list --content workbench     # what exists
tools/catalog.py add Gridfinity               # lock it at what the catalogue pins
tools/catalog.py update                       # move locked addons forward
```

Then write the package — three lines, because everything else is in the lock:

```nix
# nix/packages/gridfinity.nix
{ pkgs, flake, ... }:
flake.lib.mkAddon { inherit pkgs; } "Gridfinity" { }
```

Add it to `nix/lib/addons.nix` and run `nix run .#gen-readme`.

The catalogue gives `repository` and a pinned `git_hash` for all 173, but no content hash,
so `add` prefetches one and writes `nix/addons.json`.

**On filtering.** The catalogue's compatibility fields cannot do it: 3 of 173 declare a
`freecad_max` and none declare a `freecad_min` below 0.20. Staleness is reported and never
acted on, because an addon that needs no commits is not thereby broken. What an addon must
pass is the shape check: if its `package.xml` claims a `workbench`, then one of the three
places FreeCAD looks has to have it — `InitGui.py` at the root, `<subdirectory>/InitGui.py`
where the manifest says, or `freecad/*/init_gui.py` for a namespace package. Otherwise
FreeCAD starts with the addon installed and nothing on screen.

What does disqualify one is upstream targeting something else. Assembly4 is maintained,
but its `InitGui.py` accepts FreeCAD 0.19–0.21 and 2.x and prints an error on everything
between, and the "2.x" it points at is a fork rather than upstream — whose current release
is 1.1. FreeCAD 1.x ships an Assembly workbench anyway, so it is not packaged.

**On licences.** 45 of 173 cannot be resolved automatically, and 27 declare none at all.
The rest name a version without saying `-only` or `-or-later`, and that difference is
whether a user may move the work to a later licence — so it is never inferred from a
string. Those stay null in the lock and must be declared where the addon is packaged, with
the evidence.

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
request. It excludes `freecad-weekly`, which has the separate publishing path below.

### The automatic weekly channel

[FreeCAD weekly](.github/workflows/weekly.yml) polls the official FreeCAD releases every
six hours, at minute 17, and can also be run manually from the default branch. GitHub can
delay scheduled runs; this is polling, not a release-time guarantee.

`tools/weekly.py` accepts only dated `weekly-YYYY.MM.DD` releases, including prereleases.
It updates only `nix/packages/freecad-weekly/default.nix`, leaving `flake.lock`, addons
and the visual variant alone. The initial package pin remains `2026.08.20`; the first
enabled run fetches the newest upstream weekly and its hash.

Before publishing, the job checks patch application, automation tests, generated docs
and formatting, compiles FreeCAD, checks its reported version and runs all its inherited
runtime tests against that binary. It signs and uploads **all package outputs and their
closures** to a native Nix binary cache using `nix copy`. No Cachix cache is configured.

Only then does an atomic Git push update the bot-owned `weekly` branch and create an
immutable `weekly-<date>-<system>-<recipe>` tag. `.weekly.json` records the upstream date,
tested system and default-branch revision. Unchanged snapshots are skipped; changes to
the packaging revision are rebuilt. A failing build, test, upload or push leaves the
previous channel available. Concurrent changes to `weekly` are protected by a Git lease;
if the default branch has advanced by the final check, the job aborts and the next poll
retries from the new recipe. There is no merge into the default branch.

#### Enable it

The workflow is opt-in until the runner and replacement cache are ready. Configure
these in GitHub **Settings → Secrets and variables → Actions**:

| Kind | Name | Value |
| --- | --- | --- |
| Variable | `WEEKLY_ENABLED` | `true`, after the remaining setup |
| Variable | `WEEKLY_CACHE_URI` | Writable native Nix store, e.g. `s3://your-bucket?region=eu-west-1`; compatible providers can add `&endpoint=your-endpoint` |
| Variable | `WEEKLY_CACHE_URL` | Public read URL of the cache, normally HTTPS |
| Variable | `WEEKLY_CACHE_PUBLIC_KEY` | Public Nix signing key trusted by consumers |
| Secret | `NIX_SIGNING_KEY` | Matching private Nix signing key |
| Secret | `WEEKLY_CACHE_ACCESS_KEY_ID` | Cache-only S3 credentials, when required |
| Secret | `WEEKLY_CACHE_SECRET_ACCESS_KEY` | Matching secret access key |
| Variable | `WEEKLY_CACHE_REGION` | Provider's region; defaults to `us-east-1` |
| Variable | `WEEKLY_RUNNER` | JSON runner label or label array; defaults to `"ubuntu-24.04"` |
| Variable | `WEEKLY_SYSTEM` | Native runner system; defaults to `x86_64-linux` |

The destination and credentials are deployment settings. Choose the cache provider before
enabling publication. Other stores supported by `nix copy` need their own authentication
setup in the workflow. See the official
[Nix S3 store documentation](https://nix.dev/manual/nix/2.35/store/types/s3-binary-cache-store)
and [binary cache setup](https://nix.dev/tutorials/nixos/binary-cache-setup.html).

Allow Actions to write repository contents. Reserve `weekly` and the `weekly-*` tags for
the publisher; branch/tag rules must permit its atomic push and rolling branch updates.
Keep the workflow on the default branch, enable it and run **FreeCAD weekly → Run
workflow**. The first successful run creates the channel. Normal Actions failure
notifications report failures; re-running the workflow retries the same candidate.

FreeCAD needs substantial RAM, disk and build time. A larger or persistent native runner
is preferable if the standard hosted runner hits its limits. For example,
`["self-hosted", "linux", "x64", "freecad"]` selects a dedicated runner. The workflow
limits Nix to one build job and two compiler cores. It publishes **one architecture per
channel**, initially x86_64 Linux; choosing `aarch64-linux` also requires an ARM runner.
Both package outputs remain exposed by the flake, but another architecture is not
claimed as compiled or cached by this job.

Consumers must configure `extra-substituters` with the public cache URL and
`extra-trusted-public-keys` with its public key in `nix.conf` or their NixOS configuration.
Without that, Nix may compile locally. The private signing key stays in Actions secrets.
To roll back, pin a previous immutable tag in the consuming flake; no history rewrite
or automated downgrade is needed.

For a read-only upstream query, run `tools/weekly.py`. `--publish` is restricted to a
clean Actions checkout of the default branch. Regression tests use temporary local
Git repositories to exercise failed builds/uploads, duplicate runs, tag conflicts and
concurrent channel updates.

## Development

```bash
nix flake check          # everything, including both FreeCAD C++ builds
nix fmt                  # treefmt
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

See [AGENTS.md](AGENTS.md) for repository conventions.

## Contributing

Issues and pull requests are welcome. Before pushing, run `nix fmt` and `nix flake check`.

Extensions are packages here, not `flake = false` inputs: a bare source tree has no `meta`,
so its licence would have to be written down by hand and kept honest by hand, and nothing
could bump it because it has no version to compare.

## License

freecad.nix is licensed under the MIT license. See [`LICENSE`](LICENSE) for details.

This covers the packaging in this repository. The extensions it builds carry their own
licences — see the table above — and FreeCAD itself is LGPL-2.1-or-later.
