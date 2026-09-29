# Xiaomi Camera

Place the platform-signed `MiuiCamera.apk` in this directory. The APK is ignored
by Git. Supported version: 6.3.008710.8 from OS3.0.306.0.WPICNXM.

Prepare it with `athens_manifest/tools/prepare-miui-camera.py`; see the companion
repository's `docs/BUILD.md`. The script adapts permissions, the MIVI dump path,
vendor-tag enumeration and RAW metadata for AOSP.
