import os
import subprocess
import time
import sys

# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 将当前目录添加到 sys.path，以便离线加载捆绑的 schedule 库
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    import schedule
except ImportError:
    print("错误: 找不到 schedule 库。请确保已将 schedule 文件夹放在脚本同级目录下。")
    sys.exit(1)

def notify_cleanup():
    try:
        # 使用 notify-send 发送桌面通知 (UKUI/Gnome/KDE 兼容)
        title = "桌面清理通知"
        message = "10分钟后将自动清理桌面、下载目录及回收站，请保存重要文件。"
        subprocess.run(["notify-send", "-i", "dialog-warning", title, message], check=False)
    except Exception as e:
        print(f"发送通知失败: {e}")

def clear_recycle_bin():
    # Linux 回收站通常位于 ~/.local/share/Trash/
    trash_path = os.path.expanduser("~/.local/share/Trash/")
    try:
        if os.path.exists(trash_path):
            files = os.path.join(trash_path, "files")
            info = os.path.join(trash_path, "info")
            
            if os.path.exists(files):
                subprocess.run(f"rm -rf {files}/*", shell=True)
            if os.path.exists(info):
                subprocess.run(f"rm -rf {info}/*", shell=True)
            
            print("回收站已清空。")
        else:
            print("未找到回收站目录。")
    except Exception as e:
        print(f"清空回收站失败: {e}")

def main_task():
    notify_cleanup()
    time.sleep(600) # 等待10分钟后再清理，给用户保存时间
    clear_recycle_bin()
    subprocess.run(["notify-send", "-i", "user-trash-full", "清理完成", "回收站已清空。"], check=False)

def main():
    # 每天 8:00 到 18:00 每小时执行一次通知和回收站清理
    for hour in range(8, 19):
        schedule.every().day.at(f"{hour:02d}:00").do(main_task)

    print("Linux Notification Service started (Offline mode enabled).")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    # 启动时执行一次
    clear_recycle_bin()
    main()
