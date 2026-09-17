from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import lib
import weekly


class ReleaseTests(unittest.TestCase):
    def test_dated_prereleases_are_selected_by_date(self) -> None:
        releases = [
            {"tag_name": "1.1.3"},
            {"tag_name": "weekly-builds"},
            {"tag_name": "weekly-2026.09.16", "prerelease": True},
            {"tag_name": "weekly-2026.09.17", "draft": True},
            {"tag_name": "weekly-2026.09.09"},
        ]
        self.assertEqual(weekly.latest_weekly(releases), "2026.09.16")

    def test_missing_weekly_fails_instead_of_selecting_stable(self) -> None:
        with self.assertRaises(RuntimeError):
            weekly.latest_weekly([{"tag_name": "1.1.3"}])

    def test_invalid_date_fails(self) -> None:
        with self.assertRaises(ValueError):
            weekly.latest_weekly([{"tag_name": "weekly-2026.02.30"}])

    def test_recipe_changes_require_a_build(self) -> None:
        old = {"version": "2026.09.16", "base_revision": "old"}
        self.assertFalse(weekly.needs_build(old, dict(old)))
        self.assertTrue(weekly.needs_build(old, dict(old, base_revision="new")))

    def test_downgrade_is_refused(self) -> None:
        with self.assertRaises(RuntimeError):
            weekly.needs_build({"version": "2026.09.16"}, {"version": "2026.09.09"})


class PublicationTests(unittest.TestCase):
    """Real Git pushes to a local bare repository; compilation and cache are mocked."""

    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "checkout"
        self.root.mkdir()
        self.remote = Path(temp.name) / "origin.git"
        self.env = {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GITHUB_ACTIONS": "true",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_DEFAULT_BRANCH": "main",
            "WEEKLY_SYSTEM": "x86_64-linux",
            "WEEKLY_CACHE_URI": "s3://test.invalid",
            "NIX_SIGNING_KEY": "test-only",
            "GITHUB_STEP_SUMMARY": "",
            "GITHUB_OUTPUT": "",
        }
        self.enterContext(patch.dict(os.environ, self.env))
        self.enterContext(patch.object(lib, "ROOT", self.root))
        self.enterContext(patch.object(weekly, "ROOT", self.root))
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        package = self.root / weekly.PACKAGE
        package.parent.mkdir(parents=True)
        package.write_text("initial pin\n")
        (self.root / "flake.lock").write_text("unchanged lock\n")
        self.git("add", ".")
        self.git("commit", "-qm", "initial")
        self.base = self.git("rev-parse", "HEAD")
        self.git("init", "-q", "--bare", str(self.remote))
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "-q", "origin", "main")
        self.pin = self.enterContext(
            patch.object(
                weekly,
                "pin_version",
                side_effect=lambda v: package.write_text(v + "\n"),
            )
        )
        self.build = self.enterContext(
            patch.object(weekly, "build_candidate", return_value=["/nix/store/test"])
        )
        self.cache = self.enterContext(patch.object(weekly, "upload_cache"))

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=self.root, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()

    def retry_checkout(self) -> None:
        self.git("checkout", "--detach", self.base)

    def tag(self, version: str = "2026.09.16") -> str:
        return f"refs/tags/weekly-{version}-x86_64-linux-{self.base[:12]}"

    def test_publish_uploads_before_push_and_preserves_default_branch(self) -> None:
        def cache(*args: object) -> None:
            self.assertEqual(weekly.remote_ref(weekly.CHANNEL), "")

        self.cache.side_effect = cache
        weekly.publish("2026.09.16")
        candidate = self.git("rev-parse", "HEAD")
        self.assertEqual(weekly.remote_ref(weekly.CHANNEL), candidate)
        self.assertEqual(weekly.remote_ref(self.tag()), candidate)
        self.assertEqual(weekly.remote_ref("refs/heads/main"), self.base)
        self.assertEqual((self.root / "flake.lock").read_text(), "unchanged lock\n")
        self.assertEqual(
            set(self.git("diff", "--name-only", self.base, candidate).splitlines()),
            {weekly.PACKAGE, weekly.STATE},
        )

    def test_already_published_is_a_noop(self) -> None:
        weekly.publish("2026.09.16")
        self.retry_checkout()
        weekly.publish("2026.09.16")
        self.assertEqual(self.build.call_count, 1)
        self.assertEqual(self.cache.call_count, 1)
        self.assertEqual(self.git("rev-parse", "HEAD"), self.base)

    def test_failed_build_keeps_last_weekly_and_skips_cache(self) -> None:
        weekly.publish("2026.09.16")
        previous = weekly.remote_ref(weekly.CHANNEL)
        self.retry_checkout()
        self.build.side_effect = RuntimeError("compilation failed")
        self.cache.reset_mock()
        with self.assertRaisesRegex(RuntimeError, "compilation failed"):
            weekly.publish("2026.09.23")
        self.assertEqual(weekly.remote_ref(weekly.CHANNEL), previous)
        self.assertEqual(weekly.remote_ref(self.tag("2026.09.23")), "")
        self.cache.assert_not_called()

    def test_failed_upload_does_not_publish(self) -> None:
        self.cache.side_effect = RuntimeError("cache unavailable")
        with self.assertRaisesRegex(RuntimeError, "cache unavailable"):
            weekly.publish("2026.09.16")
        self.assertEqual(weekly.remote_ref(weekly.CHANNEL), "")
        self.assertEqual(weekly.remote_ref(self.tag()), "")

    def test_concurrent_channel_change_rejects_both_refs(self) -> None:
        self.cache.side_effect = lambda *args: self.git(
            "push", "origin", f"{self.base}:{weekly.CHANNEL}"
        )
        with self.assertRaises(subprocess.CalledProcessError):
            weekly.publish("2026.09.16")
        self.assertEqual(weekly.remote_ref(weekly.CHANNEL), self.base)
        self.assertEqual(weekly.remote_ref(self.tag()), "")

    def test_immutable_tag_conflict_does_not_move_channel(self) -> None:
        self.git("push", "origin", f"{self.base}:{self.tag()}")
        with self.assertRaises(subprocess.CalledProcessError):
            weekly.publish("2026.09.16")
        self.assertEqual(weekly.remote_ref(weekly.CHANNEL), "")
        self.assertEqual(weekly.remote_ref(self.tag()), self.base)

    def test_default_branch_advancing_aborts_publication(self) -> None:
        self.cache.side_effect = lambda *args: self.git("push", "origin", "HEAD:main")
        with self.assertRaisesRegex(RuntimeError, "default branch advanced"):
            weekly.publish("2026.09.16")
        self.assertEqual(weekly.remote_ref(weekly.CHANNEL), "")

    def test_existing_unmanaged_weekly_is_not_overwritten(self) -> None:
        self.git("push", "origin", f"{self.base}:{weekly.CHANNEL}")
        with self.assertRaises(subprocess.CalledProcessError):
            weekly.publish("2026.09.16")
        self.pin.assert_not_called()
        self.assertEqual(weekly.remote_ref(weekly.CHANNEL), self.base)

    def test_missing_cache_configuration_fails_before_updating(self) -> None:
        with (
            patch.dict(os.environ, {"WEEKLY_CACHE_URI": ""}),
            self.assertRaisesRegex(RuntimeError, "Configure WEEKLY_CACHE_URI"),
        ):
            weekly.publish("2026.09.16")
        self.pin.assert_not_called()

    def test_local_or_nondefault_invocation_is_refused(self) -> None:
        for env in ({"GITHUB_ACTIONS": "false"}, {"GITHUB_REF": "refs/heads/weekly"}):
            with (
                self.subTest(env=env),
                patch.dict(os.environ, env),
                self.assertRaisesRegex(RuntimeError, "restricted to Actions"),
            ):
                weekly.publish("2026.09.16")
        self.pin.assert_not_called()

    def test_dirty_checkout_is_preserved(self) -> None:
        dirty = self.root / "notes"
        dirty.write_text("user work")
        with self.assertRaisesRegex(RuntimeError, "clean, disposable checkout"):
            weekly.publish("2026.09.16")
        self.assertEqual(dirty.read_text(), "user work")
        self.pin.assert_not_called()


class CacheTests(unittest.TestCase):
    def test_private_key_is_removed_after_upload_failure(self) -> None:
        key_paths = []

        def run(cmd: list[str]) -> None:
            if cmd[:3] == ["nix", "store", "sign"]:
                path = Path(cmd[cmd.index("--key-file") + 1])
                key_paths.append(path)
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                self.assertEqual(path.read_text(), "test-key\n")
            else:
                raise RuntimeError("copy failed")

        with (
            patch.object(weekly, "run", side_effect=run),
            self.assertRaisesRegex(RuntimeError, "copy failed"),
        ):
            weekly.upload_cache(["/nix/store/test"], "s3://test", "test-key")
        self.assertEqual(len(key_paths), 1)
        self.assertFalse(key_paths[0].exists())


if __name__ == "__main__":
    unittest.main()
