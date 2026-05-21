#!/bin/bash

# 用户数据清理工具 (Kylin / openKylin 适配版)
# 程序作者: Genwang Ye
# 兼容 UKUI 桌面环境
# 支持清理完成桌面通知

echo "正在清除用户数据，请稍等......"
echo "基于当前登录用户进行清理..."
echo ""

# 版权/遥测系统拦截
if [ -f "/opt/kylin-clean/license_manager.py" ]; then
    python3 /opt/kylin-clean/license_manager.py
    if [ $? -ne 0 ]; then
        echo "[拦截] 此设备的增强版清理助手尚未激活，或验证已过期。"
        echo "请从系统应用菜单或开始菜单打开【麒麟清理工具设置】进行在线/扫码激活。"
        if command -v notify-send &> /dev/null; then
            notify-send -u critical "麒麟清理助手拦截" "此设备尚未授权激活，请打开设置中心使用。"
        fi
        exit 1
    fi
fi

# 获取当前用户家目录
USER_HOME=$HOME

# 尝试加载全局配置文件，以读取精细化开关
CONFIG_FILE="/opt/kylin-clean/config.sh"
CLEANUP_SYS_THUMBNAILS="no"
CLEANUP_SYS_APT="no"
CLEANUP_SYS_JOURNAL="no"

if [ -f "$CONFIG_FILE" ]; then
    # 只加载这几个特定变量，防止被恶意注入
    source <(grep -E '^(CLEANUP_SYS_THUMBNAILS|CLEANUP_SYS_APT|CLEANUP_SYS_JOURNAL)=' "$CONFIG_FILE")
fi

# 定义浏览器缓存目录
BROWSER_CACHES=(
    "$USER_HOME/.cache/mozilla/firefox"
    "$USER_HOME/.cache/chromium/Default/Cache"
    "$USER_HOME/.cache/google-chrome/Default/Cache"
    "$USER_HOME/.cache/microsoft-edge/Default/Cache"
    "$USER_HOME/.cache/BraveSoftware/Brave-Browser/Default/Cache"
    "$USER_HOME/.cache/360se"
    "$USER_HOME/.cache/qaxbrowser"
)

# 利用 XDG 规范获取标准目录路径，提供跨语言支持方案
get_xdg_dir() {
    local xdg_name=$1
    local fallback_en=$2
    local fallback_cn=$3
    
    local path=""
    if command -v xdg-user-dir &> /dev/null; then
        path=$(xdg-user-dir "$xdg_name" 2>/dev/null)
    fi
    
    # 如果 xdg-user-dir 失败或返回的是家目录根路径，则使用 fallback 探测
    if [ -z "$path" ] || [ "$path" = "$USER_HOME" ]; then
        if [ -d "$USER_HOME/$fallback_cn" ]; then
            path="$USER_HOME/$fallback_cn"
        else
            path="$USER_HOME/$fallback_en"
        fi
    fi
    echo "$path"
}

DOCUMENTS_DIR=$(get_xdg_dir DOCUMENTS Documents 文档)
DOWNLOADS_DIR=$(get_xdg_dir DOWNLOAD Downloads 下载)
PICTURES_DIR=$(get_xdg_dir PICTURES Pictures 图片)
VIDEOS_DIR=$(get_xdg_dir VIDEOS Videos 视频)
DESKTOP_DIR=$(get_xdg_dir DESKTOP Desktop 桌面)

# 定义缩略图目录
THUMBNAIL_DIR="$USER_HOME/.cache/thumbnails"

RECENT="$USER_HOME/.local/share/recently-used.xbel"

# 定义要清理的文件后缀
EXTENSIONS=("xlsx" "xls" "doc" "docx" "jpg" "jpeg" "rar" "zip" "ppt" "pdf" "pptx" "png" "txt")

# 统计变量
TOTAL_FILES=0
TOTAL_SIZE=0
BROWSER_CLEAN_COUNT=0
BROWSER_CLEAN_SIZE=0
THUMBNAIL_CLEAN_COUNT=0
APT_CLEANED=0
CLEANED_DIRS=""

# 函数：统计并删除指定目录中的文件
cleanup_directory() {
    local DIR="$1"
    local DIR_NAME="$2"
    local DIR_COUNT=0
    local DIR_SIZE=0
    
    if [ -d "$DIR" ]; then
        echo "正在清理目录: $DIR"
        for EXT in "${EXTENSIONS[@]}"; do
            # 先统计文件数量和大小
            while IFS= read -r -d '' file; do
                file_size=$(stat -c%s "$file" 2>/dev/null || echo 0)
                DIR_SIZE=$((DIR_SIZE + file_size))
                DIR_COUNT=$((DIR_COUNT + 1))
                rm -f "$file" 2>/dev/null
            done < <(find "$DIR" -maxdepth 2 -type f -iname "*.$EXT" -print0 2>/dev/null)
        done
        
        if [ $DIR_COUNT -gt 0 ]; then
            TOTAL_FILES=$((TOTAL_FILES + DIR_COUNT))
            TOTAL_SIZE=$((TOTAL_SIZE + DIR_SIZE))
            if [ -n "$CLEANED_DIRS" ]; then
                CLEANED_DIRS="$CLEANED_DIRS, $DIR_NAME"
            else
                CLEANED_DIRS="$DIR_NAME"
            fi
            echo "  - 删除了 $DIR_COUNT 个文件"
        fi
    fi
}

# 清理核心目录 (同时遍历中英文目录)
# 清理核心目录 (基于 XDG 动态获取的真实路径)
cleanup_directory "$DOCUMENTS_DIR" "文档"
cleanup_directory "$DOWNLOADS_DIR" "下载"
cleanup_directory "$PICTURES_DIR" "图片"
cleanup_directory "$VIDEOS_DIR" "视频"
cleanup_directory "$DESKTOP_DIR" "桌面"

# 清理回收站
echo "正在清空回收站..."
TRASH_COUNT=0
TRASH_DIR="$USER_HOME/.local/share/Trash"
if [ -d "$TRASH_DIR/files" ]; then
    TRASH_COUNT=$(find "$TRASH_DIR/files" -type f 2>/dev/null | wc -l)
    rm -rf "$TRASH_DIR/files"/* 2>/dev/null
    rm -rf "$TRASH_DIR/info"/* 2>/dev/null
    if [ $TRASH_COUNT -gt 0 ]; then
        echo "  - 清空了 $TRASH_COUNT 个回收站文件"
    fi
fi

# 清理最近使用的文件记录
echo "正在清理最近使用的记录..."
RECENT_CLEANED=0
if [ -f "$RECENT" ]; then
    rm -f "$RECENT"
    RECENT_CLEANED=1
fi

# 清理浏览器缓存
echo "正在清理浏览器缓存..."
for cache_dir in "${BROWSER_CACHES[@]}"; do
    if [ -d "$cache_dir" ]; then
        # 统计将要删除的文件大小和数量
        while IFS= read -r -d '' file; do
            file_size=$(stat -c%s "$file" 2>/dev/null || echo 0)
            BROWSER_CLEAN_SIZE=$((BROWSER_CLEAN_SIZE + file_size))
            BROWSER_CLEAN_COUNT=$((BROWSER_CLEAN_COUNT + 1))
        done < <(find "$cache_dir" -type f -print0 2>/dev/null)
        
        # 只删缓存目录内的文件保留空壳
        find "$cache_dir" -mindepth 1 -delete 2>/dev/null
    fi
done

if [ $BROWSER_CLEAN_COUNT -gt 0 ]; then
    echo "  - 释放了浏览器缓存空间"
fi

# 清理命令历史 (清空 bash_history 文件)
echo "正在清理 Shell 历史记录..."
if [ -f "$USER_HOME/.bash_history" ]; then
    > "$USER_HOME/.bash_history"
fi

# 清理缩略图
if [ "${CLEANUP_SYS_THUMBNAILS,,}" = "yes" ]; then
    echo "正在清理缩略图缓存..."
    if [ -d "$THUMBNAIL_DIR" ]; then
        THUMBNAIL_CLEAN_COUNT=$(find "$THUMBNAIL_DIR" -type f 2>/dev/null | wc -l)
        rm -rf "$THUMBNAIL_DIR"/* 2>/dev/null
        if [ $THUMBNAIL_CLEAN_COUNT -gt 0 ]; then
            echo "  - 清空了 $THUMBNAIL_CLEAN_COUNT 个缩略图缓存"
        fi
    fi
fi

# 清理系统底层垃圾 (APT & 日志) 需Root权限
if [ "$EUID" -eq 0 ]; then
    if [ "${CLEANUP_SYS_APT,,}" = "yes" ] || [ "${CLEANUP_SYS_JOURNAL,,}" = "yes" ]; then
        echo "识别为 Root 权限，正在按配置清理系统底层缓存..."
        
        # 清理APT缓存
        if [ "${CLEANUP_SYS_APT,,}" = "yes" ]; then
            echo "  - 清理 APT 软件包缓存..."
            apt-get clean -y >/dev/null 2>&1
            apt-get autoremove -y >/dev/null 2>&1
            APT_CLEANED=1
        fi
        
        # 清理旧日志
        if [ "${CLEANUP_SYS_JOURNAL,,}" = "yes" ]; then
            echo "  - 清理过期 Systemd 日志..."
            if command -v journalctl &> /dev/null; then
                journalctl --vacuum-time=7d >/dev/null 2>&1
                journalctl --vacuum-size=100M >/dev/null 2>&1
                JOURNAL_CLEANED=1
            fi
        fi
    fi
fi

# 格式化文件大小
format_size() {
    local size=$1
    if [ $size -ge 1073741824 ]; then
        echo "$(awk "BEGIN {printf \"%.2f\", $size/1073741824}") GB"
    elif [ $size -ge 1048576 ]; then
        echo "$(awk "BEGIN {printf \"%.2f\", $size/1048576}") MB"
    elif [ $size -ge 1024 ]; then
        echo "$(awk "BEGIN {printf \"%.2f\", $size/1024}") KB"
    else
        echo "$size B"
    fi
}

# 生成清理报告
echo ""
echo "=========================================="
echo "用户数据清理完成!"
echo "=========================================="
echo ""

FORMATTED_SIZE=$(format_size $TOTAL_SIZE)
FORMATTED_BROWSER_SIZE=$(format_size $BROWSER_CLEAN_SIZE)

if [ $TOTAL_FILES -gt 0 ] || [ $TRASH_COUNT -gt 0 ] || [ $BROWSER_CLEAN_COUNT -gt 0 ] || [ $RECENT_CLEANED -eq 1 ] || [ $THUMBNAIL_CLEAN_COUNT -gt 0 ] || [ $APT_CLEANED -eq 1 ]; then
    echo "清理统计:"
    if [ $TOTAL_FILES -gt 0 ]; then
        echo "  • 用户目录: 删除 $TOTAL_FILES 个文件 ($FORMATTED_SIZE)"
        echo "    清理位置: $CLEANED_DIRS"
    fi
    if [ $BROWSER_CLEAN_COUNT -gt 0 ]; then
        echo "  • 浏览器缓存: 清理了 $BROWSER_CLEAN_COUNT 个临时文件 ($FORMATTED_BROWSER_SIZE)"
    fi
    if [ $THUMBNAIL_CLEAN_COUNT -gt 0 ]; then
        echo "  • 缩略图缓存: 清理了 $THUMBNAIL_CLEAN_COUNT 张过时图片缓存"
    fi
    if [ $TRASH_COUNT -gt 0 ]; then
        echo "  • 回收站: 清空 $TRASH_COUNT 个文件"
    fi
    if [ $APT_CLEANED -eq 1 ]; then
        echo "  • APT 缓存: 清理了陈旧的安装包残留"
    fi
    if [ "$JOURNAL_CLEANED" = "1" ]; then
        echo "  • 系统日志: 修剪了庞大的过时 Systemd 日志"
    fi
    if [ $RECENT_CLEANED -eq 1 ]; then
        echo "  • 最近使用记录: 已清理"
    fi
else
    echo "本次未发现需要清理的文件。"
fi

echo ""
echo "操作已执行完毕。"

# 发送桌面通知
if command -v notify-send &> /dev/null; then
    if [ $TOTAL_FILES -gt 0 ] || [ $TRASH_COUNT -gt 0 ] || [ $BROWSER_CLEAN_COUNT -gt 0 ] || [ $THUMBNAIL_CLEAN_COUNT -gt 0 ] || [ $APT_CLEANED -eq 1 ]; then
        NOTIFY_MSG="已清理 $TOTAL_FILES 个日常文件 ($FORMATTED_SIZE)"
        if [ $TRASH_COUNT -gt 0 ]; then
            NOTIFY_MSG="$NOTIFY_MSG\n回收站清空 $TRASH_COUNT 个垃圾"
        fi
        if [ $BROWSER_CLEAN_COUNT -gt 0 ]; then
            NOTIFY_MSG="$NOTIFY_MSG\n释放浏览器空间 $FORMATTED_BROWSER_SIZE"
        fi
        if [ $THUMBNAIL_CLEAN_COUNT -gt 0 ]; then
            NOTIFY_MSG="$NOTIFY_MSG\n清除了 $THUMBNAIL_CLEAN_COUNT 张系统缩略图缓存"
        fi
        if [ $APT_CLEANED -eq 1 ]; then
            NOTIFY_MSG="$NOTIFY_MSG\n移除了底层 APT 残留"
        fi
        if [ "$JOURNAL_CLEANED" = "1" ]; then
            NOTIFY_MSG="$NOTIFY_MSG\n截断了过期系统日志"
        fi
        if [ -n "$CLEANED_DIRS" ]; then
            NOTIFY_MSG="$NOTIFY_MSG\n清理位置: $CLEANED_DIRS"
        fi
        notify-send -i user-trash-full "用户数据清理完成" "$NOTIFY_MSG" 2>/dev/null
    else
        notify-send -i dialog-information "用户数据清理完成" "本次未发现需要清理的文件" 2>/dev/null
    fi
fi

read -p "按回车键退出..." -n 1 -s
