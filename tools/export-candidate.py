#!/usr/bin/env python3
"""Copy an athens build into an independently stored, consistently named candidate.

Usage: export-pixelos-candidate.py built.zip artifact-directory --revision r11
The archive contents and signatures are preserved; no additional hashes are computed.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('directory', type=Path)
parser.add_argument('--revision', required=True)
args = parser.parse_args()
match = re.fullmatch(r'PixelOS_athens-(\d+\.\d+)-.+\.zip', args.source.name)
if not match or not re.fullmatch(r'r[1-9][0-9]*', args.revision):
    parser.error('Expected PixelOS_athens-VERSION-*.zip and revision rN.')
with zipfile.ZipFile(args.source) as archive:
    metadata = dict(line.split('=', 1) for line in
                    archive.read('META-INF/com/android/metadata').decode().splitlines()
                    if '=' in line)
if metadata.get('pre-device') != 'athens' or metadata.get('ota-type') != 'AB':
    parser.error('Expected an athens A/B OTA.')
stamp = datetime.fromtimestamp(int(metadata['post-timestamp']), timezone.utc)
name = f'PixelOS_athens-{match[1]}-UNOFFICIAL-{stamp:%Y%m%d-%H%M}UTC-{args.revision}.zip'
args.directory.mkdir(parents=True, exist_ok=True)
target = args.directory / name
with args.source.open('rb') as source, target.open('xb') as dest:
    shutil.copyfileobj(source, dest, length=8 * 1024 * 1024)
print(json.dumps({'artifact': str(target.resolve()), 'size': target.stat().st_size,
                  'incremental': metadata['post-build-incremental'],
                  'build_time_utc': stamp.isoformat()}, indent=2))
