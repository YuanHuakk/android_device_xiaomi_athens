#
# Copyright (C) 2026 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

# Inherit from products. Most specific first.
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit some common Lineage stuff.
$(call inherit-product, vendor/lineage/config/common_full_phone.mk)

# Inherit from the athens device.
$(call inherit-product, device/xiaomi/athens/device.mk)

# MIUI Camera. Activates once its blobs are extracted, see PORTING.md.
# Not created yet — YAGNI until the base ROM boots.
# ifneq ($(wildcard vendor/xiaomi/athens-miuicamera/athens-miuicamera-vendor.mk),)
# $(call inherit-product, device/xiaomi/athens-miuicamera/device.mk)
# endif

## Device identifier
# VERIFIED —— 原厂指纹 Redmi/athens/athens:16/BQ2A.260225.001-BP2A.250705.008/OS3.0.306.0.WPICNXM:user/release-keys
# 本机包是 CN（WPICNXM），故 BRAND=Redmi。POCO F9 Pro 是同机换标，走 EEA 包时再另立 product。
PRODUCT_DEVICE := athens
PRODUCT_NAME := lineage_athens
PRODUCT_BRAND := Redmi
PRODUCT_MODEL := Redmi K100 Pro
PRODUCT_MANUFACTURER := xiaomi

# NOTE: songyuan 在这里写了一个裸 `BUILD_FINGERPRINT :=` 覆盖。该变量在
# core/version_defaults.mk 里是派生值，裸赋值是否仍生效**未经验证**；AOSP 的规范
# 做法是 PRODUCT_BUILD_PROP_OVERRIDES。v1 先不写，需要时单独验证再补。
