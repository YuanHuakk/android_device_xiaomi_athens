#!/usr/bin/env python3
"""Prepare the locally supplied athens camera, preserving its binary resources.
Port two app compatibility patches from xiaomi-onyx-dev's camera tree and
keep the MIVI debug directory in app-internal storage.
"""
from pathlib import Path
import argparse
import atexit
import tempfile
import difflib
import subprocess
import zipfile

parser = argparse.ArgumentParser(description="Prepare athens stock camera 6.3.008710.8 for PixelOS")
parser.add_argument('--tree', required=True, type=Path, help='PixelOS source root')
parser.add_argument('--stock-apk', required=True, type=Path)
parser.add_argument('--build-tools', required=True, type=Path, help='Android SDK build-tools directory')
parser.add_argument('--key', required=True, type=Path, help='Local platform signing key (.pk8)')
parser.add_argument('--cert', required=True, type=Path, help='Matching platform certificate (.x509.pem)')
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
TREE = args.tree.resolve()
JAVA = TREE / 'prebuilts/jdk/jdk21/linux-x86/bin/java'
SMALI = TREE / 'prebuilts/extract-tools/common/smali'
BT = args.build_tools.resolve()
STOCK = args.stock_apk.resolve()
OUTPUT = args.output.resolve()
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
_temp = tempfile.TemporaryDirectory(prefix='athens-camera-')
atexit.register(_temp.cleanup)
WORK = Path(_temp.name)


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def change(file, old, new):
    before = file.read_text()
    if before.count(old) != 1:
        raise ValueError(f'Expected exactly one known athens patch site: {file}')
    after = before.replace(old, new)
    patch = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=str(file.relative_to(WORK)), tofile=str(file.relative_to(WORK))))
    with (WORK / 'applied.patch').open('a') as f:
        f.write(patch)
    file.write_text(after)

(WORK / 'applied.patch').write_text('')
with zipfile.ZipFile(STOCK) as apk:
    for n in ['classes.dex', 'classes2.dex']:
        (WORK / n).write_bytes(apk.read(n))
        run(JAVA, '-Xmx2g', '-jar', SMALI / 'baksmali.jar', 'd', WORK / n, '-o', WORK / (n + '.smali'))

# The stock UI posts this message after the HyperOS/Leica integration check.
# Keep runtime camera/microphone permissions intact; remove only this dialog.
change(WORK / 'classes.dex.smali/com/android/camera/a$c.smali',
       '    const p1, 0x7f140bdd\n\n    invoke-static {p0, p1}, LD1/t3;->g(Landroid/app/Activity;I)V\n',
       '    # AOSP: omit the HyperOS-only limited-permissions dialog.\n')
# Select the existing Android permission flow, without changing system region.
change(WORK / 'classes2.dex.smali/id/c.smali',
       '    move-result v0\n\n    sput-boolean v0, Lid/c;->m:Z',
       '    const/4 v0, 0x1\n\n    sput-boolean v0, Lid/c;->m:Z')
# MIVI initializes this directory even when all image-dump flags are off.
# External storage may be unavailable; that must not break image-pool setup.
# This field is for debug dumps only, not the user's DCIM photo destination.
change(WORK / 'classes2.dex.smali/ff/e.smali',
       '.method static constructor <clinit>()V\n    .registers 2',
       '.method static constructor <clinit>()V\n    .registers 3')
change(WORK / 'classes2.dex.smali/ff/e.smali',
       '    invoke-virtual {v0, v1}, Landroid/content/Context;->getExternalFilesDir(Ljava/lang/String;)Ljava/io/File;',
       '    const/4 v2, 0x0\n\n    invoke-virtual {v0, v1, v2}, Landroid/content/Context;->getDir(Ljava/lang/String;I)Ljava/io/File;')
# The stock HAL exposes MIVI tags beyond availableCaptureRequestKeys. On HyperOS
# the app enumerates the complete vendor descriptor; use that same supported
# CameraMetadataNative API on AOSP without spoofing the system's MIUI identity.
change(WORK / 'classes.dex.smali/s8/b.smali',
       '    invoke-static {}, LSb/X8;->n()Z\n\n    move-result p2\n\n    if-eqz p2, :cond_366\n\n    invoke-static {p1}, LMh/b;->c',
       '    # AOSP: include the HAL MIVI vendor tags, as on stock.\n\n    invoke-static {p1}, LMh/b;->c')
for n in ['classes.dex', 'classes2.dex']:
    run(JAVA, '-Xmx2g', '-jar', SMALI / 'smali.jar', 'a', WORK / (n + '.smali'), '-o', WORK / ('patched-' + n))

unsigned = WORK / 'unsigned.apk'
with zipfile.ZipFile(STOCK) as src, zipfile.ZipFile(unsigned, 'w') as dst:
    for entry in src.infolist():
        if entry.filename.startswith('META-INF/'):
            continue
        data = (WORK / ('patched-' + entry.filename)).read_bytes() if entry.filename in ['classes.dex', 'classes2.dex'] else src.read(entry.filename)
        dst.writestr(entry, data)
aligned = WORK / 'aligned.apk'
run(BT / 'zipalign', '-f', '-P', '16', '4', unsigned, aligned)
# Platform signing provides the app-scoped hidden API access used by MIUIX.
# No global hidden API exemptions and no framework replacement are needed.
run(BT / 'apksigner', 'sign', '--key', args.key.resolve(), '--cert', args.cert.resolve(), '--out', OUTPUT, aligned)
print(OUTPUT)
