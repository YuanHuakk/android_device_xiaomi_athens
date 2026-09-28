#
# Copyright (C) 2026 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#
# 取值依据标注：VERIFIED = 本机原厂包实测；TODO = 尚未取证，写明了取法。
#

DEVICE_PATH := device/xiaomi/athens
KERNEL_PATH := $(DEVICE_PATH)-kernel

# Kernel
# VERIFIED —— 取自 athens 自己的 boot.img：
#   strings boot.img | grep -m1 'Linux version'
#   → Linux version 6.12.69-android16-6-g0d80ee00f747-ab15461283-4k
# 与 songyuan 逐字符相同（含 git 短哈希与 build id），即两台设备用的是同一次 kleaf 构建。
# KMI 代 = android16-6（GKI 分支 android16-6.12），4K 页。
# 这个值决定 system_dlkm 下模块的落盘路径；填错的表现是模块静默不加载。
KERNEL_RELEASE := 6.12.69-android16-6-g0d80ee00f747-ab15461283-4k

# Inherit from sm8850-common
include device/xiaomi/sm8850-common/BoardConfigCommon.mk

# Preserve the device's stock pvmfw. Keep OTA membership and AVB descriptors
# consistent with PRODUCT_BUILD_PVMFW_IMAGE=false / PRODUCT_AVF_ENABLED=false.
AB_OTA_PARTITIONS := $(filter-out pvmfw,$(AB_OTA_PARTITIONS))
BOARD_AVB_VBMETA_SYSTEM := $(filter-out pvmfw,$(BOARD_AVB_VBMETA_SYSTEM))
BOARD_BOOTCONFIG := $(filter-out androidboot.hypervisor.protected_vm.supported=true,$(BOARD_BOOTCONFIG))
BOARD_BOOTCONFIG += androidboot.hypervisor.protected_vm.supported=false

# ABL still requests the stock pvmfw and countrycode while AVF is disabled.
# Preserve their stock hash descriptors so all six requested boot partitions
# are loaded. This metadata contains no firmware and adds no OTA partitions.
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --include_descriptors_from_image $(DEVICE_PATH)/avb/oem_boot_descriptors.img

# GKI v4 stores OS/SPL in AVB properties, leaving the packed header field zero.
# These board arguments follow the platform arguments in mkbootimg invocation.
BOARD_MKBOOTIMG_ARGS += --os_version 0 --os_patch_level 0
BOARD_MKBOOTIMG_INIT_ARGS += --os_version 0 --os_patch_level 0

# First-boot bring-up: keep SELinux loaded and logging, but do not enforce AVCs.
# init accepts this boot parameter in eng/userdebug builds. Production user
# builds remain enforcing. Verify the built vendor_boot/recovery parameters.
ifneq ($(filter eng userdebug,$(TARGET_BUILD_VARIANT)),)
BOARD_BOOTCONFIG += androidboot.selinux=permissive
BOARD_KERNEL_CMDLINE += androidboot.selinux=permissive
endif

# NFC
# VERIFIED —— athens 是 NXP，不是 songyuan 的 ST54L。原厂 odm 里有三个 fragment：
#   odm/etc/vintf/manifest/nfc2-service-nxp.xml
#   odm/etc/vintf/manifest/android.hardware.security.keymint3-service.strongbox.nxp.xml
#   odm/etc/vintf/manifest/android.hardware.weaver-service.nxp.xml
# 前者的内容是 android.hardware.nfc v2 + secure_element/eSE1 + vendor.nxp.nxpnfc_aidl。
#
# 我们自带的 manifest 只保留 nfc 与 nxp 两项：secure_element/eSE1 已由
# sm8850-common 的 configs/vintf/manifest_canoe.xml 声明，重复声明会被 VINTF 判冲突。
# 裁剪细节与逐项实测写在 configs/vintf/nfc-service-nxp.xml 里。
#
# ❌ 故意不列 contexthub：
#   songyuan 的清单**提取** odm/etc/init/android.hardware.contexthub-service.qmi.rc
#   并据此声明该 HAL。athens 原厂**没有这个 rc**（全盘搜 contexthub 只命中
#   vendor/bin/hw/... 二进制与两个 @1.0/V3-ndk 库，没有任何 .rc 提到它），
#   服务不会被 init 拉起 —— 声明它就是声明一个永远不存在的 HAL。
ODM_MANIFEST_FILES := \
    $(DEVICE_PATH)/configs/vintf/nfc-service-nxp.xml

# athens-specific private HAL instances carried by the stock ODM manifest.
DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE += \
    $(DEVICE_PATH)/configs/vintf/compatibility_matrix.athens.xml

# ── NXP OEM AID（实施方案 §9.4）──────────────────────────────────────────────
# 结论：**设备树不需要新增 config.fs**。取证如下。
#
# 1) AID 值本身公共树已经有了，且与 athens 原厂逐值一致 ——
#    对照 device/xiaomi/sm8850-common/configs/config.fs 与 athens 的 vendor/etc/passwd：
#      公共树                                   athens 原厂 vendor/etc/passwd:10,11,15
#      AID_VENDOR_NXP_STRONGBOX  = 2910    →    vendor_nxp_strongbox::2910:2910
#      AID_VENDOR_NXP_WEAVER     = 2911    →    vendor_nxp_weaver::2911:2911
#      AID_VENDOR_NXP_AUTHSECRET = 2915    →    vendor_nxp_authsecret::2915:2915
#    公共树那份还多带 Thales 的 2913/2916/2917（songyuan 用），在 athens 上无引用，留着无害。
#
# 2) 运行期 uid 由 rc 的 `user` 决定，不由 fs_config 决定。athens 两个 rc 实测：
#      odm/etc/init/android.hardware.security.keymint3-service.strongbox.nxp.rc:3  user vendor_nxp_strongbox
#      odm/etc/init/android.hardware.weaver-service.nxp.rc:3-4                     user/group vendor_nxp_weaver
#    两个都**没有 capabilities 行**，即 init 不为它们追加 capability。所以只要 AID 存在就能起来。
#
# 3) ⚠️ 未对齐的一项（**已知且暂不修**，P4 复核）：公共树 fs_config 里的**路径条目**写的是
#    源码构建产物，与 athens 的 blob 路径/名字都对不上：
#      公共树 [vendor/bin/hw/android.hardware.security.keymint4-service.strongbox-nxp-qti]
#      athens  odm/bin/hw/android.hardware.security.keymint3-service.strongbox.nxp   ← keymint3 非 4
#      公共树 [vendor/bin/hw/android.hardware.authsecret-service.nxp-qti]
#      athens  odm/bin/hw/vendor.xiaomi.hardware.authsecretd                        ← 名字完全不同
#    后果有限：这些条目管的是**文件属主/权限**，而 /odm/bin/* 走 AOSP 默认（0755 root:shell，
#    全局可执行），init 照样能 exec 再降权到 AID。所以不阻塞启动。
#    真要补，写法必须是 TARGET_FS_CONFIG_GEN **+=** —— 公共树用的是 `:=`
#    （BoardConfigCommon.mk:67），写成 := 会把它整份顶掉，平台 AID 一起丢。
#
# 4) 不开 TARGET_FS_CONFIG_GEN：没有要加的东西，多一份空配置只会掩盖上面第 3 点。

# ── Sepolicy（实施方案 §9.6）────────────────────────────────────────────────
# 只做**对象标注**，不做 allow 规则。三个 NXP HAL 在 athens 上位于 /odm/bin/hw/，
# 而 QTI 的 sm8850 策略只按 /vendor/bin/hw/ 正则标注 —— 实测三条绝对路径全无匹配，
# 未标注 = vendor_file = init exec 不了 = 服务静默不启动。逐条依据写在
# sepolicy/vendor/file_contexts 里。
#
# ⚠️ 必须用 **+=** 且必须放在 BoardConfigCommon.mk 的 include **之后**：
#    公共树 BoardConfigCommon.mk:141 自己也是 `BOARD_VENDOR_SEPOLICY_DIRS += ...`
#    （它先 include device/qcom/sepolicy_vndr/SEPolicy.mk 再追加自己的 sepolicy 目录），
#    这里若写成 := 会把 QTI 与公共树两个目录一起顶掉，整份 vendor 策略消失。
#    放在 include 之后是同一个道理：先让它们写完，再追加。
BOARD_VENDOR_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/vendor

# Display
# VERIFIED —— 原厂 ro.sf.lcd_density=480（在 **product/etc/build.prop**，不是 odm/vendor，
# 那两处一个字都没有）。另有 persist.miui.density_v2=480。
# ⚠️ 原厂 product 分区我们不用（ROM 的 product 由 AOSP 源码编出来），所以这个值必须由
#    此处带上，不能指望 blob —— 否则密度回落到默认值，界面整体缩小。
TARGET_SCREEN_DENSITY := 480

# Dtb/o
BOARD_PREBUILT_DTBOIMAGE := $(KERNEL_PATH)/dtbo.img
BOARD_PREBUILT_DTBIMAGE_DIR := $(KERNEL_PATH)/dtb

TARGET_NO_KERNEL_OVERRIDE := true

# Kernel headers: no kernel source is published for any SM8850 Xiaomi device, so
# ship the QTI UAPI headers (IPA) that in-tree code needs. This assignment feeds
# the prebuilt_kernel_includes genrule, but cc.go reads the same name with
# Getenv, which a makefile cannot set. So it must ALSO be exported in the shell,
# or libipanat fails on linux/msm_ipa.h:
#   export TARGET_PREBUILT_KERNEL_HEADERS=device/xiaomi/athens-kernel/kernel-headers.tar.gz
TARGET_PREBUILT_KERNEL_HEADERS := $(KERNEL_PATH)/kernel-headers.tar.gz
PRODUCT_COPY_FILES += \
	$(KERNEL_PATH)/kernel:kernel

# Kernel modules
# ⚠️ 这四个 shell cat：文件不存在时 cat 报错但 make 不中断，结果是空列表 ——
#    "零模块加载"完全静默。athens-kernel 建好后先确认这四个文件都在。
BOARD_VENDOR_RAMDISK_KERNEL_MODULES_LOAD := $(strip $(shell cat $(KERNEL_PATH)/vendor_ramdisk/modules.load))
BOARD_VENDOR_RAMDISK_RECOVERY_KERNEL_MODULES_LOAD := $(strip $(shell cat $(KERNEL_PATH)/vendor_ramdisk/modules.load.recovery))
BOARD_VENDOR_KERNEL_MODULES_LOAD := $(strip $(shell cat $(KERNEL_PATH)/vendor_dlkm/modules.load))

PRODUCT_COPY_FILES += \
    $(call find-copy-subdir-files,*,$(KERNEL_PATH)/vendor_dlkm/,$(TARGET_COPY_OUT_VENDOR_DLKM)/lib/modules) \
    $(call find-copy-subdir-files,*,$(KERNEL_PATH)/vendor_ramdisk/,$(TARGET_COPY_OUT_VENDOR_RAMDISK)/lib/modules) \
    $(call find-copy-subdir-files,*,$(KERNEL_PATH)/system_dlkm_flatten/,$(TARGET_COPY_OUT_SYSTEM_DLKM)/flatten/lib/modules) \
    $(call find-copy-subdir-files,*,$(KERNEL_PATH)/system_dlkm/,$(TARGET_COPY_OUT_SYSTEM_DLKM)/lib/modules/$(KERNEL_RELEASE))

# Properties
# odm.prop 携带原厂 odm/etc/build.prop 里机型相关的值。那个文件**不作为 blob 提取**，
# /odm/etc/build.prop 由构建生成，所以值不搬过来就会静默丢（分辨率、指纹热区、
# 传感器标定全部回落默认）。逐条依据与行号写在文件内。
TARGET_ODM_PROP += $(DEVICE_PATH)/configs/properties/odm.prop

# ❌ 故意没有 vendor.prop。songyuan 的 vendor.prop 只有两块内容，在 athens 上都不成立：
#   1) 31 行 debug.sf.*.{20,24,...,144} 逐刷新率时序 —— 那是 songyuan 覆盖公共树用的。
#      实测 athens 原厂 vendor/build.prop 用的是**无后缀**形式
#      （debug.sf.{early,earlyGl,late}.{app,sf}.duration +
#        use_phase_offsets_as_durations=1），而这 14 个键**公共树已全部覆盖，
#      且值逐字符相同**，重复声明无意义。
#   2) ro.vendor.light.white_only=true —— songyuan 的后置 LED 是纯白 AW21024。
#      athens 原厂 rc 里有独立的 leds/red、leds/green、leds/blue 三个节点，是 RGB，
#      置 true 会把彩色灯锁成白色。

# Partitions
# VERIFIED —— 解析 athens 原厂 super.img 的 LP 元数据得出（权威）：
#   super                          = 16,106,127,360  (15.00 GiB)
#   qti_dynamic_partitions 组 max_size = 16,095,641,600  (14.99 GiB)
# 两者差 10 MiB，与 songyuan 的 (16642998272 - 16632512512) 完全一致 —— 交叉验证通过。
#
# ⚠️ 不可继承也不能借：公共树默认 12.5 GiB，songyuan 覆写 15.5 GiB，两个都不对。
#    （Mianbier 那份 README 写的 12 GiB 也是错的，他那份没覆写公共树默认值。）
BOARD_SUPER_PARTITION_SIZE := 16106127360
BOARD_QTI_DYNAMIC_PARTITIONS_SIZE := 16095641600

# 其余分区由 BoardConfigCommon.mk 提供。逐项对着 athens 原厂分区表核验过
# （stock/reports/physical-partitions.json，从设备 GPT 读出，权威）：
#
#   分区            athens 实际        公共树            结论
#   boot_a          100663296         100663296         ✅ 一致，不覆写
#   init_boot_a     8388608           8388608           ✅ 一致，不覆写
#   vendor_boot_a   100663296         100663296         ✅ 一致，不覆写
#   recovery_a      104857600         104857600         ✅ 一致，不覆写
#   dtbo_a          33554432          23068672          ❌ **必须覆写**，见下
#   pvmfw_a         1048576           1048576           ✅ 一致，不覆写
#
# dtbo 这一处是**唯一**不一致的分区，容易漏：公共树写的 23068672 恰好等于
# athens-kernel/dtbo.img 这个**文件**的长度（原厂 fastboot 包里 dtbo.img 的实体大小），
# 所以"看文件大小对上了"会得出错误结论 —— 它不是分区大小。分区是 33554432。
BOARD_DTBOIMG_PARTITION_SIZE := 33554432

# VERIFIED after the first build: dtbo receives an AVB hash footer with
# Algorithm NONE, and its hash descriptor is authenticated by root vbmeta.
# No separate BOARD_AVB_DTBO_KEY_PATH does not mean absence from the AVB chain.
# Both DT overlay payloads still match the stock image byte for byte.

# Security
# Actual pre-flash baseline: system 16OS3.1.260804.223345479.QCPECN.S / 2026-07-01;
# vendor OS3.0.306.0.WPICNXM / 2026-08-01; backed-up boot AVB SPL 2026-08-01.
# These are independent patch levels. PLATFORM_SECURITY_PATCH and AVB rollback
# indices require a separate audit; Xiaomi anti_version=1 is not either value.
BOOT_SECURITY_PATCH := 2026-08-01
VENDOR_SECURITY_PATCH := $(BOOT_SECURITY_PATCH)

# Boot is the unchanged stock kernel. Keep its known rollback baseline.
# System/recovery use the platform date, with the installed system's AVB index
# as a floor; rollback indices are counters, not security-patch declarations.
BOARD_AVB_BOOT_ROLLBACK_INDEX := 1785542400
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX := $(shell if [ $(PLATFORM_SECURITY_PATCH_TIMESTAMP) -gt 1785542400 ]; then echo $(PLATFORM_SECURITY_PATCH_TIMESTAMP); else echo 1785542400; fi)
BOARD_AVB_RECOVERY_ROLLBACK_INDEX := $(BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX)

# Inherit from the proprietary version
-include vendor/xiaomi/athens/BoardConfigVendor.mk
