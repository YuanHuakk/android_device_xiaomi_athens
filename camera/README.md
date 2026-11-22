# Xiaomi Camera

Place the platform-signed `MiuiCamera.apk` in this directory. The APK is ignored
by Git. Supported version: 6.7.000480.0 from OS4.0.6.0.XPICNXM.

Prepare it with `athens_manifest/tools/prepare-miui-camera.py`; see the companion
repository's `docs/BUILD.md`. The script adapts permissions, the MIVI dump path,
vendor-tag enumeration and RAW metadata for AOSP.
