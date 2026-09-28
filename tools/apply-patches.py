#!/usr/bin/env python3
"""Apply the r12 source changes to their pinned upstream revisions."""
import argparse
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--tree', required=True, type=Path)
parser.add_argument('--check', action='store_true', help='Inspect without changing files')
args = parser.parse_args()
patches = Path(__file__).resolve().parents[1] / 'patches'
pending = []
for entry in json.loads((patches / 'series.json').read_text()):
    project = args.tree.resolve() / entry['project']
    patch = patches / entry['patch']
    head = subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
    if head != entry['base_commit']:
        raise SystemExit(f"Wrong baseline: {entry['project']} (expected {entry['base_commit']}, got {head})")
    command = ['git', '-C', str(project), 'apply', '--check']
    forward = subprocess.run(command + [str(patch)], capture_output=True, text=True)
    if forward.returncode == 0:
        pending.append((project, patch))
        print(f"ready: {entry['project']}")
    elif subprocess.run(command + ['--reverse', str(patch)], capture_output=True).returncode == 0:
        print(f"already applied: {entry['project']}")
    else:
        raise SystemExit(f"Cannot apply {entry['project']}:\n{forward.stderr}")

# Check every project before modifying any of them. Never reset unrelated changes.
if not args.check:
    for project, patch in pending:
        subprocess.run(['git', '-C', str(project), 'apply', str(patch)], check=True)
    print(f'Applied {len(pending)} project patches.')
