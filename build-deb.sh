#!/bin/bash
# build-deb.sh - 构建Debian安装包
# 用法: ./build-deb.sh [arm64|i386|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
DEB_DIR="$PROJECT_DIR/debian/pkg"
OUTPUT_DIR="$PROJECT_DIR/output"
PKG_NAME="kylin-system-tools"
VERSION="1.0.3"
ARCH="${1:-arm64}"

echo "========================================"
echo "  麒麟运维百宝箱 - DEB构建脚本"
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
mkdir -p "$DEB_DIR/usr/share/kylin-system-tools/core"
mkdir -p "$DEB_DIR/usr/share/kylin-system-tools/ui"
mkdir -p "$DEB_DIR/usr/share/kylin-system-tools/tools/usb_fix_tool"
mkdir -p "$DEB_DIR/usr/share/kylin-system-tools/tools/pxe"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$DEB_DIR/usr/share/polkit-1/actions"
mkdir -p "$DEB_DIR/lib/systemd/system"
mkdir -p "$DEB_DIR/etc/kylin-system-tools"
mkdir -p "$DEB_DIR/var/log/kylin-system-tools"
mkdir -p "$DEB_DIR/var/lib/kylin-system-tools/pxe/iso"
mkdir -p "$DEB_DIR/etc/kylin-system-tools/pxe"
mkdir -p "$DEB_DIR/opt/kylin-clean"

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
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/bin/kylintools" "$DEB_DIR/usr/bin/"
chmod 755 "$DEB_DIR/usr/bin/kylintools"
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/bin/kylin-usb-tool" "$DEB_DIR/usr/bin/"
chmod 755 "$DEB_DIR/usr/bin/kylin-usb-tool"

# 复制桌面图标
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/share/applications/kylin-system-tools.desktop" "$DEB_DIR/usr/share/applications/"
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/share/icons/hicolor/256x256/apps/kylin-system-tools.svg" "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/"
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/share/icons/hicolor/256x256/apps/usb-fix-tool.svg" "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/"
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/share/icons/hicolor/256x256/apps/kylin-cleanup.svg" "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/"
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/share/icons/hicolor/256x256/apps/kylin-cleanup-settings.svg" "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/"
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/share/icons/hicolor/256x256/apps/kylin-cleanup.png" "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/"
cp "$PROJECT_DIR/debian/kylin-system-tools/usr/share/polkit-1/actions/com.kylin.system-tools.policy" "$DEB_DIR/usr/share/polkit-1/actions/"

# 复制配置文件
cp "$PROJECT_DIR/debian/kylin-system-tools/etc/kylin-system-tools/config.json" "$DEB_DIR/etc/kylin-system-tools/"

# 复制源代码
echo "[5/6] 复制源代码..."
cp "$PROJECT_DIR/kylintools.py" "$DEB_DIR/usr/share/kylin-system-tools/"

# 复制核心模块
cp "$PROJECT_DIR/core/__init__.py" "$DEB_DIR/usr/share/kylin-system-tools/core/"
cp "$PROJECT_DIR/core/commands.py" "$DEB_DIR/usr/share/kylin-system-tools/core/"
cp "$PROJECT_DIR/core/local_client.py" "$DEB_DIR/usr/share/kylin-system-tools/core/"
cp "$PROJECT_DIR/core/auth_service.py" "$DEB_DIR/usr/share/kylin-system-tools/core/"

# 复制UI模块
cp "$PROJECT_DIR/ui/__init__.py" "$DEB_DIR/usr/share/kylin-system-tools/ui/"
cp "$PROJECT_DIR/ui/main_window.py" "$DEB_DIR/usr/share/kylin-system-tools/ui/"

# 复制U盘工具箱
cp "$PROJECT_DIR/tools/usb_fix_tool/usb_tool.py" "$DEB_DIR/usr/share/kylin-system-tools/tools/usb_fix_tool/"
cp "$PROJECT_DIR/tools/usb_fix_tool/ui_assets.py" "$DEB_DIR/usr/share/kylin-system-tools/tools/usb_fix_tool/"
cp "$PROJECT_DIR/tools/usb_fix_tool/ventoy-1.1.12-linux.tar.gz" "$DEB_DIR/usr/share/kylin-system-tools/tools/usb_fix_tool/"

# 复制PXE工具箱
cp "$PROJECT_DIR/tools/pxe/__init__.py" "$DEB_DIR/usr/share/kylin-system-tools/tools/pxe/"
cp "$PROJECT_DIR/tools/pxe/pxe_server.py" "$DEB_DIR/usr/share/kylin-system-tools/tools/pxe/"
cp "$PROJECT_DIR/tools/pxe/pxe_ui.py" "$DEB_DIR/usr/share/kylin-system-tools/tools/pxe/"
cp -r "$PROJECT_DIR/tools/pxe/config" "$DEB_DIR/usr/share/kylin-system-tools/tools/pxe/"
cp -r "$PROJECT_DIR/tools/pxe/netboot" "$DEB_DIR/usr/share/kylin-system-tools/tools/pxe/"
cp -r "$PROJECT_DIR/tools/pxe/scripts" "$DEB_DIR/usr/share/kylin-system-tools/tools/pxe/"
cp -r "$PROJECT_DIR/tools/pxe/services" "$DEB_DIR/usr/share/kylin-system-tools/tools/pxe/"

# 复制PXE默认配置文件
cp "$PROJECT_DIR/tools/pxe/config/config.json" "$DEB_DIR/etc/kylin-system-tools/pxe/config.json"

# 设置Python脚本权限
chmod 644 "$DEB_DIR/usr/share/kylin-system-tools/"*.py
chmod 644 "$DEB_DIR/usr/share/kylin-system-tools/core/"*.py
chmod 644 "$DEB_DIR/usr/share/kylin-system-tools/ui/"*.py
chmod 644 "$DEB_DIR/usr/share/kylin-system-tools/tools/usb_fix_tool/"*.py
chmod 644 "$DEB_DIR/usr/share/kylin-system-tools/tools/usb_fix_tool/"*.tar.gz
chmod 644 "$DEB_DIR/usr/share/kylin-system-tools/tools/pxe/"*.py
chmod 644 "$DEB_DIR/usr/share/kylin-system-tools/tools/pxe/config/"*
chmod 644 "$DEB_DIR/usr/share/kylin-system-tools/tools/pxe/scripts/"*
chmod 755 "$DEB_DIR/usr/share/kylin-system-tools/tools/pxe/scripts/"*.sh
chmod 644 "$DEB_DIR/usr/share/kylin-system-tools/tools/pxe/services/"*.py
chmod 644 "$DEB_DIR/usr/share/polkit-1/actions/"*.policy

# 创建日志目录占位
touch "$DEB_DIR/var/log/kylin-system-tools/.gitkeep"

# 复制kylin-clean-tools服务文件
echo "[5.5/6] 复制kylin-clean-tools文件..."
cp "$PROJECT_DIR/service/kylin-clean-tools.service" "$DEB_DIR/lib/systemd/system/"
cp "$PROJECT_DIR/tools/kylin_clean/clean_linux.py" "$DEB_DIR/opt/kylin-clean/"
cp "$PROJECT_DIR/tools/kylin_clean/notify_clean_linux.py" "$DEB_DIR/opt/kylin-clean/"
cp "$PROJECT_DIR/tools/kylin_clean/license_manager.py" "$DEB_DIR/opt/kylin-clean/"
cp "$PROJECT_DIR/tools/kylin_clean/popup_warning.py" "$DEB_DIR/opt/kylin-clean/"
cp "$PROJECT_DIR/tools/kylin_clean/ui_assets.py" "$DEB_DIR/opt/kylin-clean/"
cp "$PROJECT_DIR/tools/kylin_clean/settings_ui.py" "$DEB_DIR/opt/kylin-clean/"
cp "$PROJECT_DIR/tools/kylin_clean/settings_ui_qt.py" "$DEB_DIR/opt/kylin-clean/"
cp "$PROJECT_DIR/tools/kylin_clean/kylin-cleanup.svg" "$DEB_DIR/opt/kylin-clean/"
cp "$PROJECT_DIR/tools/kylin_clean/kylin-cleanup-settings.svg" "$DEB_DIR/opt/kylin-clean/"
cp "$PROJECT_DIR/tools/kylin_clean/cleanup_user_data.sh" "$DEB_DIR/opt/kylin-clean/"
cp "$PROJECT_DIR/tools/kylin_clean/service_toggle.sh" "$DEB_DIR/opt/kylin-clean/"
mkdir -p "$DEB_DIR/opt/kylin-clean/schedule"
cp "$PROJECT_DIR/tools/kylin_clean/schedule/__init__.py" "$DEB_DIR/opt/kylin-clean/schedule/"
cp "$PROJECT_DIR/tools/kylin_clean/schedule/py.typed" "$DEB_DIR/opt/kylin-clean/schedule/"

# 创建配置目录
mkdir -p "$DEB_DIR/etc/kylin-clean"
touch "$DEB_DIR/etc/kylin-clean/config.sh"

# 设置kylin-clean-tools文件权限
chmod 644 "$DEB_DIR/lib/systemd/system/kylin-clean-tools.service"
chmod 644 "$DEB_DIR/opt/kylin-clean/"*.py
chmod 644 "$DEB_DIR/opt/kylin-clean/"*.svg
chmod 644 "$DEB_DIR/opt/kylin-clean/schedule/"*.py
chmod 755 "$DEB_DIR/opt/kylin-clean/"*.sh
chmod 755 "$DEB_DIR/etc/kylin-clean"
chmod 644 "$DEB_DIR/etc/kylin-clean/config.sh"

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
echo "运行方法:"
echo "  kylintools"
echo ""
echo "卸载方法:"
echo "  sudo dpkg -P kylin-system-tools"
echo ""
