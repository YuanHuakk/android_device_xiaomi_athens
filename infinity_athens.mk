#
# Copyright (C) 2026 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

TARGET_SCREEN_WIDTH := 1156
TARGET_SCREEN_HEIGHT := 2510
TARGET_HAS_UDFPS := true
WITH_GAPPS := true
INFINITY_BUILD_TYPE := UNOFFICIAL
PRODUCT_GMS_CLIENTID_BASE := android-xiaomi

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)
$(call inherit-product, vendor/infinity/config/common_full_phone.mk)

$(call inherit-product, device/xiaomi/athens/device.mk)

PRODUCT_PACKAGES += InfinityChargingAthens

# Keep authenticated root ADB available in userdebug builds.
ifeq ($(TARGET_BUILD_VARIANT),userdebug)
PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG := false
endif

# Device identity
PRODUCT_DEVICE := athens
PRODUCT_NAME := infinity_athens
PRODUCT_BRAND := Redmi
PRODUCT_MODEL := Redmi K100 Pro
PRODUCT_MANUFACTURER := xiaomi
