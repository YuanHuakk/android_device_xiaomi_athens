#
# Copyright (C) 2026 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

# Set the boot animation size before inheriting PixelOS configuration.
TARGET_SCREEN_WIDTH := 1156
TARGET_SCREEN_HEIGHT := 2510

# Product configuration
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

$(call inherit-product, vendor/custom/config/common_full_phone.mk)

$(call inherit-product, device/xiaomi/athens/device.mk)

# Keep authenticated root ADB available in userdebug builds.
ifeq ($(TARGET_BUILD_VARIANT),userdebug)
PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG := false
endif

# Device identity
PRODUCT_NAME := custom_athens
PRODUCT_DEVICE := athens
PRODUCT_BRAND := Redmi
PRODUCT_MODEL := REDMI K100 Pro
PRODUCT_MANUFACTURER := xiaomi

# GMS
PRODUCT_GMS_CLIENTID_BASE := android-xiaomi
