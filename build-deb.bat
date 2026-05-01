@echo off
chcp 65001 >nul
echo ========================================
echo   银河麒麟运维管理工具 - DEB构建说明
echo ========================================
echo.
echo 此脚本需要在Linux系统上运行
echo.
echo 在Linux麒麟系统上执行以下命令:
echo.
echo   1. 给脚本添加执行权限:
echo      chmod +x build-deb.sh
echo.
echo   2. 构建ARM64版本:
echo      ./build-deb.sh arm64
echo.
echo   3. 构建完成后安装:
echo      sudo dpkg -i output/kylin-system-tools_1.0.0_arm64.deb
echo.
echo   4. 如有依赖问题:
echo      sudo apt-get install -f
echo.
echo 安装后启动:
echo   - 服务端: sudo kylintools-server
echo   - 客户端: kylintools-client
echo   - 快捷启动: kylintools
echo.
pause
