# Redmi K100 Pro — Android 17 设备树

Redmi K100 Pro（athens）的设备树，平台为 Qualcomm SM8850 / canoe。
放到源码树的 `device/xiaomi/athens` 下使用。

共享设备树分支为 `android-17`，用于构建 PixelOS、Evolution X 和 Project Infinity X。
厂商文件来自国行 HyperOS 4 `OS4.0.6.0.XPICNXM` 线刷包。

## 构建依赖

在配套的 [athens_manifest](https://github.com/YuanHuakk/athens_manifest) 仓库选择对应分支，
按该分支的 `docs/BUILD.md` 同步源码和准备构建输入。

| ROM | athens_manifest 分支 | ROM 上游分支 | 构建产品 |
| --- | --- | --- | --- |
| PixelOS | `pixelos-17` | `seventeen` | `custom_athens` |
| Evolution X | `evox-17` | `cnb` | `lineage_athens` |
| Project Infinity X | `infinity-x-17` | `17` | `infinity_athens` |

本仓库保留设备配置、资源覆盖、SELinux 规则和专有文件提取脚本。
vendor 文件、预编译内核、小米相机和 Pixel Tips APK 需另行准备。

## 当前配置

| 项目                   | 值         |
| ---------------------- | ---------- |
| System 安全补丁        | 由 ROM 的上游构建配置决定 |
| Vendor / Boot 安全补丁 | 2026-10-01 |
| SELinux                | Enforcing |
| 构建类型               | 默认 `user`，可选 `userdebug` |

启动诊断服务仅包含在 `userdebug` / `eng` 中，日志位于 `/metadata/athens-diag/logs`。

## 来源

设备适配基于 PixelOS、LineageOS 和 AlexZorzi 的 SM8850 公共树。
来源及许可见 [NOTICE.md](NOTICE.md)。
