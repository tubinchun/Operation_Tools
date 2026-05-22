#!/bin/bash

# Kylin / openKylin 清理服务自启动管理脚本
# 支持开启/关闭开机自启动、查看运行状态、配置清理频率

SERVICE_NAME="kylin-clean-tools.service"
CONFIG_FILE="/opt/kylin-clean/config.sh"

# 默认配置
DEFAULT_CLEANUP_HOURS="8 9 10 11 12 13 14 15 16 17 18"
DEFAULT_SHUTDOWN_TIME="23:00"
DEFAULT_SHUTDOWN_ENABLED="yes"

# 加载配置
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    else
        CLEANUP_HOURS="$DEFAULT_CLEANUP_HOURS"
        SHUTDOWN_TIME="$DEFAULT_SHUTDOWN_TIME"
        SHUTDOWN_ENABLED="$DEFAULT_SHUTDOWN_ENABLED"
    fi
}

# 保存配置
save_config() {
    sudo tee "$CONFIG_FILE" > /dev/null << EOF
# Kylin / openKylin 清理工具配置文件
# 清理执行时间（小时，空格分隔）
CLEANUP_HOURS="$CLEANUP_HOURS"
# 关机时间
SHUTDOWN_TIME="$SHUTDOWN_TIME"
# 是否启用定时关机 (yes/no)
SHUTDOWN_ENABLED="$SHUTDOWN_ENABLED"
EOF
    echo "配置已保存。"
}

show_status() {
    clear
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║     Kylin / openKylin 自动清理服务 - 管理控制台            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 检查是否安装了服务
    if ! systemctl list-unit-files 2>/dev/null | grep -q "^$SERVICE_NAME"; then
        echo "  ⚠ 状态: [未安装]"
        echo "  请先安装 DEB 包后再使用此工具。"
        echo ""
        read -p "按回车键退出..."
        exit 1
    fi

    # 检查是否自启动
    if systemctl is-enabled "$SERVICE_NAME" &>/dev/null; then
        ENABLED_STATUS="✔ 已开启"
        ENABLED_COLOR="\e[32m"
    else
        ENABLED_STATUS="✘ 已关闭"
        ENABLED_COLOR="\e[31m"
    fi

    # 检查是否正在运行
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        ACTIVE_STATUS="✔ 运行中"
        ACTIVE_COLOR="\e[32m"
        # 获取运行时间
        UPTIME=$(systemctl show "$SERVICE_NAME" --property=ActiveEnterTimestamp 2>/dev/null | cut -d'=' -f2)
    else
        ACTIVE_STATUS="✘ 已停止"
        ACTIVE_COLOR="\e[31m"
        UPTIME=""
    fi

    echo "  ┌─────────────────────────────────────────────────────────┐"
    echo "  │ 服务状态                                                │"
    echo "  ├─────────────────────────────────────────────────────────┤"
    echo -e "  │  开机自启动:  $ENABLED_COLOR$ENABLED_STATUS\e[0m                                     │"
    echo -e "  │  当前运行状态: $ACTIVE_COLOR$ACTIVE_STATUS\e[0m                                     │"
    if [ -n "$UPTIME" ]; then
        echo "  │  启动时间:    $UPTIME  │"
    fi
    echo "  └─────────────────────────────────────────────────────────┘"
    echo ""
    
    # 加载并显示当前配置
    load_config
    echo "  ┌─────────────────────────────────────────────────────────┐"
    echo "  │ 清理计划配置                                            │"
    echo "  ├─────────────────────────────────────────────────────────┤"
    echo "  │  定时清理: 每天 ${CLEANUP_HOURS// /、} 点整执行         │"
    echo "  │  清理前提醒: 提前 5 分钟                                │"
    if [ "$SHUTDOWN_ENABLED" = "yes" ]; then
        echo "  │  定时关机: $SHUTDOWN_TIME (提前 10 分钟提醒)             │"
    else
        echo "  │  定时关机: 已禁用                                       │"
    fi
    echo "  └─────────────────────────────────────────────────────────┘"
    echo ""
}

toggle_service() {
    if systemctl is-enabled "$SERVICE_NAME" &>/dev/null; then
        echo "正在关闭开机自启动..."
        sudo systemctl disable "$SERVICE_NAME"
        sudo systemctl stop "$SERVICE_NAME"
        echo "✔ 已关闭自启动并停止服务。"
    else
        echo "正在开启开机自启动..."
        sudo systemctl enable "$SERVICE_NAME"
        sudo systemctl start "$SERVICE_NAME"
        echo "✔ 已开启自启动并启动服务。"
    fi
}

view_logs() {
    echo ""
    echo "═══════════════════ 最近日志 (最新 20 条) ═══════════════════"
    echo ""
    if [ -f "/opt/kylin-clean/cleanup_and_shutdown.log" ]; then
        tail -n 20 /opt/kylin-clean/cleanup_and_shutdown.log
    elif [ -f "/tmp/kylin-clean.log" ]; then
        tail -n 20 /tmp/kylin-clean.log
    else
        sudo journalctl -u kylin-clean-tools -n 20 --no-pager 2>/dev/null || echo "暂无日志。"
    fi
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
}

# 主菜单
main_menu() {
    while true; do
        show_status
        
        echo "  操作菜单:"
        echo "  ─────────────────────────────────────────────────────────"
        echo "  1. 切换自启动状态 (开启/关闭)"
        echo "  2. 立即启动服务"
        echo "  3. 立即停止服务"
        echo "  4. 重启服务"
        echo "  5. 查看运行日志"
        echo "  6. 立即执行深度清理 (彻底清空目录)"
        echo "  7. 立即执行手动清理 (按后缀名清理)"
        echo "  q. 退出"
        echo ""
        read -p "  请选择操作 [1-7/q]: " choice

        case $choice in
            1)
                toggle_service
                sleep 2
                ;;
            2)
                echo "正在启动服务..."
                sudo systemctl start "$SERVICE_NAME"
                echo "✔ 服务已启动。"
                sleep 2
                ;;
            3)
                echo "正在停止服务..."
                sudo systemctl stop "$SERVICE_NAME"
                echo "✔ 服务已停止。"
                sleep 2
                ;;
            4)
                echo "正在重启服务..."
                sudo systemctl restart "$SERVICE_NAME"
                echo "✔ 服务已重启。"
                sleep 2
                ;;
            5)
                view_logs
                read -p "按回车键返回菜单..."
                ;;
            6)
                echo "正在执行深度清理 (彻底清空，请稍候)..."
                sudo python3 /opt/kylin-clean/clean_linux.py --once
                echo "✔ 深度清理执行任务已触发。"
                sleep 2
                ;;
            7)
                echo "正在执行手动清理 (扫描特定后缀)..."
                sudo bash /opt/kylin-clean/cleanup_user_data.sh
                echo "✔ 手动清理已完成。"
                sleep 2
                ;;
            q|Q)
                echo "退出。"
                exit 0
                ;;
            *)
                echo "无效选项，请重新选择。"
                sleep 1
                ;;
        esac
    done
}

# 运行主菜单
main_menu
