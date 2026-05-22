#!/bin/bash

# 创建临时目录
TMP_DIR=$(mktemp -d)
CONFIG_DIR="$TMP_DIR/config"
LOG_DIR="$TMP_DIR/log"

mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"

# 复制配置文件
cp /etc/kylin-system-tools/pxe/config.json "$CONFIG_DIR/"
cp /etc/kylin-system-tools/pxe/leases.json "$CONFIG_DIR/"
cp /etc/kylin-system-tools/pxe/blackwhitelist.json "$CONFIG_DIR/"

# 设置环境变量
export KYLIN_CONFIG_DIR="$CONFIG_DIR"
export KYLIN_LOG_DIR="$LOG_DIR"

# 进入源码目录并启动服务
cd /home/Lyle_Tu/下载/Operation_Tools-1.3/Operation_Tools-1.3
python3 -c "
import sys
sys.path.insert(0, '/home/Lyle_Tu/下载/Operation_Tools-1.3/Operation_Tools-1.3')

import os
os.environ['KYLIN_CONFIG_DIR'] = '$CONFIG_DIR'
os.environ['KYLIN_LOG_DIR'] = '$LOG_DIR'

from tools.pxe.pxe_server import PXECommands
server = PXECommands()
result = server.start_pxe_services()
print(result)
"