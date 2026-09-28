#
# Copyright (C) 2026 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

# Device paths
DEVICE_PATH := device/xiaomi/athens
KERNEL_PATH := $(DEVICE_PATH)-kernel

# Kernel module directory name
KERNEL_RELEASE := 6.12.69-android16-6-g0d80ee00f747-ab15461283-4k

# Common configuration
include device/xiaomi/sm8850-common/BoardConfigCommon.mk

# Keep the installed pvmfw while AVF is disabled.
AB_OTA_PARTITIONS := $(filter-out pvmfw,$(AB_OTA_PARTITIONS))
BOARD_AVB_VBMETA_SYSTEM := $(filter-out pvmfw,$(BOARD_AVB_VBMETA_SYSTEM))
BOARD_BOOTCONFIG := $(filter-out androidboot.hypervisor.protected_vm.supported=true,$(BOARD_BOOTCONFIG))
BOARD_BOOTCONFIG += androidboot.hypervisor.protected_vm.supported=false

# ABL requires descriptors for the preserved pvmfw and countrycode partitions.
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --include_descriptors_from_image $(DEVICE_PATH)/avb/oem_boot_descriptors.img

# GKI v4 reads OS and patch levels from AVB properties.
BOARD_MKBOOTIMG_ARGS += --os_version 0 --os_patch_level 0
BOARD_MKBOOTIMG_INIT_ARGS += --os_version 0 --os_patch_level 0

# SELinux
ifneq ($(filter eng userdebug,$(TARGET_BUILD_VARIANT)),)
BOARD_BOOTCONFIG += androidboot.selinux=permissive
BOARD_KERNEL_CMDLINE += androidboot.selinux=permissive
endif

# NFC; the common manifest already declares the secure element.
ODM_MANIFEST_FILES := \
    $(DEVICE_PATH)/configs/vintf/nfc-service-nxp.xml

# Device-specific vendor HALs
DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE += \
    $(DEVICE_PATH)/configs/vintf/compatibility_matrix.athens.xml

# SELinux policy
BOARD_VENDOR_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/vendor

# Display
TARGET_SCREEN_DENSITY := 480

# Prebuilt kernel
BOARD_PREBUILT_DTBOIMAGE := $(KERNEL_PATH)/dtbo.img
BOARD_PREBUILT_DTBIMAGE_DIR := $(KERNEL_PATH)/dtb

TARGET_NO_KERNEL_OVERRIDE := true

# UAPI headers consumed by the patched Soong configuration.
TARGET_PREBUILT_KERNEL_HEADERS := $(KERNEL_PATH)/kernel-headers.tar.gz
PRODUCT_COPY_FILES += \
    $(KERNEL_PATH)/kernel:kernel

# Kernel modules
BOARD_VENDOR_RAMDISK_KERNEL_MODULES_LOAD := $(strip $(shell cat $(KERNEL_PATH)/vendor_ramdisk/modules.load))
BOARD_VENDOR_RAMDISK_RECOVERY_KERNEL_MODULES_LOAD := $(strip $(shell cat $(KERNEL_PATH)/vendor_ramdisk/modules.load.recovery))
BOARD_VENDOR_KERNEL_MODULES_LOAD := $(strip $(shell cat $(KERNEL_PATH)/vendor_dlkm/modules.load))

PRODUCT_COPY_FILES += \
    $(call find-copy-subdir-files,*,$(KERNEL_PATH)/vendor_dlkm/,$(TARGET_COPY_OUT_VENDOR_DLKM)/lib/modules) \
    $(call find-copy-subdir-files,*,$(KERNEL_PATH)/vendor_ramdisk/,$(TARGET_COPY_OUT_VENDOR_RAMDISK)/lib/modules) \
    $(call find-copy-subdir-files,*,$(KERNEL_PATH)/system_dlkm_flatten/,$(TARGET_COPY_OUT_SYSTEM_DLKM)/flatten/lib/modules) \
    $(call find-copy-subdir-files,*,$(KERNEL_PATH)/system_dlkm/,$(TARGET_COPY_OUT_SYSTEM_DLKM)/lib/modules/$(KERNEL_RELEASE))

# Device properties
TARGET_ODM_PROP += $(DEVICE_PATH)/configs/properties/odm.prop

# Partition sizes
BOARD_SUPER_PARTITION_SIZE := 16106127360
BOARD_QTI_DYNAMIC_PARTITIONS_SIZE := 16095641600

# Use the physical partition size, not the padded image file size.
BOARD_DTBOIMG_PARTITION_SIZE := 33554432

# Patch levels for the stock OS3.0.306.0 vendor and kernel.
BOOT_SECURITY_PATCH := 2026-08-01
VENDOR_SECURITY_PATCH := $(BOOT_SECURITY_PATCH)

# Keep the installed boot rollback index; use the platform date for system.
BOARD_AVB_BOOT_ROLLBACK_INDEX := 1785542400
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX := $(shell if [ $(PLATFORM_SECURITY_PATCH_TIMESTAMP) -gt 1785542400 ]; then echo $(PLATFORM_SECURITY_PATCH_TIMESTAMP); else echo 1785542400; fi)
BOARD_AVB_RECOVERY_ROLLBACK_INDEX := $(BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX)

# Vendor configuration
-include vendor/xiaomi/athens/BoardConfigVendor.mk
