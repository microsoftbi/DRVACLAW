#!/bin/bash
# 构建「驾驶智陪工作台 · 服务控制台」macOS 应用（SwiftUI 原生）
# 依赖：Xcode Command Line Tools（swiftc / xcrun），无需完整 Xcode
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="$ROOT/DesktopApp/build/驾驶智陪工作台.app"
BIN="$APP/Contents/MacOS/DrvaclawLauncher"

echo "项目根目录: $ROOT"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

echo "编译 SwiftUI 应用..."
swiftc -O -swift-version 5 -parse-as-library \
    -target arm64-apple-macosx13.0 \
    -sdk "$(xcrun --show-sdk-path)" \
    "$ROOT/DesktopApp/Sources/AppMain.swift" \
    -o "$BIN" \
    -framework SwiftUI -framework AppKit

cp "$ROOT/DesktopApp/Info.plist" "$APP/Contents/Info.plist"
printf 'APPL????' > "$APP/Contents/PkgInfo"

echo "本地签名（ad-hoc）..."
codesign --force --sign - "$APP" >/dev/null 2>&1 || true

echo ""
echo "构建完成: $APP"
echo "启动方式: open \"$APP\""
echo "首次打开如被系统拦截，请右键点击应用 → 选择「打开」。"
