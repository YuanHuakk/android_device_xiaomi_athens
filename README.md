# Redmi K100 Pro — PixelOS

Redmi K100 Pro（athens）的设备树，平台为 Qualcomm SM8850 / canoe。
放到源码树的 `device/xiaomi/athens` 下使用。

当前适配版本为 r12 / Android 17，厂商文件来自 OS3.0.306.0.WPICNXM。

## 构建依赖

配套的 `athens_manifest` 仓库保存源码清单、17 个上游项目的补丁、构建工具和测试记录。
构建步骤见该仓库的 `docs/BUILD.md`。两个仓库目前仅在本地整理，尚未发布。

本仓库保留设备配置、资源覆盖、SELinux 规则和专有文件提取脚本。
vendor 文件、预编译内核和小米相机 APK 需另行准备。

## 当前配置

| 项目 | 值 |
|---|---|
| System 安全补丁 | 2026-09-01 |
| Vendor / Boot 安全补丁 | 2026-08-01 |
| SELinux | Permissive |
| 构建类型 | userdebug |

保留了启动诊断服务，日志位于 `/metadata/athens-diag/logs`。
功能验证范围见 `athens_manifest` 的 `docs/STATUS.md`。

## 来源

设备适配基于 PixelOS、LineageOS 和 AlexZorzi 的 SM8850 公共树。
来源及许可见 [NOTICE.md](NOTICE.md)。
