"""Shared bits for the update scripts.

Deliberately small, and deliberately not tied to any CI: `write_output` degrades to a log
line when `GITHUB_OUTPUT` is unset, so the same scripts run under a workflow, under a
self-hosted runner, or by hand in a terminal.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]


def run(
    cmd: list[str],
    *,
    check: bool = True,
    capture: bool = False,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command from the repository root unless told otherwise."""
    log.debug("running %s", " ".join(cmd))
    return subprocess.run(
        cmd, capture_output=capture, text=True, check=check, cwd=cwd or ROOT
    )


def write_output(key: str, value: str) -> None:
    """A key=value pair for GitHub Actions, or a log line anywhere else."""
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with Path(target).open("a", encoding="utf-8") as handle:
            handle.write(f"{key}={value}\n")
    else:
        log.info("output: %s=%s", key, value)


def tree_state() -> str:
    """A comparable snapshot of the work tree.

    Not "is the tree dirty": a CI job may have staged something before calling, and a
    caller that reports `changed=true` because of *that* is worse than useless — it opens
    a pull request for a target that did not move. Compare this before and after instead.
    """
    status = run(["git", "status", "--porcelain"], capture=True).stdout
    diff = run(
        ["git", "diff", "--no-ext-diff", "--no-textconv", "--binary", "HEAD"],
        capture=True,
    ).stdout
    untracked = run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"], capture=True
    ).stdout
    contents = []
    for name in sorted(filter(None, untracked.split("\0"))):
        path = ROOT / name
        data = (
            os.fsencode(os.readlink(path)) if path.is_symlink() else path.read_bytes()
        )
        contents.append((name, path.lstat().st_mode, hashlib.sha256(data).hexdigest()))
    return json.dumps((status, diff, contents))
