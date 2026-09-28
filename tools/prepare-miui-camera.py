#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare stock athens Xiaomi Camera 6.3.008710.8 for PixelOS."""

import argparse
import subprocess
import tempfile
import zipfile
from pathlib import Path

DEX_FILES = ("classes.dex", "classes2.dex")


def run_tool(*command: str | Path) -> None:
    subprocess.run([str(argument) for argument in command], check=True)


def replace_once(path: Path, old: str, new: str) -> None:
    content = path.read_text()
    if content.count(old) != 1:
        raise ValueError(f"Expected one patch location in {path}")
    path.write_text(content.replace(old, new))


def patch_smali(work: Path) -> None:
    """Adapt permissions, the MIVI debug directory, and vendor-tag enumeration."""
    replace_once(
        work / "classes.dex.smali/com/android/camera/a$c.smali",
        "    const p1, 0x7f140bdd\n\n    invoke-static {p0, p1}, LD1/t3;->g(Landroid/app/Activity;I)V\n",
        "    # AOSP: omit the HyperOS-only limited-permissions dialog.\n",
    )
    replace_once(
        work / "classes2.dex.smali/id/c.smali",
        "    move-result v0\n\n    sput-boolean v0, Lid/c;->m:Z",
        "    const/4 v0, 0x1\n\n    sput-boolean v0, Lid/c;->m:Z",
    )
    replace_once(
        work / "classes2.dex.smali/ff/e.smali",
        ".method static constructor <clinit>()V\n    .registers 2",
        ".method static constructor <clinit>()V\n    .registers 3",
    )
    replace_once(
        work / "classes2.dex.smali/ff/e.smali",
        "    invoke-virtual {v0, v1}, Landroid/content/Context;->getExternalFilesDir(Ljava/lang/String;)Ljava/io/File;",
        "    const/4 v2, 0x0\n\n    invoke-virtual {v0, v1, v2}, Landroid/content/Context;->getDir(Ljava/lang/String;I)Ljava/io/File;",
    )
    replace_once(
        work / "classes.dex.smali/s8/b.smali",
        "    invoke-static {}, LSb/X8;->n()Z\n\n    move-result p2\n\n    if-eqz p2, :cond_366\n\n    invoke-static {p1}, LMh/b;->c",
        "    # AOSP: include the HAL MIVI vendor tags, as on stock.\n\n    invoke-static {p1}, LMh/b;->c",
    )


def prepare_camera(
    tree: Path,
    stock_apk: Path,
    build_tools: Path,
    key: Path,
    cert: Path,
    output: Path,
) -> None:
    java = tree / "prebuilts/jdk/jdk21/linux-x86/bin/java"
    smali = tree / "prebuilts/extract-tools/common/smali"
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="athens-camera-") as temporary:
        work = Path(temporary)
        with zipfile.ZipFile(stock_apk) as apk:
            for name in DEX_FILES:
                (work / name).write_bytes(apk.read(name))
                run_tool(
                    java,
                    "-Xmx2g",
                    "-jar",
                    smali / "baksmali.jar",
                    "d",
                    work / name,
                    "-o",
                    work / (name + ".smali"),
                )

        patch_smali(work)
        for name in DEX_FILES:
            run_tool(
                java,
                "-Xmx2g",
                "-jar",
                smali / "smali.jar",
                "a",
                work / (name + ".smali"),
                "-o",
                work / ("patched-" + name),
            )

        unsigned = work / "unsigned.apk"
        with (
            zipfile.ZipFile(stock_apk) as original,
            zipfile.ZipFile(unsigned, "w") as apk,
        ):
            for entry in original.infolist():
                if entry.filename.startswith("META-INF/"):
                    continue
                if entry.filename in DEX_FILES:
                    data = (work / ("patched-" + entry.filename)).read_bytes()
                else:
                    data = original.read(entry.filename)
                apk.writestr(entry, data)

        aligned = work / "aligned.apk"
        run_tool(build_tools / "zipalign", "-f", "-P", "16", "4", unsigned, aligned)
        # MIUIX requires the ROM platform certificate for hidden API access.
        run_tool(
            build_tools / "apksigner",
            "sign",
            "--key",
            key,
            "--cert",
            cert,
            "--out",
            output,
            aligned,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", required=True, type=Path, help="PixelOS source root")
    parser.add_argument("--stock-apk", required=True, type=Path)
    parser.add_argument("--build-tools", required=True, type=Path)
    parser.add_argument(
        "--key", required=True, type=Path, help="Platform signing key (.pk8)"
    )
    parser.add_argument(
        "--cert", required=True, type=Path, help="Platform certificate (.x509.pem)"
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    prepare_camera(
        args.tree.resolve(),
        args.stock_apk.resolve(),
        args.build_tools.resolve(),
        args.key.resolve(),
        args.cert.resolve(),
        args.output.resolve(),
    )
    print(args.output.resolve())


if __name__ == "__main__":
    main()
