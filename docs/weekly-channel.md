# The automatic weekly channel

[← Back to the README](../README.md)

[FreeCAD weekly](../.github/workflows/weekly.yml) polls the official FreeCAD releases every
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

## Enable it

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
