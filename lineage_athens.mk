#
# Copyright (C) 2026 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

$(call inherit-product, vendor/lineage/config/common_full_phone.mk)

$(call inherit-product, device/xiaomi/athens/device.mk)

# Device identity
PRODUCT_DEVICE := athens
PRODUCT_NAME := lineage_athens
PRODUCT_BRAND := Redmi
PRODUCT_MODEL := Redmi K100 Pro
PRODUCT_MANUFACTURER := xiaomi
