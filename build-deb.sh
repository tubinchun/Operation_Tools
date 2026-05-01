#!/bin/bash
# build-deb.sh - 构建Debian安装包
# 用法: ./build-deb.sh [arm64|i386|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
DEB_DIR="$PROJECT_DIR/debian/pkg"
OUTPUT_DIR="$PROJECT_DIR/output"
PKG_NAME="kylin-system-tools"
VERSION="1.0.0"
ARCH="${1:-arm64}"

echo "========================================"
echo "  银河麒麟运维管理工具 - DEB构建脚本"
echo "========================================"
echo ""

# 清理旧文件
echo "[1/6] 清理旧构建文件..."
rm -rf "$DEB_DIR"
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# 创建DEB目录结构
echo "[2/6] 创建DEB目录结构..."
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/kylin-system-tools/server"
mkdir -p "$DEB_DIR/usr/share/kylin-system-tools/client"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$DEB_DIR/lib/systemd/system"
mkdir -p "$DEB_DIR/etc/kylin-system-tools"
mkdir -p "$DEB_DIR/var/log/kylin-system-tools"

# 复制DEBIAN配置
echo "[3/6] 复制DEBIAN配置..."
cp "$PROJECT_DIR/debian/kylin-system-tools/DEBIAN/control" "$DEB_DIR/DEBIAN/"
cp "$PROJECT_DIR/debian/kylin-system-tools/DEBIAN/postinst" "$DEB_DIR/DEBIAN/"
cp "$PROJECT_DIR/debian/kylin-system-tools/DEBIAN/prerm" "$DEB_DIR/DEBIAN/"
cp "$PROJECT_DIR/debian/kylin-system-tools/DEBIAN/postrm" "$DEB_DIR/DEBIAN/"
cp "$PROJECT_DIR/debian/kylin-system-tools/DEBIAN/conffiles" "$DEB_DIR/DEBIAN/"

# 设置脚本权限
chmod 755 "$DEB_DIR/DEBIAN/postinst"
chmod 755 "$DEB_DIR/DEBIAN/prerm"
chmod 755 "$DEB_DIR/DEBIAN/postrm"

# 复制启动脚本
echo "[4/6] 复制启动脚本..."
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/bin/kylintools-server" "$DEB_DIR/usr/bin/"
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/bin/kylintools-client" "$DEB_DIR/usr/bin/"
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/bin/kylintools" "$DEB_DIR/usr/bin/"
chmod 755 "$DEB_DIR/usr/bin/kylintools"*
rm -f "$DEB_DIR/usr/bin/kylintools-"*

# 复制systemd服务
cp "$PROJECT_DIR/debian/kylin-system-tools/lib/systemd/system/kylin-system-tools.service" "$DEB_DIR/lib/systemd/system/"

# 复制桌面图标
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/share/applications/kylin-system-tools.desktop" "$DEB_DIR/usr/share/applications/"
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/share/applications/kylin-system-tools-server.desktop" "$DEB_DIR/usr/share/applications/"
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/share/icons/hicolor/256x256/apps/kylin-system-tools.svg" "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/"

# 复制配置文件
cp "$PROJECT_DIR/debian/kylin-system-tools/etc/kylin-system-tools/config.json" "$DEB_DIR/etc/kylin-system-tools/"

# 复制源代码
echo "[5/6] 复制源代码..."
cp "$PROJECT_DIR/server/server.py" "$DEB_DIR/usr/share/kylin-system-tools/server/"
cp "$PROJECT_DIR/server/__init__.py" "$DEB_DIR/usr/share/kylin-system-tools/server/"
cp "$PROJECT_DIR/server/__main__.py" "$DEB_DIR/usr/share/kylin-system-tools/server/"
cp "$PROJECT_DIR/server/mock_server.py" "$DEB_DIR/usr/share/kylin-system-tools/server/"

cp "$PROJECT_DIR/client/client.py" "$DEB_DIR/usr/share/kylin-system-tools/client/"
cp "$PROJECT_DIR/client/__init__.py" "$DEB_DIR/usr/share/kylin-system-tools/client/"
cp "$PROJECT_DIR/client/__main__.py" "$DEB_DIR/usr/share/kylin-system-tools/client/"
cp "$PROJECT_DIR/client/apple_ui.py" "$DEB_DIR/usr/share/kylin-system-tools/client/"
cp "$PROJECT_DIR/client/gui.py" "$DEB_DIR/usr/share/kylin-system-tools/client/"

cp "$PROJECT_DIR/setup.py" "$DEB_DIR/usr/share/kylin-system-tools/"

# 设置Python脚本权限
chmod 644 "$DEB_DIR/usr/share/kylin-system-tools/server/"*.py
chmod 644 "$DEB_DIR/usr/share/kylin-system-tools/client/"*.py
chmod 644 "$DEB_DIR/usr/share/kylin-system-tools/setup.py"

# 创建日志目录占位
touch "$DEB_DIR/var/log/kylin-system-tools/.gitkeep"

# 修改control文件中的架构
if [ "$ARCH" = "all" ]; then
    sed -i 's/Architecture: arm64/Architecture: all/' "$DEB_DIR/DEBIAN/control"
else
    sed -i "s/Architecture: arm64/Architecture: $ARCH/" "$DEB_DIR/DEBIAN/control"
fi

# 构建DEB包
echo "[6/6] 构建DEB包..."
DEB_FILE="$OUTPUT_DIR/${PKG_NAME}_${VERSION}_${ARCH}.deb"

dpkg-deb --build "$DEB_DIR" "$DEB_FILE"

echo ""
echo "========================================"
echo "  构建完成！"
echo "========================================"
echo ""
echo "DEB包位置: $DEB_FILE"
echo "包大小: $(du -h "$DEB_FILE" | cut -f1)"
echo ""
echo "安装方法:"
echo "  sudo dpkg -i $DEB_FILE"
echo "  sudo apt-get install -f  # 如有依赖问题"
echo ""
echo "卸载方法:"
echo "  sudo dpkg -P kylin-system-tools"
echo ""
