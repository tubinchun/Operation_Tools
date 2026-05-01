#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install_server() {
    echo "安装服务端..."
    cd "$SCRIPT_DIR"
    python3 -m pip install -e .
    echo "服务端已安装，使用 'sudo kylintools-server' 启动"
}

uninstall() {
    echo "卸载中..."
    python3 -m pip uninstall kylin-system-tools -y
    echo "卸载完成"
}

case "$1" in
    install)
        install_server
        ;;
    uninstall)
        uninstall
        ;;
    *)
        echo "用法: $0 {install|uninstall}"
        exit 1
        ;;
esac
