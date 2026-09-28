#
# Copyright (C) 2026 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

# ── 开机动画分辨率：必须写在 vendor/custom 继承**之前** ─────────────────────
# 依据（实测取回 PixelOS-AOSP/android_vendor_custom 的 config/common.mk:3-8，
# revision 见 .repo/local_manifests/athens-pixelos.xml）：
#
#     ifeq ($(strip $(TARGET_SCREEN_WIDTH)),)
#         $(warning "TARGET_SCREEN_WIDTH is undefined, assuming 1080p")
#     else
#         $(call soong_config_set,vendor_custom,bootanimation_res,$(TARGET_SCREEN_WIDTH))
#     endif
#
# 没赋值不会报错，只打一句 $(warning) 然后按 1080p 选资源；athens 是 1156 宽，
# 后果是开机动画被拉伸。这是"改一行位置就能避免"的静默错误，所以放在文件最前。
# VERIFIED：athens 屏 1156x2510（原厂 ro.sf.lcd_density=480）。
TARGET_SCREEN_WIDTH := 1156
TARGET_SCREEN_HEIGHT := 2510

# Inherit from those products. Most specific first.
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit some common PixelOS stuff.
# 这一条会连带继承 vendor/lineage/config/common_full_phone.mk 与
# vendor/custom/config/common.mk（含 pixel.mk / ota.mk / version.mk）。
# 所以**不要在下面再继承一次 common_full_phone** —— 会重复。
$(call inherit-product, vendor/custom/config/common_full_phone.mk)

# Inherit from the athens device.
$(call inherit-product, device/xiaomi/athens/device.mk)

# Bring-up needs adb root; keep ro.adb.secure=1 and host-key authorization.
ifeq ($(TARGET_BUILD_VARIANT),userdebug)
PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG := false
endif

## Device identifier
# VERIFIED —— 原厂指纹 Redmi/athens/athens:16/BQ2A.260225.001-BP2A.250705.008/OS3.0.306.0.WPICNXM:user/release-keys
# 本机包是 CN（WPICNXM），故 BRAND=Redmi。POCO F9 Pro 是同机换标，走 EEA 包时再另立 product。
# 与 lineage_athens.mk 保持同值：两套产品入口除 PRODUCT_NAME 外不该有别的差异。
PRODUCT_NAME := custom_athens
PRODUCT_DEVICE := athens
PRODUCT_BRAND := Redmi
PRODUCT_MODEL := REDMI K100 Pro
PRODUCT_MANUFACTURER := xiaomi

# GMS
# PixelOS 官方设备树的规范写法（对照 PixelOS-Devices/android_device_xiaomi_alioth
# 的 seventeen 分支 custom_alioth.mk），两者都在，缺一不可：
PRODUCT_GMS_CLIENTID_BASE := android-xiaomi
# Use the generated PixelOS fingerprint for system/OTA identity. The stock
# Android 16 fingerprint belongs in the recovery baseline, not post-build.

# 非官方构建身份：**不**设 IS_OFFICIAL=true。
# 依据：vendor/custom/config/version.mk:16 只在 IS_OFFICIAL=true 时写
# net.pixelos.build_type=ci，那是 CI 自动构建的标记，本地自编不该带。
