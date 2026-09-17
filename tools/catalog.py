#!/usr/bin/env python3
"""FreeCAD's addon catalogue, as a source for Nix packages.

FreeCAD 1.1 replaced the old `.gitmodules` addon list with a catalogue the Addon
Manager downloads from `addons.freecad.org` (see `addonmanager_preferences_defaults.json`
in FreeCAD's tree, and `src/Mod/AddonManager/AddonCatalog.py`, which warns that its entry
class must stay identical to the one generating the remote cache). Every entry carries
`repository` and a pinned `git_hash`, and most carry the addon's `package.xml` verbatim.

That is nearly everything a package needs. What it does not carry is a content hash, so
`add` prefetches one, and the result is written to a lock file — the same shape nixpkgs
uses for terraform providers, where `providers.json` holds owner/repo/rev/hash/spdx per
provider and `default.nix` maps a constructor over it. 168 providers there, 173 addons
here; the problem is the same size and the same shape.

Two things this deliberately does NOT do.

**It does not decide what works.** The catalogue's compatibility fields are almost
empty — of 173 addons, 3 declare a `freecad_max` and none declare a `freecad_min` below
0.20 — so they filter nothing. The only real signal is how long ago upstream last
touched the thing (median 126 days, but the 90th percentile is 3.7 years), and an addon
that has not needed a commit in two years is not thereby broken. So `list` *reports*
staleness and never acts on it. Whether an addon works is answered by building it and
checking that it exposes what its `package.xml` claims, not by a date.

**It does not resolve every licence.** Addons declare licences as free text: 26 distinct
strings across 148 addons, of which 113 are exact SPDX identifiers and the rest are
`LGPLv2.1`, `AGPLv3.0`, `LGPLv3` and friends. Anything unrecognised is written to the
lock as null, and packaging it then has to say what it is by hand. nixpkgs does the same
for the providers whose licence GitHub reports wrongly.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import logging
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

log = logging.getLogger("catalog")

CATALOG_URL = "https://addons.freecad.org/addon_catalog_cache.zip"
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".scratch" / "addon_catalog_cache.json"
LOCK = ROOT / "nix" / "addons.json"

# Free text in practice, so this maps what upstream actually writes rather than trying to
# be a general SPDX parser. Anything absent stays null in the lock and has to be declared
# where the addon is packaged — never guessed.
# Only spellings that cannot change what the licence permits. Notably absent: every
# `LGPLv2.1`, `GPLv3`, `AGPLv3` form. Those name a version but not whether it is `-only`
# or `-or-later`, and the difference is whether a user may move the work to a later
# licence — not a detail to infer from a string. They go to the by-hand pile with
# `LGPL-3` and `GPL-3`, which have exactly the same defect.
SPDX = {
    "apache 2.0": "Apache-2.0",
    "apache license 2.0": "Apache-2.0",
    "mit license": "MIT",
}
# Matched case-insensitively, then reported in canonical case: several addons write a
# perfectly good identifier in lower case, and rejecting those would send them to the
# by-hand pile for no reason.
CANONICAL = [
    "LGPL-2.0-or-later",
    "LGPL-2.1-only",
    "LGPL-2.1-or-later",
    "LGPL-3.0-only",
    "LGPL-3.0-or-later",
    "GPL-2.0-only",
    "GPL-2.0-or-later",
    "GPL-3.0-only",
    "GPL-3.0-or-later",
    "AGPL-3.0-only",
    "AGPL-3.0-or-later",
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "MPL-2.0",
    "CC0-1.0",
    "CC-BY-3.0",
    "CC-BY-4.0",
    "CC-BY-SA-3.0",
    "CC-BY-SA-4.0",
    "GPL-3.0",
    "GPL-2.0",
    "Unlicense",
]

# Left deliberately unresolved, and each for a reason worth keeping:
#
#   'LGPL-3', 'GPL-3'  ambiguous — they do not say -only or -or-later, and picking one
#                      changes what the licence permits. Not ours to guess.
#   'GPLv2.1'          no such licence. GPL has no 2.1; LGPL does. Ask upstream.
#   'CCOv1'            probably CC0-1.0, and "probably" is not good enough for a licence.
#   (no <license>)     27 addons, most of them the 25 with no usable package.xml.
BY_LOWER = {c.lower(): c for c in CANONICAL}


def write_lock(lock: dict[str, Any]) -> str:
    """`nix/addons.json`, in the one form both writers of it produce.

    `nix fmt` runs `jsonfmt` over this file too, so the two have to agree or every update
    and every format would undo the other. They do, and the non-obvious half is escaping:
    several descriptions carry characters like `≥`, Python escapes them to `\\u2265`, and
    `jsonfmt` leaves whatever it finds alone. (`jq` does not — it unescapes, which is why
    editing this file with `jq` introduces a diff that comes straight back.)
    """
    return json.dumps(lock, indent=2, sort_keys=True) + "\n"


def fetch_catalog(refresh: bool = False) -> dict[str, list[dict[str, Any]]]:
    """The catalogue, from disk unless asked for a fresh copy."""
    if CACHE.exists() and not refresh:
        return json.loads(CACHE.read_text(encoding="utf-8"))

    log.info("downloading %s", CATALOG_URL)
    with urllib.request.urlopen(CATALOG_URL) as response:
        blob = response.read()

    # The Addon Manager verifies the companion .sha256 before trusting the zip, so this
    # does too: it is the only integrity signal the endpoint offers.
    try:
        with urllib.request.urlopen(CATALOG_URL + ".sha256") as response:
            want = response.read().decode().split()[0].strip()
        got = hashlib.sha256(blob).hexdigest()
        if want != got:
            raise SystemExit(f"catalogue sha256 mismatch: want {want}, got {got}")
        log.info("sha256 verified")
    except urllib.error.URLError as exc:
        log.warning("could not fetch the catalogue's .sha256 (%s), continuing", exc)

    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        data = json.loads(archive.read("addon_catalog_cache.json"))

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return data


def package_xml(entry: dict[str, Any]) -> ET.Element | None:
    raw = (entry.get("metadata") or {}).get("package_xml")
    if not raw:
        return None
    try:
        return ET.fromstring(raw)
    except ET.ParseError:
        return None


def describe(name: str, entry: dict[str, Any]) -> dict[str, Any]:
    """Everything worth knowing about one catalogue entry, flattened."""
    root = package_xml(entry)

    def text(tag: str) -> str:
        # `if root:` would be the bug the DeprecationWarning warns about: an Element with
        # no children is falsy today and truthy in a future Python.
        if root is None:
            return ""
        return (root.findtext("{*}" + tag) or "").strip()

    kinds: list[str] = []
    if root is not None:
        content = root.find("{*}content")
        if content is not None:
            kinds = sorted({child.tag.split("}")[-1] for child in content})

    licence = text("license") or None
    spdx = None
    if licence:
        key = licence.lower().strip()
        spdx = BY_LOWER.get(key) or SPDX.get(key)

    age = None
    stamp = entry.get("last_update_time") or ""
    try:
        when = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if when.tzinfo is None:
            when = when.replace(tzinfo=dt.timezone.utc)
        age = (dt.datetime.now(dt.timezone.utc) - when).days
    except ValueError:
        pass

    return {
        "name": name,
        "repository": entry.get("repository"),
        "rev": entry.get("git_hash"),
        "ref": entry.get("git_ref"),
        "tag": entry.get("git_tag") or None,
        "version": text("version") or None,
        "description": text("description") or None,
        "homepage": text("url") or entry.get("repository"),
        "license": licence,
        "spdx": spdx,
        "content": kinds,
        "age_days": age,
    }


def entries(catalog: dict[str, list[dict[str, Any]]], name: str) -> dict[str, Any]:
    """The entry to package for `name`.

    Thirteen of the 173 offer more than one branch — twelve offer two and one offers
    four, a `main` beside a `development`, say. **The first is taken, always**, which is
    the order the catalogue itself lists them in. Nothing here reads the branch names or
    prefers a stable one; that ordering is upstream's, and this does not second-guess it.

    Of what this repo locks, exactly one is affected: `FreeCAD-Ribbon` offers `main` and
    `Develop`, and gets `main`. That is the right answer, but it is the right answer by
    upstream's ordering rather than by a decision made here — so if a catalogue entry ever
    leads with a development branch, this takes it silently. `nix/addons.json` records the
    `ref` of whatever was chosen, which is where you would notice.
    """
    found = catalog.get(name)
    if not found:
        raise SystemExit(f"no addon called {name!r} in the catalogue")
    return found[0]


def cmd_list(args: argparse.Namespace) -> int:
    catalog = fetch_catalog(args.refresh)
    rows = [describe(n, entries(catalog, n)) for n in sorted(catalog)]

    if args.content:
        rows = [r for r in rows if args.content in r["content"]]
    if args.search:
        needle = args.search.lower()
        rows = [
            r
            for r in rows
            if needle in r["name"].lower() or needle in (r["description"] or "").lower()
        ]

    if args.json:
        print(json.dumps(rows, indent=2))
        return 0

    print(f"{'addon':<34} {'version':<12} {'licence':<22} {'idle':>6}  content")
    print("-" * 100)
    for r in rows:
        age = f"{r['age_days']}d" if r["age_days"] is not None else "?"
        # A licence we could not resolve is the interesting case, so it is marked.
        lic = r["spdx"] or (f"?{r['license']}" if r["license"] else "?none")
        print(
            f"{r['name']:<34} {(r['version'] or '-'):<12} {lic:<22} {age:>6}  "
            f"{','.join(r['content']) or '-'}"
        )
    print(f"\n{len(rows)} addons")

    unresolved = [r for r in rows if not r["spdx"]]
    ancient = [r for r in rows if (r["age_days"] or 0) > 730]
    if unresolved:
        print(f"  {len(unresolved)} with a licence this cannot resolve (marked ?)")
    if ancient:
        print(
            f"  {len(ancient)} untouched upstream for over two years — a warning, not a verdict"
        )
    return 0


def prefetch(repository: str, rev: str) -> str:
    """The SRI hash of a repository at a revision. The one thing the catalogue lacks."""
    log.info("prefetching %s@%s", repository, rev[:12])
    proc = subprocess.run(
        [
            "nix-prefetch-git",
            "--url",
            repository,
            "--rev",
            rev,
            "--quiet",
            "--no-add-path",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return str(json.loads(proc.stdout)["hash"])


def cmd_add(args: argparse.Namespace) -> int:
    catalog = fetch_catalog(args.refresh)
    lock: dict[str, Any] = (
        json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {}
    )

    for name in args.name:
        info = describe(name, entries(catalog, name))
        if not info["rev"]:
            raise SystemExit(f"{name}: the catalogue has no git_hash for it")
        info["hash"] = prefetch(info["repository"], info["rev"])
        info.pop("age_days")  # a measurement, not a fact about the package
        lock[name] = info
        if not info["spdx"]:
            log.warning(
                "%s declares its licence as %r, which is not an SPDX id. "
                "Say what it is where the addon is packaged.",
                name,
                info["license"],
            )

    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(write_lock(lock), encoding="utf-8")
    print(f"wrote {LOCK} ({len(lock)} addons)")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    """Move every locked addon to whatever the catalogue now pins."""
    if not LOCK.exists():
        raise SystemExit(f"{LOCK} does not exist yet; add an addon first")
    catalog = fetch_catalog(refresh=True)
    lock: dict[str, Any] = json.loads(LOCK.read_text(encoding="utf-8"))

    moved = []
    for name, was in sorted(lock.items()):
        if args.name and name not in args.name:
            continue
        info = describe(name, entries(catalog, name))
        if info["rev"] == was.get("rev"):
            continue
        info["hash"] = prefetch(info["repository"], info["rev"])
        info.pop("age_days")
        # A licence resolved by hand is a decision; do not silently undo it.
        if was.get("spdx") and not info["spdx"]:
            info["spdx"] = was["spdx"]
        lock[name] = info
        moved.append(f"{name}: {was.get('version')} -> {info['version']}")

    if not moved:
        print("nothing moved")
        return 0
    LOCK.write_text(write_lock(lock), encoding="utf-8")
    for line in moved:
        print(f"  {line}")
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--refresh", action="store_true", help="re-download the catalogue")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ls = sub.add_parser("list", help="what the catalogue offers")
    ls.add_argument("--content", help="workbench, preferencepack, macro, other")
    ls.add_argument("--search")
    ls.add_argument("--json", action="store_true")
    ls.set_defaults(func=cmd_list)

    add = sub.add_parser("add", help="lock an addon at what the catalogue pins")
    add.add_argument("name", nargs="+")
    add.set_defaults(func=cmd_add)

    up = sub.add_parser(
        "update", help="move locked addons to the catalogue's current pin"
    )
    up.add_argument("name", nargs="*")
    up.set_defaults(func=cmd_update)

    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
