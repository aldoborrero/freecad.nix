from __future__ import annotations

import contextlib
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import check_patches
import lib
import update


class PatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.diff = self.root / "change.patch"
        self.diff.write_text("--- a/file\n+++ b/file\n@@ -1 +1 @@\n-old\n+new\n")

    def check(self) -> int:
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            return check_patches.check(self.source, [self.diff], {})

    def test_missing_target_fails(self) -> None:
        self.assertEqual(self.check(), 1)

    def test_malformed_patch_fails(self) -> None:
        self.diff.write_text("not a patch\n")
        self.assertEqual(self.check(), 1)

    def test_missing_patch_fails(self) -> None:
        self.diff.unlink()
        self.assertEqual(self.check(), 1)

    def test_rejected_hunk_fails(self) -> None:
        (self.source / "file").write_text("different\n")
        self.assertEqual(self.check(), 1)

    def test_relative_path_applies_without_changing_source(self) -> None:
        (self.source / "file").write_text("old\n")
        self.diff = Path(os.path.relpath(self.diff))
        self.assertEqual(self.check(), 0)
        self.assertEqual((self.source / "file").read_text(), "old\n")


class UpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        root_patch = patch.object(lib, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)
        git_env = patch.dict(
            os.environ, {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        )
        git_env.start()
        self.addCleanup(git_env.stop)
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.file = self.root / "package.nix"
        self.file.write_text("initial\n")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")

    def git(self, *args: str) -> str:
        return subprocess.check_output(["git", "-C", str(self.root), *args], text=True)

    def test_already_dirty_content_changes_are_detected(self) -> None:
        self.file.write_text("first\n")
        before = lib.tree_state()
        self.assertEqual(before, lib.tree_state())
        self.file.write_text("second\n")
        self.assertNotEqual(before, lib.tree_state())

    def test_staged_content_changes_are_detected(self) -> None:
        self.file.write_text("first\n")
        self.git("add", ".")
        before = lib.tree_state()
        self.file.write_text("second\n")
        self.git("add", ".")
        self.assertNotEqual(before, lib.tree_state())

    def test_untracked_content_changes_are_detected(self) -> None:
        other = self.root / "new.nix"
        other.write_text("first\n")
        before = lib.tree_state()
        other.write_text("second\n")
        self.assertNotEqual(before, lib.tree_state())

    def test_update_regenerates_readme_only_on_change(self) -> None:
        self.file.write_text("already dirty\n")
        for changed in (True, False):
            with self.subTest(changed=changed):

                def apply(entry: dict[str, str], changed: bool = changed) -> None:
                    if changed:
                        self.file.write_text("updated\n")

                def run(
                    cmd: list[str], **kwargs: object
                ) -> subprocess.CompletedProcess[str]:
                    if cmd[:2] == ["nix", "run"]:
                        (self.root / "README.md").write_text("updated metadata\n")
                        return subprocess.CompletedProcess(cmd, 0, "", "")
                    return lib.run(cmd, **kwargs)

                with (
                    patch.object(update, "apply", side_effect=apply),
                    patch.object(update, "run", side_effect=run) as runner,
                    patch.object(update, "write_output") as output,
                    patch(
                        "sys.argv", ["update.py", "--kind", "catalog", "--name", "test"]
                    ),
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    self.assertEqual(update.main(), 0)
                regenerations = [
                    c for c in runner.call_args_list if c.args[0][:2] == ["nix", "run"]
                ]
                self.assertEqual(len(regenerations), int(changed))
                output.assert_any_call("changed", "true" if changed else "false")


if __name__ == "__main__":
    unittest.main()
