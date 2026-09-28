# SPDX-License-Identifier: Apache-2.0
"""Tests for release export and multi-project patch application."""

import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


exporter = load_tool("export-candidate")
patcher = load_tool("apply-patches")


class ExportTest(unittest.TestCase):
    def test_export_is_independent_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "PixelOS_athens-17.0-test.zip"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(
                    exporter.OTA_METADATA,
                    "pre-device=athens\nota-type=AB\n"
                    "post-timestamp=1790614675\npost-build-incremental=1790614675\n",
                )
            original = source.read_bytes()
            result = exporter.export_candidate(source, root / "releases", "r12")
            target = Path(result["artifact"])
            self.assertEqual(
                target.name, "PixelOS_athens-17.0-UNOFFICIAL-20260928-1657UTC-r12.zip"
            )
            self.assertEqual(target.read_bytes(), original)
            with self.assertRaises(FileExistsError):
                exporter.export_candidate(source, root / "releases", "r12")
            source.write_bytes(b"next build")
            self.assertEqual(target.read_bytes(), original)

    def test_wrong_device_does_not_create_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "PixelOS_athens-17.0-test.zip"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(
                    exporter.OTA_METADATA, "pre-device=other\nota-type=AB\n"
                )
            with self.assertRaisesRegex(ValueError, "athens A/B"):
                exporter.export_candidate(source, root / "releases", "r12")
            self.assertFalse((root / "releases").exists())


class PatchSeriesTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.series = self.root / "series.json"

    def create_project(self, name):
        project = self.root / name
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        source = project / "value.txt"
        source.write_text("original\n")
        subprocess.run(["git", "add", "."], cwd=project, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-qm",
                "Initial version",
            ],
            cwd=project,
            check=True,
        )
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=project, text=True
        ).strip()
        source.write_text("patched\n")
        patch = self.root / f"{name}.patch"
        patch.write_bytes(subprocess.check_output(["git", "diff"], cwd=project))
        source.write_text("original\n")
        return {"project": name, "base_commit": revision, "patch": patch.name}

    def test_check_and_repeated_application(self):
        self.series.write_text(json.dumps([self.create_project("first")]))
        source = self.root / "first/value.txt"
        with contextlib.redirect_stdout(io.StringIO()):
            patcher.apply_patches(self.root, self.series, check_only=True)
            self.assertEqual(source.read_text(), "original\n")
            patcher.apply_patches(self.root, self.series)
            patcher.apply_patches(self.root, self.series)
        self.assertEqual(source.read_text(), "patched\n")

    def test_invalid_later_project_does_not_modify_earlier_project(self):
        first = self.create_project("first")
        second = self.create_project("second")
        second["base_commit"] = "0" * 40
        self.series.write_text(json.dumps([first, second]))
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "Wrong baseline: second"):
                patcher.apply_patches(self.root, self.series)
        self.assertEqual((self.root / "first/value.txt").read_text(), "original\n")


if __name__ == "__main__":
    unittest.main()
