# Local Xiaomi Camera input

Place the locally prepared, platform-signed `MiuiCamera.apk` here before building.
It is intentionally ignored by Git. The supported stock version is 6.3.008710.8
from athens OS3.0.306.0.WPICNXM.

Use `tools/prepare-miui-camera.py` as documented in `docs/BUILD.md`. The script
preserves the tested permission flow, internal MIVI dump directory and full HAL
vendor-tag enumeration. No camera APK is distributed in this source repository.
