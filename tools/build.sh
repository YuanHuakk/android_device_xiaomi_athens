#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
set -eo pipefail
: "${TREE:?Set TREE to the PixelOS source root}"
cd "$TREE"
source build/envsetup.sh
lunch custom_athens trunk_staging userdebug
m -j"${JOBS:-12}" "${1:-pixelos}"
