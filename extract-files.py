#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

namespace_imports = [
    "device/xiaomi/sm8850-common",
    "hardware/qcom-caf/sm8850",
    "hardware/xiaomi",
    "vendor/qcom/opensource/commonsys-intf/display",
    "vendor/xiaomi/sm8850-common",
]


def lib_fixup_odm_rename(lib: str, *args, **kwargs):
    """Use an ODM module suffix for consumers in either partition."""
    return f"{lib}_odm"


def lib_fixup_athens_suffix(lib: str, *args, **kwargs):
    """Avoid the source module name collision while retaining the SONAME."""
    return f"{lib}_athens"


lib_fixups: lib_fixups_user_type = {
    **lib_fixups,
    ("nfc_nci_nxp_snxxx_v2",): lib_fixup_odm_rename,
    ("libdng_sdk",): lib_fixup_athens_suffix,
}


def fixup_aosp_audio_volumes(ctx, file, file_path, *args, **kwargs):
    """Remove private categories and normalize volume indices to 0..100."""
    allowed = {
        "DEVICE_CATEGORY_HEADSET",
        "DEVICE_CATEGORY_SPEAKER",
        "DEVICE_CATEGORY_EARPIECE",
        "DEVICE_CATEGORY_EXT_MEDIA",
        "DEVICE_CATEGORY_HEARING_AID",
    }
    path = Path(file_path)
    content = path.read_text()
    pattern = r'<volume\s+deviceCategory="([^"]+)"[^>]*?/\s*>|<volume\s+deviceCategory="([^"]+)"[^>]*>.*?</volume>'

    def convert_volume(match):
        if (match[1] or match[2]) not in allowed:
            return ""
        block = match[0]
        points = list(re.finditer(r"<point>\s*(\d+)\s*,\s*(-?\d+)\s*</point>", block))
        if not points:
            return block
        max_index = max(int(point[1]) for point in points)
        if max_index <= 100:
            return block
        # AIDL volume indices must fit 0..100; preserve attenuation values.
        previous_index = -1

        def normalize_point(point):
            nonlocal previous_index
            index = max(
                previous_index + 1, (int(point[1]) * 100 + max_index // 2) // max_index
            )
            assert index <= 100
            previous_index = index
            return f"<point>{index},{point[2]}</point>"

        return re.sub(
            r"<point>\s*(\d+)\s*,\s*(-?\d+)\s*</point>", normalize_point, block
        )

    content = re.sub(pattern, convert_volume, content, flags=re.DOTALL)
    root = ET.fromstring(content)
    assert all(v.get("deviceCategory") in allowed for v in root.iter("volume"))
    path.write_text(content)


blob_fixups: blob_fixups_user_type = {
    # Remove private output types unsupported by the AOSP audio HAL.
    "odm/etc/audio/audio_module_config_primary.xml": blob_fixup()
    .regex_replace(r'(?s)<mixPort\s+name="virtual_deep_buffer"[^>]*>.*?</mixPort>', "")
    .regex_replace(r"virtual_deep_buffer,\s*|,\s*virtual_deep_buffer", "")
    .regex_replace(r'(?s)<devicePort\s+tagName="Multiroute"[^>]*>.*?</devicePort>', "")
    .regex_replace(r'<route\s+[^>]*sink="Multiroute"[^>]*/>', "")
    .regex_replace(r"\s*audio/vnd\.mi\.mihc", ""),
    "odm/etc/audio_policy_engine_stream_volumes_mi.xml": blob_fixup().call(
        fixup_aosp_audio_volumes, need_tmp_dir=False
    ),
    "odm/etc/audio_policy_engine_product_strategies_mi.xml": blob_fixup().regex_replace(
        r'(?m)^\s*<Attributes>\s*<Usage value="AUDIO_USAGE_BLUETOOTH_SCO"/>\s*</Attributes>\r?\n',
        "",
    ),
    # Keep hardware setup while replacing the stock service with the source HAL.
    "odm/etc/init/init.mfp-daemon.aidl.rc": blob_fixup()
    .regex_replace(r"(?ms)\Aservice mfp-daemon\b.*?(?=^on )", "")
    .regex_replace(
        r"(?m)^(    (?:stop|start)) mfp-daemon$", r"\1 vendor.fingerprint-default"
    ),
    (
        "odm/etc/camera/enhance_motiontuning.xml",
        "odm/etc/camera/motiontuning.xml",
        "odm/etc/camera/snsc_bokeh_motiontuning.xml",
        "odm/etc/camera/snsc_enhance_motiontuning.xml",
        "odm/etc/camera/snsc_motiontuning.xml",
        "odm/etc/camera/snsc_noface_motiontuning.xml",
    ): blob_fixup().regex_replace("xml=version", "xml version"),
    (
        "odm/lib64/libMiEmojiEffect.so",
        "odm/lib64/libMiVideoFilter.so",
        "odm/lib64/libAncHumanPreviewBokeh.so",
        "odm/lib64/libarcsoft_beautyshot.so",
        "odm/lib64/libwa_widelens_undistort.so",
        "vendor/lib64/libMiPhotoFilter.so",
    ): blob_fixup()
    .clear_symbol_version("AHardwareBuffer_allocate")
    .clear_symbol_version("AHardwareBuffer_describe")
    .clear_symbol_version("AHardwareBuffer_lockPlanes")
    .clear_symbol_version("AHardwareBuffer_release")
    .clear_symbol_version("AHardwareBuffer_unlock")
    .clear_symbol_version("AHardwareBuffer_lock")
    .clear_symbol_version("AHardwareBuffer_isSupported"),
    (
        "vendor/lib64/camera/components/com.qti.node.dewarp.so",
        "vendor/lib64/vendor.qti.hardware.camera.offlinecamera-service-impl.so",
    ): blob_fixup().replace_needed(
        "android.hardware.graphics.allocator-V1-ndk.so",
        "android.hardware.graphics.allocator-V2-ndk.so",
    ),
    (
        "vendor/lib64/vendor.xiaomi.hardware.camera.injection-V1-ndk.so",
        "vendor/lib64/vendor.xiaomi.hardware.camera.injection-client.so",
        "vendor/lib64/vendor.xiaomi.hardware.camera.injection-service.so",
    ): blob_fixup().replace_needed(
        "android.hardware.camera.device-V1-ndk.so",
        "android.hardware.camera.device-V2-ndk.so",
    ),
    (
        "odm/lib64/camera/dynamicplugins/com.xiaomi.plugin.mialgoallinone.so",
        "odm/lib64/camera/plugins/com.xiaomi.plugin.anchor.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.asd.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamawbideal.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamb2y.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamformatconvertor.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamheic.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamjpeg.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcammfnr.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcammlawb.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamtintless.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamyuveis.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamyuvreprocess.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamyuvsplit.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineawbideal.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineb2y.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineehdr.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineformatconvertor.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlinehdrraw2y.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineheic.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlinei2y.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlinejpeg.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlinemfnr.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlinemlawb.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlinetintless.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlinetintlesshdr.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineyuveis.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineyuvreprocess.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineyuvsplit.so",
        "odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineyuvwarp.so",
        "odm/lib64/com.xiaomi.plugin.ecdengine.so",
        "vendor/bin/hw/vendor.qti.camera.provider-service_64",
        "vendor/lib64/camera/components/com.mi.node.fd.so",
        "vendor/lib64/camera/components/com.qti.node.fd.so",
        "vendor/lib64/com.xiaomi.stub.chi.so",
        "vendor/lib64/com.xiaomi.stubv1.camx.so",
        "vendor/lib64/hw/camera.qcom.core.so",
        "vendor/lib64/libcamxdumpinforecorder.so",
        "vendor/lib64/libcom.xiaomi.dsac.so",
        "vendor/lib64/libmicamera_aidl_provider.so",
        "vendor/lib64/libmicamera_hal_core.so",
        "vendor/lib64/libsimulation.so",
    ): blob_fixup().replace_needed("libtinyxml2.so", "libtinyxml2-v36.so"),
    ("vendor/lib64/libcameraopt.so",): blob_fixup().add_needed(
        "libprocessgroup_shim.so"
    ),
}

module = ExtractUtilsModule(
    "athens",
    "xiaomi",
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == "__main__":
    utils = ExtractUtils.device_with_common(module, "sm8850-common", module.vendor)
    utils.run()
