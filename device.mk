#
# Copyright (C) 2026 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

# Device configurations must precede common.mk to override its copies.
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/perf/perfboostsconfig.xml:$(TARGET_COPY_OUT_VENDOR)/etc/perf/perfboostsconfig.xml \
    $(LOCAL_PATH)/configs/perf/perfboostselection.xml:$(TARGET_COPY_OUT_VENDOR)/etc/perf/perfboostselection.xml \
    $(LOCAL_PATH)/configs/perf/targetresourceconfigs.xml:$(TARGET_COPY_OUT_VENDOR)/etc/perf/targetresourceconfigs.xml \
    $(LOCAL_PATH)/configs/audio/default_volume_tables.xml:$(TARGET_COPY_OUT_VENDOR)/etc/default_volume_tables.xml \
    $(LOCAL_PATH)/configs/audio/audio_policy_volumes.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio_policy_volumes.xml \
    hardware/qcom-caf/sm8850/audio/primary-hal/configs/common/bluetooth_qti_hearing_aid_audio_policy_configuration.xml:$(TARGET_COPY_OUT_VENDOR)/etc/bluetooth_qti_hearing_aid_audio_policy_configuration.xml

# Use the source fingerprint HAL with the stock Goodix module.
TARGET_USES_STOCK_FINGERPRINT := false
# Keep the installed pvmfw until AVF support is validated.
TARGET_DISABLE_AVF := true
$(call inherit-product, device/xiaomi/sm8850-common/common.mk)

PRODUCT_AVF_ENABLED := false
PRODUCT_BUILD_PVMFW_IMAGE := false

# The stock PAL backend requires A2DP offload for LE Audio as well.
PRODUCT_VENDOR_PROPERTIES += persist.bluetooth.a2dp_offload.disabled=false

# Vendor files
$(call inherit-product, vendor/xiaomi/athens/athens-vendor.mk)

# libhardware loads the stock Goodix module through a .default.so alias.
PRODUCT_PACKAGES += fingerprint.goodix_us2.default_symlink

# Turbo uses the Tips provider to update thermal warning settings.
PRODUCT_PACKAGES += TipsPrebuilt

# Camera
PRODUCT_PACKAGES += \
    android.hardware.graphics.allocator-V1-ndk.vendor \
    vendor.qti.hardware.camera.offlinecamera-V2-ndk.vendor

# Display calibration
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/display/display_id_4630946928389601939.xml:$(TARGET_COPY_OUT_VENDOR)/etc/displayconfig/display_id_4630946928389601939.xml

# Composer interface required by the stock service.
PRODUCT_PACKAGES += \
    vendor.qti.hardware.display.composer3-V4-ndk.vendor

# Init
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/init/init.athens.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/init.athens.rc

# Soong namespaces
PRODUCT_SOONG_NAMESPACES += \
    $(LOCAL_PATH)

# Resource overlays
PRODUCT_PACKAGES += \
    FrameworksResAthens \
    SystemUIResAthens

# Boot diagnostics
ifneq (,$(filter eng userdebug,$(TARGET_BUILD_VARIANT)))
PRODUCT_COPY_FILES += \
    device/xiaomi/athens/configs/bringup/init.athens-diagnostics.rc:$(TARGET_COPY_OUT_SYSTEM)/etc/init/init.athens-diagnostics.rc \
    device/xiaomi/athens/configs/bringup/collect.sh:$(TARGET_COPY_OUT_SYSTEM)/bin/athens-collect.sh
endif

# IFAA
PRODUCT_PACKAGES += IFAAService
PRODUCT_VENDOR_PROPERTIES += persist.vendor.sys.pay.ifaa=1

# Xiaomi Camera
PRODUCT_PACKAGES += MiuiCameraAthens
# MIVI may enlarge JPEG output for watermark layouts. Keep its requested size.
PRODUCT_VENDOR_PROPERTIES += persist.vendor.camera.privapp.list=com.android.camera
