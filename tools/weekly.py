#!/usr/bin/env python3
"""Publish a tested weekly channel; without --publish, only query upstream releases.

The publisher runs in a disposable checkout on the default branch. It never merges
into that branch. Cache upload and all tests must finish before a single atomic push
makes the candidate available as both a rolling branch and an immutable tag.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import ROOT, run, write_output

PACKAGE = "nix/packages/freecad-weekly/default.nix"
STATE = ".weekly.json"
CHANNEL = "refs/heads/weekly"
log = logging.getLogger("weekly")


def latest_weekly(releases: list[dict[str, Any]]) -> str:
    versions = []
    for release in releases:
        match = re.fullmatch(r"weekly-(\d{4}\.\d{2}\.\d{2})", release["tag_name"])
        if match and not release.get("draft", False):
            version = match[1]
            date.fromisoformat(version.replace(".", "-"))
            versions.append(version)
    if not versions:
        raise RuntimeError("No dated FreeCAD weekly release found; refusing a fallback")
    return max(versions)


def upstream_version() -> str:
    # /latest excludes prereleases, which is how FreeCAD publishes its weeklies.
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "freecad.nix"}
    if token := os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    request = Request(
        "https://api.github.com/repos/FreeCAD/FreeCAD/releases?per_page=100",
        headers=headers,
    )
    with urlopen(request, timeout=60) as response:
        return latest_weekly(json.load(response))


def git(*args: str) -> str:
    return run(["git", *args], capture=True).stdout.strip()


def remote_ref(ref: str) -> str:
    result = git("ls-remote", "--refs", "origin", ref)
    return result.split()[0] if result else ""


def clean_checkout() -> None:
    if git("status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("Weekly publication requires a clean, disposable checkout")


def channel_state() -> tuple[str, dict[str, Any]]:
    previous = remote_ref(CHANNEL)
    if not previous:
        return "", {}
    git("fetch", "--no-tags", "origin", CHANNEL)
    if git("rev-parse", "FETCH_HEAD") != previous:
        raise RuntimeError("The weekly channel changed during discovery; retry")
    # An existing branch without our marker belongs to someone else; do not take it.
    return previous, json.loads(git("show", f"{previous}:{STATE}"))


def needs_build(previous: dict[str, Any], candidate: dict[str, str]) -> bool:
    if previous and previous["version"] > candidate["version"]:
        raise RuntimeError(
            "Upstream appears older than the channel; refusing downgrade"
        )
    return previous != candidate


def pin_version(version: str) -> None:
    run(
        [
            "nix-update",
            "--flake",
            "freecad-weekly",
            "--version",
            version,
            "--src-only",
            "--override-filename",
            str(ROOT / PACKAGE),
        ]
    )
    changed = set(git("diff", "--name-only", "HEAD").splitlines())
    if changed - {PACKAGE} or git("ls-files", "--others", "--exclude-standard"):
        raise RuntimeError("The weekly update changed files outside its package pin")
    actual = run(
        ["nix", "eval", "--no-update-lock-file", "--raw", ".#freecad-weekly.version"],
        capture=True,
    ).stdout
    if actual != version:
        raise RuntimeError(f"Requested weekly {version}, but Nix evaluates {actual}")


def commit_candidate(state: dict[str, str]) -> str:
    (ROOT / STATE).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    git("add", "--", PACKAGE, STATE)
    git(
        "-c",
        "user.name=github-actions[bot]",
        "-c",
        "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-m",
        f"freecad-weekly: {state['version']}",
    )
    return git("rev-parse", "HEAD")


def build_candidate(system: str) -> list[str]:
    native = run(
        ["nix", "eval", "--impure", "--raw", "--expr", "builtins.currentSystem"],
        capture=True,
    ).stdout
    if native != system:
        raise RuntimeError(f"Expected a native {system} runner, got {native}")
    checks = [
        "weekly-patches",
        "tools-python",
        "readme-current",
        "pkgs-formatter-check",
    ]
    run(
        ["nix", "build", "--no-update-lock-file", "--no-link", "-L"]
        + [f".#checks.{system}.{check}" for check in checks]
    )
    # Discover passthru tests so a new upstream test cannot be silently omitted.
    test_names = json.loads(
        run(
            [
                "nix",
                "eval",
                "--no-update-lock-file",
                "--json",
                f".#packages.{system}.freecad-weekly.tests",
                "--apply",
                "builtins.attrNames",
            ],
            capture=True,
        ).stdout
    )
    if not {"modules", "python-path"}.issubset(test_names):
        raise RuntimeError("Expected FreeCAD runtime tests have disappeared")
    result = subprocess.run(
        ["nix", "build", "--no-update-lock-file", "--no-link", "--json", "-L"]
        + [f".#packages.{system}.freecad-weekly^*"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    run(
        ["nix", "build", "--no-update-lock-file", "--no-link", "-L"]
        + [f".#checks.{system}.pkgs-freecad-weekly-{test}" for test in test_names]
    )
    # Publish every package output (including the launcher), not the test markers.
    builds = json.loads(result.stdout)
    outputs = sorted(builds[0]["outputs"].values())
    if not outputs or any(not path.startswith("/nix/store/") for path in outputs):
        raise RuntimeError("The build returned no FreeCAD store paths")
    return outputs


def upload_cache(outputs: list[str], uri: str, signing_key: str) -> None:
    # NamedTemporaryFile is mode 0600 and removed even when signing/copying fails.
    with tempfile.NamedTemporaryFile(mode="w", prefix="weekly-key-") as key:
        key.write(signing_key.strip() + "\n")
        key.flush()
        run(["nix", "store", "sign", "--recursive", "--key-file", key.name, *outputs])
        run(["nix", "copy", "--to", uri, *outputs])


def publish_refs(candidate: str, state: dict[str, str], previous: str) -> str:
    clean_checkout()
    if git("rev-parse", "HEAD") != candidate:
        raise RuntimeError("HEAD changed after validation")
    if remote_ref(f"refs/heads/{state['default_branch']}") != state["base_revision"]:
        raise RuntimeError("The default branch advanced during the build; retry")
    tag = f"weekly-{state['version']}-{state['system']}-{state['base_revision'][:12]}"
    # The lease also guards branch creation: an empty expected value requires absence.
    # Tags are never forced. --atomic prevents either ref moving on a rejected push.
    git(
        "push",
        "--atomic",
        f"--force-with-lease={CHANNEL}:{previous}",
        "origin",
        f"{candidate}:{CHANNEL}",
        f"{candidate}:refs/tags/{tag}",
    )
    return tag


def publish(version: str) -> None:
    branch = os.environ.get("GITHUB_DEFAULT_BRANCH", "")
    if (
        os.environ.get("GITHUB_ACTIONS") != "true"
        or not branch
        or branch == "weekly"
        or os.environ.get("GITHUB_REF") != f"refs/heads/{branch}"
    ):
        raise RuntimeError("--publish is restricted to Actions on the default branch")
    clean_checkout()
    base = git("rev-parse", "HEAD")
    if remote_ref(f"refs/heads/{branch}") != base:
        raise RuntimeError("Checkout is not the current default branch; retry")
    system = os.environ.get("WEEKLY_SYSTEM", "x86_64-linux")
    if system not in {"x86_64-linux", "aarch64-linux"}:
        raise RuntimeError(f"Unsupported system: {system}")
    state = {
        "version": version,
        "base_revision": base,
        "default_branch": branch,
        "system": system,
    }
    previous, old_state = channel_state()
    if not needs_build(old_state, state):
        log.info("Weekly %s is already published from this recipe", version)
        write_output("changed", "false")
        return
    uri = os.environ.get("WEEKLY_CACHE_URI", "")
    key = os.environ.get("NIX_SIGNING_KEY", "")
    if not uri or not key:
        raise RuntimeError(
            "Configure WEEKLY_CACHE_URI and NIX_SIGNING_KEY before publishing"
        )
    pin_version(version)
    candidate = commit_candidate(state)
    outputs = build_candidate(system)
    upload_cache(outputs, uri, key)
    tag = publish_refs(candidate, state, previous)
    write_output("changed", "true")
    write_output("tag", tag)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(summary).open("a", encoding="utf-8") as handle:
            handle.write(
                f"Published **FreeCAD {version}** for `{system}`.\n\n"
                f"Commit: `{candidate}`; immutable tag: `{tag}`.\n\n"
                "Compilation, runtime tests and binary cache upload passed.\n\n"
                + "\n".join(f"- `{path}`" for path in outputs)
                + "\n"
            )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--publish", action="store_true", help="update the CI-only channel"
    )
    args = parser.parse_args()
    version = upstream_version()
    print(f"Latest upstream weekly: {version}", flush=True)
    if args.publish:
        publish(version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
