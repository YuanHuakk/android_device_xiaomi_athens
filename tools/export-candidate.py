#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Export an independent athens OTA copy named by its build timestamp."""

import argparse
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

OTA_METADATA = "META-INF/com/android/metadata"


def export_candidate(
    source: Path, directory: Path, revision: str
) -> dict[str, str | int]:
    version = re.fullmatch(r"PixelOS_athens-(\d+\.\d+)-.+\.zip", source.name)
    if not version or not re.fullmatch(r"r[1-9][0-9]*", revision):
        raise ValueError("Expected PixelOS_athens-VERSION-*.zip and revision rN.")

    with zipfile.ZipFile(source) as archive:
        metadata = dict(
            line.split("=", 1)
            for line in archive.read(OTA_METADATA).decode().splitlines()
            if "=" in line
        )
    if metadata.get("pre-device") != "athens" or metadata.get("ota-type") != "AB":
        raise ValueError("Expected an athens A/B OTA.")

    timestamp = datetime.fromtimestamp(int(metadata["post-timestamp"]), timezone.utc)
    name = (
        f"PixelOS_athens-{version[1]}-UNOFFICIAL-"
        f"{timestamp:%Y%m%d-%H%M}UTC-{revision}.zip"
    )
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    # Copy rather than hard-link: build outputs may be overwritten in place.
    with source.open("rb") as original, target.open("xb") as exported:
        shutil.copyfileobj(original, exported, length=8 * 1024 * 1024)
    return {
        "artifact": str(target.resolve()),
        "size": target.stat().st_size,
        "incremental": metadata["post-build-incremental"],
        "build_time_utc": timestamp.isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    try:
        result = export_candidate(args.source, args.directory, args.revision)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
