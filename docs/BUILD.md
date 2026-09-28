# 构建

以下命令在 Linux 下执行。需要 Git、repo、Git LFS、Python 3 和 PixelOS 构建依赖。
相机脚本另需 Android SDK Build Tools 37.0.0；编译使用源码树自带的 JDK 21。

先设置几个本地路径：

```bash
export DEVICE_REPO=/path/to/android_device_xiaomi_athens
export TREE=/path/to/pixelos
export STOCK=/path/to/extracted-stock
export RELEASE_DIR=/path/to/releases
```

## 同步源码

在空源码目录中初始化：

```bash
mkdir -p "$TREE"
cd "$TREE"
repo init -u https://github.com/PixelOS-AOSP/android_manifest \
  -b c16cfd0c95c5c3d7f5f2ef85b5b3140787db2035 --git-lfs
cp "$DEVICE_REPO/manifests/pixelos-r12-locked.xml" .repo/manifests/athens-r12.xml
repo init -m athens-r12.xml
repo sync -c -j12
mkdir -p device/xiaomi
git clone "$DEVICE_REPO" device/xiaomi/athens
```

锁定清单已经包含 SM8850 项目。`sm8850-platform.xml` 仅供以后换基线时参考，不要重复加载。

## 应用补丁

在源码树根目录执行：

```bash
python3 device/xiaomi/athens/tools/apply-patches.py --tree "$PWD" --check
python3 device/xiaomi/athens/tools/apply-patches.py --tree "$PWD"
```

脚本核对 `patches/series.json` 中的提交号，全部检查通过后再应用补丁。
重复执行会跳过已应用的补丁。

## 提取原厂文件

使用 athens **OS3.0.306.0.WPICNXM**。展开后的 `$STOCK` 下应有 `vendor/`、`odm/`、
`product/`、`system_ext/` 等目录，文件路径与 `proprietary-files.txt` 对应。

```bash
cd device/xiaomi/athens
./extract-files.py "$STOCK"
cd ../../..
```

这个入口同时处理 athens 和 sm8850-common，生成两个 `vendor/xiaomi/` 目录。
内核包放到 `device/xiaomi/athens-kernel`，所需文件见 [KERNEL.md](KERNEL.md)。

## 准备小米相机

脚本适用于原厂 6.3.008710.8。`KEY` 和 `CERT` 使用与 ROM 相同的平台签名：

```bash
export KEY=/path/to/platform.pk8
export CERT=/path/to/platform.x509.pem
python3 device/xiaomi/athens/tools/prepare-miui-camera.py \
  --tree "$PWD" \
  --stock-apk "$STOCK/product/priv-app/MiuiCamera/MiuiCamera.apk" \
  --build-tools "$ANDROID_SDK_ROOT/build-tools/37.0.0" \
  --key "$KEY" --cert "$CERT" \
  --output device/xiaomi/athens/camera/MiuiCamera.apk
```

AOSP 开发测试密钥在 `build/make/target/product/security/`。
使用自己的发布密钥时，也要配置 ROM 签名。IFAAService 会随源码编译，不用单独放 APK。

## 编译

```bash
TREE="$PWD" JOBS=12 bash device/xiaomi/athens/tools/build.sh pixelos
```

完成后导出独立副本；把下面的文件名替换为实际输出：

```bash
python3 device/xiaomi/athens/tools/export-candidate.py \
  out/target/product/athens/PixelOS_athens-17.0-YYYYMMDD-HHMM.zip \
  "$RELEASE_DIR" --revision r12
```

导出文件名使用包内 UTC 时间。独立副本不会随下一次构建输出一起被覆盖。

原工作区的 r12 已编译通过。这份源码整理还没有从空目录完整重编；内核输入目前仍需
手动准备，见 [KERNEL.md](KERNEL.md)。
