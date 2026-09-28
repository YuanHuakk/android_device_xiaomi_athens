# Redmi K100 Pro — PixelOS

Redmi K100 Pro（athens）的 PixelOS 设备树，平台为 Qualcomm SM8850 / canoe。
放到源码树的 `device/xiaomi/athens` 下使用。

当前代码对应 r12，Android 17，厂商文件来自 OS3.0.306.0.WPICNXM。

## 设备状态

已测试：

- 系统启动、指纹录入和解锁
- 扬声器、音量调节、录音、电话及蓝牙通话
- 传统蓝牙 / LE Audio 音乐播放、自动亮度
- 状态栏和半展开控制中心布局
- 小米相机主摄、超广角、长焦、前摄拍照及基础录像
- 支付宝指纹支付设置
- 快充状态显示、有线及无线反向充电

无线充电接收和相机高级模式还没测。r12 已编译通过，整包尚未刷机复验。
具体测试范围见 [STATUS.md](docs/STATUS.md)。

## 构建

[构建步骤](docs/BUILD.md) · [内核输入](docs/KERNEL.md)

仓库包含设备配置、提取规则，以及 17 个上游项目的补丁。
`manifests/pixelos-r12-locked.xml` 记录本次构建使用的源码版本。

vendor 文件、预编译内核和小米相机 APK 需要自行准备，不在仓库里。
相机处理脚本位于 `tools/prepare-miui-camera.py`。

## 当前配置

| 项目 | 值 |
|---|---|
| System 安全补丁 | 2026-09-01 |
| Vendor / Boot 安全补丁 | 2026-08-01 |
| SELinux | Permissive |
| 构建类型 | userdebug |

保留了启动诊断服务，日志位于 `/metadata/athens-diag/logs`。

## 来源

设备适配基于 PixelOS、LineageOS 和 AlexZorzi 的 SM8850 公共树。
来源及许可见 [NOTICE.md](NOTICE.md)。
