#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#
# ┌──────────────────────────────────────────────────────────────────────────┐
# │ 本表每一条都来自**对 athens 自己那份 blob 的实测**，验证命令写在条目上方。 │
# │ songyuan 的同类文件只当检查表用 —— 凡在 athens 上实测不成立的都剔掉了。   │
# │                                                                          │
# │ 已剔除的反例：songyuan 对 `com.qti.node.gme.so` 有一个 12 字节 OIS 补丁， │
# │ athens 同路径文件里不含该字节串（相机不同），该条不适用。                 │
# │                                                                          │
# │ 平台级 blob 的 fixup 不在这里：device/xiaomi/sm8850-common 自带的        │
# │ extract-files.py 有一份（52 个文件），由下面的 device_with_common 一并    │
# │ 生效。两棵树的 fixup 文件集实测交集为 0，各管各的，不会互相覆盖。         │
# │                                                                          │
# │ ⚠️ 已知归属待办（不在本文件）：                                            │
# │   vendor/lib64/hw/libaudiocorehal.qti.so 与 vendor/lib64/libsdmcore.so    │
# │   实测 NEEDED 含 libtinyxml2.so，但这两个只在**公共树**的提取清单里，     │
# │   其 fixup 要写进公共树补丁，写这里不会生效。                             │
# └──────────────────────────────────────────────────────────────────────────┘

from pathlib import Path
import re
import xml.etree.ElementTree as ET

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

# 参与构建的 soong namespace。与 songyuan 的清单逐字相同 —— 这是
# sm8850-common 型设备树的已验证写法，公共树另有一份更长的（那是它自己的
# vendor 树的 namespace，两份互不合并，不是本文件少写了）。
namespace_imports = [
    'device/xiaomi/sm8850-common',
    'hardware/qcom-caf/sm8850',
    'hardware/xiaomi',
    'vendor/qcom/opensource/commonsys-intf/display',
    'vendor/xiaomi/sm8850-common',
]

def lib_fixup_odm_rename(lib: str, *args, **kwargs):
    """把对 odm 专属 blob 的引用无条件改指带 _odm 后缀的模块。

    与公共树的 lib_fixup_vendor_suffix **不能按消费者分区判断**：
    nfc_nci_nxp_snxxx_v2.so 的消费者实测跨两个分区 ——
      odm/bin/hw/android.hardware.nqnfc-service.nxp   (odm)
      vendor/lib64/libnfc_vendor_extn.so              (vendor)
    而原厂只在 /odm/lib64/ 放了这一份（vendor 侧不存在，已 find 验证），
    vendor 侧那个消费者运行期同样从 /odm/lib64 加载。若按分区分流，vendor
    那一侧会留在源码版上；而源码版属默认 namespace、不被任何
    PRODUCT_PACKAGES 引用、不会安装 —— 结果是运行期找不到 SONAME。
    """
    return f'{lib}_odm'


def lib_fixup_athens_suffix(lib: str, *args, **kwargs):
    """把对 libdng_sdk 的引用改指带 _athens 后缀的模块。

    原厂只在 /vendor/lib64/ 放了一份 libdng_sdk.so，而构建树 external/dng_sdk
    有一个同名源码模块（system 分区），Soong 的 prebuilt 覆盖机制要求两者同
    分区，否则报 partition is different —— 加后缀消歧（<清单里同一行也写了
    MODULE_SUFFIX=_athens，两处必须一致>）。

    **与 nfc_nci_nxp_snxxx_v2 的关键差别**：这里后缀只用于模块名消歧，
    **绝不能动 SONAME**。公共树的 libwfdcommonutils.so（system_ext 分区）的
    DT_NEEDED 实测就是 libdng_sdk.so，而 system_ext 模块运行期在 /vendor/lib64
    里按 SONAME 找它 —— 一旦改名（如早先的 `:libdng_sdk-athens.so;FIX_SONAME`
    写法），这个消费者会永久找不到库。extract-utils 的 MODULE_SUFFIX 正好只改
    模块名、把 stem 留作原名，安装文件名与 SONAME 都不变，是本场景的正解。
    """
    return f'{lib}_athens'


lib_fixups: lib_fixups_user_type = {
    **lib_fixups,
    # 源码树 hardware/nxp/nfc/snxxx 有一个同名模块，它落 vendor 分区而本 blob
    # 落 odm，Soong 的 prebuilt 覆盖机制要求两者同分区，否则报
    #   partition is different: vendor(...) != odm(prebuilt_...)
    # 加后缀消歧（<清单里同一行也写了 MODULE_SUFFIX=_odm，两处必须一致>）；
    # stem 由 extract-utils 一并写入，安装文件名保持不变。
    ('nfc_nci_nxp_snxxx_v2',): lib_fixup_odm_rename,
    ('libdng_sdk',): lib_fixup_athens_suffix,
}

def fixup_aosp_audio_volumes(ctx, file, file_path, *args, **kwargs):
    """Adapt MIUI categories and extended curve indices to AOSP audio policy."""
    allowed = {
        'DEVICE_CATEGORY_HEADSET', 'DEVICE_CATEGORY_SPEAKER',
        'DEVICE_CATEGORY_EARPIECE', 'DEVICE_CATEGORY_EXT_MEDIA',
        'DEVICE_CATEGORY_HEARING_AID',
    }
    path = Path(file_path)
    content = path.read_text()
    pattern = r'<volume\s+deviceCategory="([^"]+)"[^>]*?/\s*>|<volume\s+deviceCategory="([^"]+)"[^>]*>.*?</volume>'
    def convert_volume(match):
        if (match[1] or match[2]) not in allowed:
            return ''
        block = match[0]
        points = list(re.finditer(r'<point>\s*(\d+)\s*,\s*(-?\d+)\s*</point>', block))
        if not points:
            return block
        max_index = max(int(point[1]) for point in points)
        if max_index <= 100:
            return block
        # Stock music/speaker uses 0..150. AIDL's signed-byte indices wrap
        # 130/140/150 negative, making every nonzero UI step use the final gain.
        # Normalize positions, keeping attenuation and distinct low-end points.
        previous_index = -1
        def normalize_point(point):
            nonlocal previous_index
            index = max(previous_index + 1,
                        (int(point[1]) * 100 + max_index // 2) // max_index)
            assert index <= 100
            previous_index = index
            return f'<point>{index},{point[2]}</point>'
        return re.sub(r'<point>\s*(\d+)\s*,\s*(-?\d+)\s*</point>', normalize_point, block)

    content = re.sub(pattern, convert_volume, content, flags=re.DOTALL)
    root = ET.fromstring(content)
    assert all(v.get('deviceCategory') in allowed for v in root.iter('volume'))
    path.write_text(content)


# ── blob 修补表 ────────────────────────────────────────────────────────────
blob_fixups: blob_fixups_user_type = {
    # AOSP cannot convert Xiaomi's virtual output, multiroute device or MIHC codec.
    'odm/etc/audio/audio_module_config_primary.xml': blob_fixup()
        .regex_replace(r'(?s)<mixPort\s+name="virtual_deep_buffer"[^>]*>.*?</mixPort>', '')
        .regex_replace(r'virtual_deep_buffer,\s*|,\s*virtual_deep_buffer', '')
        .regex_replace(r'(?s)<devicePort\s+tagName="Multiroute"[^>]*>.*?</devicePort>', '')
        .regex_replace(r'<route\s+[^>]*sink="Multiroute"[^>]*/>', '')
        .regex_replace(r'\s*audio/vnd\.mi\.mihc', ''),
    'odm/etc/audio_policy_engine_stream_volumes_mi.xml': blob_fixup()
        .call(fixup_aosp_audio_volumes, need_tmp_dir=False),
    # The AIDL audio converter rejects Xiaomi's private SCO usage and aborts.
    # Keep the SCO stream/volume group and AUDIO_FLAG_SCO routing rule.
    'odm/etc/audio_policy_engine_product_strategies_mi.xml': blob_fixup()
        .regex_replace(r'(?m)^\s*<Attributes>\s*<Usage value="AUDIO_USAGE_BLUETOOTH_SCO"/>\s*</Attributes>\r?\n', ''),
    # Keep hardware permissions/directories, with only the source service running.
    'odm/etc/init/init.mfp-daemon.aidl.rc': blob_fixup()
        .regex_replace(r'(?ms)\Aservice mfp-daemon\b.*?(?=^on )', '')
        .regex_replace(r'(?m)^(    (?:stop|start)) mfp-daemon$', r'\1 vendor.fingerprint-default'),
    # 原厂把 XML 声明写成了非法的 `xml=version`，AOSP 的解析器只认 `xml version`。
    # 实测：6 个文件全部含 b'xml=version'（grep -c 逐个确认）
    (
        'odm/etc/camera/enhance_motiontuning.xml',
        'odm/etc/camera/motiontuning.xml',
        'odm/etc/camera/snsc_bokeh_motiontuning.xml',
        'odm/etc/camera/snsc_enhance_motiontuning.xml',
        'odm/etc/camera/snsc_motiontuning.xml',
        'odm/etc/camera/snsc_noface_motiontuning.xml',
    ): blob_fixup()
        .regex_replace('xml=version', 'xml version'),

    # 这几个闭源库把 AHardwareBuffer_* 绑到了私有的 @LIBNATIVEWINDOW 符号版本上。
    # 实测：readelf -W --dyn-syms <lib> | grep AHardwareBuffer_allocate → 全部带
    # @LIBNATIVEWINDOW。清版本后按无版本符号解析。
    # 7 个符号是各库实测集合的并集；对不含某符号的库，clear_symbol_version 是空操作。
    (
        'odm/lib64/libMiEmojiEffect.so',
        'odm/lib64/libMiVideoFilter.so',
        'odm/lib64/libAncHumanPreviewBokeh.so',
        'odm/lib64/libarcsoft_beautyshot.so',
        'odm/lib64/libwa_widelens_undistort.so',
        'vendor/lib64/libMiPhotoFilter.so',
    ): blob_fixup()
        .clear_symbol_version('AHardwareBuffer_allocate')
        .clear_symbol_version('AHardwareBuffer_describe')
        .clear_symbol_version('AHardwareBuffer_lockPlanes')
        .clear_symbol_version('AHardwareBuffer_release')
        .clear_symbol_version('AHardwareBuffer_unlock')
        .clear_symbol_version('AHardwareBuffer_lock')
        .clear_symbol_version('AHardwareBuffer_isSupported'),

    # 相机的 allocator NDK 代次落后一代。
    # 实测：readelf -dW <lib> | grep allocator-V1-ndk —— 只有这两个还有 V1，
    # songyuan 列的另三个（chi.override / camximageformatutils / chifeature2）
    # 在 athens 里已经是 V2，故不收进来。
    (
        'vendor/lib64/camera/components/com.qti.node.dewarp.so',
        'vendor/lib64/vendor.qti.hardware.camera.offlinecamera-service-impl.so',
    ): blob_fixup()
        .replace_needed(
            'android.hardware.graphics.allocator-V1-ndk.so',
            'android.hardware.graphics.allocator-V2-ndk.so',
        ),

    # 实测：readelf -dW 三个库都还有 android.hardware.camera.device-V1-ndk.so
    (
        'vendor/lib64/vendor.xiaomi.hardware.camera.injection-V1-ndk.so',
        'vendor/lib64/vendor.xiaomi.hardware.camera.injection-client.so',
        'vendor/lib64/vendor.xiaomi.hardware.camera.injection-service.so',
    ): blob_fixup()
        .replace_needed(
            'android.hardware.camera.device-V1-ndk.so',
            'android.hardware.camera.device-V2-ndk.so',
        ),

    # libtinyxml2 的重定向。原厂的 vendor/lib64/libtinyxml2.so **不作为 blob 提取**
    # （两个清单都只提 libtinyxml2_1.so），依赖由构建树里带版本号的同名库满足，
    # 所以必须重定向，否则这些库在运行期找不到 SONAME。
    #
    # 列表的来历：扫 athens 原厂包中「会被提取」的全部 ELF（3189 个），取 NEEDED
    # 含 libtinyxml2.so 的 66 个，减去公共树已覆盖的 22 个、减去实测在 athens 上
    # 已是新版的，得到下面 42 个。另有 2 个属于公共树清单，见文件头待办。
    #
    # 实测命令：for f in ...; do readelf -dW $f | grep -q 'libtinyxml2\.so'; done
    (
        'odm/lib64/camera/dynamicplugins/com.xiaomi.plugin.mialgoallinone.so',
        'odm/lib64/camera/plugins/com.xiaomi.plugin.anchor.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.asd.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamawbideal.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamb2y.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamformatconvertor.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamheic.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamjpeg.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcammfnr.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcammlawb.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamtintless.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamyuveis.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamyuvreprocess.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offcamyuvsplit.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineawbideal.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineb2y.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineehdr.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineformatconvertor.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlinehdrraw2y.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineheic.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlinei2y.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlinejpeg.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlinemfnr.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlinemlawb.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlinetintless.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlinetintlesshdr.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineyuveis.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineyuvreprocess.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineyuvsplit.so',
        'odm/lib64/camera/preloadplugins/com.xiaomi.plugin.offlineyuvwarp.so',
        'odm/lib64/com.xiaomi.plugin.ecdengine.so',
        'vendor/bin/hw/vendor.qti.camera.provider-service_64',
        'vendor/lib64/camera/components/com.mi.node.fd.so',
        'vendor/lib64/camera/components/com.qti.node.fd.so',
        'vendor/lib64/com.xiaomi.stub.chi.so',
        'vendor/lib64/com.xiaomi.stubv1.camx.so',
        'vendor/lib64/hw/camera.qcom.core.so',
        'vendor/lib64/libcamxdumpinforecorder.so',
        'vendor/lib64/libcom.xiaomi.dsac.so',
        'vendor/lib64/libmicamera_aidl_provider.so',
        'vendor/lib64/libmicamera_hal_core.so',
        'vendor/lib64/libsimulation.so',
    ): blob_fixup()
        .replace_needed('libtinyxml2.so', 'libtinyxml2-v36.so'),

    # 实测：readelf -dW 该库 NEEDED 中含 libdng_sdk.so —— 这条依赖**不需要** fixup。
    # 设备树改用 MODULE_SUFFIX=_athens 消歧后，extract-utils 写入的 stem 仍是
    # libdng_sdk，安装文件名与 SONAME 都保持 libdng_sdk.so 原样，运行期按原
    # SONAME 直接命中（详见文件头 lib_fixup_athens_suffix 的说明）。

    # 实测：readelf -dW 该库 NEEDED 中**没有** libprocessgroup_shim.so。
    # 这条只做了一半的验证 —— 它是否必需取决于构建树里 libprocessgroup 的拆分，
    # 等首次构建确认（症状：libcameraopt 起不来或符号缺失）。
    (
        'vendor/lib64/libcameraopt.so',
    ): blob_fixup()
        .add_needed('libprocessgroup_shim.so'),
}

# ── 入口 ────────────────────────────────────────────────────────────────────
#
#   ExtractUtils.device(module)                                    → 只跑这棵树
#   ExtractUtils.device_with_common(module, '<common>', vendor)    → 连公共树一起跑
#
# 用后者。注意它**不是**"只做命名空间准备"：ExtractUtils.__init__ 会把两个
# module 都放进 self.__modules，而 process_modules / write_makefiles /
# write_updated_proprietary_files 全部遍历它。也就是说**跑本文件一条就覆盖了
# 两棵树**，再单独跑 sm8850-common/extract-files.py 是重复劳动。
#
# ⚠️ setup-makefiles.py 仍要**两棵树各跑一次** —— 生成 *-vendor.mk 与提取 blob
# 是两件事，device_with_common 只覆盖后者。
module = ExtractUtilsModule(
    'athens',
    'xiaomi',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == '__main__':
    utils = ExtractUtils.device_with_common(
        module, 'sm8850-common', module.vendor
    )
    utils.run()
