# 内核输入

当前使用原厂内核 `6.12.69-android16-6-g0d80ee00f747-ab15461283-4k`，
来自 athens OS3.0.306.0.WPICNXM。

将本地内核包放在 `device/xiaomi/athens-kernel`，目录如下：

| 路径 | 来源 |
|---|---|
| `kernel` | boot.img 的 kernel 段 |
| `dtbo.img` | 原厂 dtbo.img |
| `dtb/raw01.dtb` … `dtb/raw12.dtb` | vendor_boot.img 的串联 FDT，按原始顺序拆分 |
| `vendor_ramdisk/` | vendor_boot ramdisk 中的 lib/modules |
| `vendor_dlkm/` | vendor_dlkm 镜像中的 lib/modules |
| `system_dlkm/` | system_dlkm 中该内核版本的模块目录内容 |
| `system_dlkm_flatten/` | system_dlkm 的 flatten/lib/modules |
| `kernel-headers.tar.gz` | UAPI 头，归档根为 usr/include |

boot/vendor_boot 可用 AOSP `unpack_bootimg` 拆分；super 用 `simg2img`、`lpunpack`，
EROFS 镜像用 `fsck.erofs`。FDT 按大端 magic `0xd00dfeed` 和 totalsize 定位。
保留 `modules.load`、`modules.load.recovery`、`modules.order` 等加载清单。

UAPI 头来自 GKI `android16-6.12` 和 QTI SM8850：

- https://android.googlesource.com/kernel/common
- https://github.com/LineageOS/android_kernel_qcom_sm8850

仓库不含原厂内核、模块或头文件包。现有头文件包的组装过程还没整理成自动脚本，
这部分目前需要手动准备。
