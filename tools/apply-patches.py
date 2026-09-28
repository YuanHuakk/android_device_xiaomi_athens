#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Apply device patches to their pinned upstream revisions."""

import argparse
import json
import subprocess
from pathlib import Path


def apply_patches(tree: Path, series_path: Path, check_only: bool = False) -> None:
    pending = []
    for entry in json.loads(series_path.read_text()):
        project = tree / entry["project"]
        patch = series_path.parent / entry["patch"]
        head = subprocess.check_output(
            ["git", "-C", str(project), "rev-parse", "HEAD"], text=True
        ).strip()
        if head != entry["base_commit"]:
            raise ValueError(
                f"Wrong baseline: {entry['project']} "
                f"(expected {entry['base_commit']}, got {head})"
            )

        command = ["git", "-C", str(project), "apply", "--check"]
        forward = subprocess.run([*command, str(patch)], capture_output=True, text=True)
        if forward.returncode == 0:
            pending.append((project, patch))
            print(f"ready: {entry['project']}")
            continue

        reverse = subprocess.run(
            [*command, "--reverse", str(patch)], capture_output=True
        )
        if reverse.returncode != 0:
            raise ValueError(f"Cannot apply {entry['project']}:\n{forward.stderr}")
        print(f"already applied: {entry['project']}")

    # Validate the whole series before changing any project.
    if check_only:
        return
    for project, patch in pending:
        subprocess.run(["git", "-C", str(project), "apply", str(patch)], check=True)
    print(f"Applied {len(pending)} project patches.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--check", action="store_true", help="Check without applying")
    args = parser.parse_args()
    series_path = Path(__file__).resolve().parents[1] / "patches/series.json"
    try:
        apply_patches(args.tree.resolve(), series_path, args.check)
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
