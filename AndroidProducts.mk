#
# Copyright (C) 2026 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

# 两套产品入口并存（实施方案 §9.1：追加 custom_athens，保留已有 Lineage 入口）。
#   custom_athens  → PixelOS 17（本仓库当前的构建目标）
#   lineage_athens → LineageOS 24.0（同一棵树里的另一套，vendor/lineage 在 PixelOS
#                    的 manifest 里也有，所以它仍然能 lunch 起来）
# 除 PRODUCT_NAME 外两者的机型标识必须保持同值，别让它们各自漂移。
PRODUCT_MAKEFILES := \
    $(LOCAL_DIR)/lineage_athens.mk \
    $(LOCAL_DIR)/custom_athens.mk
