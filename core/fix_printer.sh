#!/bin/bash

set -e

echo "正在恢复 CUPS 默认配置文件..."
pkexec cp /usr/share/cups/cupsd.conf.default /etc/cups/cupsd.conf

echo "重启 CUPS 服务..."
pkexec systemctl restart cups

echo "CUPS 已恢复并重启完成。"
