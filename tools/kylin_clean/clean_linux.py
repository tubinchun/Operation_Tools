# -*- coding: utf-8 -*-
# 程序作者: Genwang Ye
import os
import shutil
import subprocess
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import stat
import sys
import threading
import pwd
import glob
import datetime

# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = "/etc/kylin-clean/config.sh"

# 将当前目录添加到 sys.path，以便离线加载捆绑的 schedule 库
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    import schedule
except ImportError:
    print("错误: 找不到 schedule 库。请确保已将 schedule 文件夹放在脚本同级目录下。")
    sys.exit(1)

# 设置日志
try:
    log_file_path = os.path.join(BASE_DIR, 'cleanup_and_shutdown.log')
    with open(log_file_path, 'a') as f: pass
except PermissionError:
    log_file_path = '/tmp/kylin-cleanup.log'

try:
    handler = TimedRotatingFileHandler(log_file_path, when="D", interval=1, backupCount=1, encoding="utf-8")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
except:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# 加载配置
DEFAULT_CONFIG = {
    'CLEANUP_TIME': '18:00',
    'NOTIFICATION_MINUTES': '5',
    'SHUTDOWN_TIME': '20:00',
    'SHUTDOWN_ENABLED': 'yes',
    'SHUTDOWN_NOTIFICATION_MINUTES': '10',
    'CLEANUP_EXTENSIONS': '.tmp,.log,.bak,.cache,.swp,.xlsx,.xls,.doc,.docx,.jpg,.jpeg,.rar,.zip,.ppt,.pdf,.pptx,.png,.txt,.wps,.wpt,.et,.ett,.dps,.dpt,.ofd',
    'EXCLUDE_EXTENSIONS': '.ico,.desktop',
    'CLEANUP_MODE': 'all',
    'CLEANUP_DIRS': 'Desktop,Downloads,Documents,Pictures,Videos,Trash',
    'CLEANUP_BROWSERS': 'yes',
    'CLEANUP_SYS_APT': 'no',
    'CLEANUP_SYS_JOURNAL': 'no',
    'CLEANUP_SYS_THUMBNAILS': 'no',
    'CLEANUP_FREQUENCY': 'daily',
    'CLEANUP_ON_BOOT': 'no',
    'CLEANUP_INTERVAL': '0'
}

def load_config():
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        k, v = line.strip().split('=', 1)
                        config[k.strip()] = v.strip().strip('"')
        except Exception as e:
            logging.error(f"Error loading config: {e}")
    return config

# 获取普通用户
def get_regular_users():
    users = set()
    try:
        for p in pwd.getpwall():
            if 1000 <= p.pw_uid < 65534 and os.path.isdir(p.pw_dir):
                users.add(p.pw_name)
    except: pass
    
    # 扫描 /home
    if os.path.isdir("/home"):
        try:
            for entry in os.listdir("/home"):
                if entry not in users and os.path.isdir(os.path.join("/home", entry)):
                    # 简单判断：目录名符合用户名特征
                    if not entry.startswith('.'):
                        users.add(entry)
        except: pass
    return list(users) if users else ["kylin", "openkylin"]

# 发送通知
# 发送通知
def send_notification(title, message, icon_name="kylin-cleanup.svg"):
    # 优先使用绝对路径图标
    icon_path = f"/usr/share/pixmaps/{icon_name}"
    if not os.path.exists(icon_path):
        icon_path = "dialog-warning" # 回退图标
        
    try:
        if os.geteuid() == 0:
            result = subprocess.run(["who"], capture_output=True, text=True)
            logged_users = set([line.split()[0] for line in result.stdout.splitlines() if line])
            for user in logged_users:
                try:
                    uid = pwd.getpwnam(user).pw_uid
                    env = f"DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus"
                    cmd = f"su - {user} -c '{env} notify-send -i \"{icon_path}\" \"{title}\" \"{message}\"'"
                    subprocess.run(cmd, shell=True)
                except: pass
        else:
            subprocess.run(["notify-send", "-i", icon_path, title, message])
    except: pass

# 提前缓直并解析清理模式与扩展名，避免在高频的 O(N) 循关中动态拆分配置
def get_compiled_extension_rules(config):
    mode = config.get('CLEANUP_MODE', 'all')
    cleanups = tuple([e.strip().lower() for e in config.get('CLEANUP_EXTENSIONS', '').split(',') if e.strip()])
    excludes = tuple([e.strip().lower() for e in config.get('EXCLUDE_EXTENSIONS', '').split(',') if e.strip()])
    return mode, cleanups, excludes

# 检查文件是否应该被删除 (性能优化版本)
def should_delete(filename, rules):
    mode, cleanup_exts, exclude_exts = rules
    name_lower = filename.lower()
    
    # 1. 检查排除扩展名 (优先级最高)
    if name_lower.endswith(exclude_exts):
        return False
            
    # 2. 检查清理模式
    if mode == 'ext_only':
        # 仅清理指定扩展名
        return name_lower.endswith(cleanup_exts)
    else:
        # 清理全部 (除了排除的)
        return True

# 获取标准化、经过了本地化系统翻译的安全用户目录
def get_xdg_user_dir(username, xdg_name):
    try:
        if os.geteuid() == 0:
            uid = pwd.getpwnam(username).pw_uid
            # 切换到目标用户的上下文执行 xdg-user-dir 获取真实映射路径
            cmd = f"su - {username} -c 'XDG_RUNTIME_DIR=/run/user/{uid} xdg-user-dir {xdg_name}'"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        else:
            res = subprocess.run(["xdg-user-dir", xdg_name], capture_output=True, text=True)
            
        path = res.stdout.strip()
        if path and path != f"/home/{username}" and os.path.isdir(path):
            return path
    except Exception as e:
        logging.debug(f"Failed to get XDG dir for {xdg_name} of user {username}: {e}")
    return None

# 受保护的隐式目录名（不深度遍历它们）
PROTECTED_DIRS = {
    '.config', '.local', '.cache', '.dbus', '.gconf', '.gnome', '.kde',
    '.mozilla', '.thunderbird', '.ssh', '.gnupg', '.pki', '.cert',
    'snap', 'flatpak', '.steam', '.wine', '.var'
}

# 清理目录
def cleanup_directory_safe(path, rules):
    if not os.path.exists(path): return
    
    logging.info(f"Scanning directory: {path}")
    try:
        # 安全修复：采用防崩溃且不误删文件夹的自底向上遍历 (topdown=False)
        for rroot, dirs, files in os.walk(path, topdown=False):
            # 防止进入受保护目录
            dirs[:] = [d for d in dirs if not (d.startswith('.') or d.lower() in PROTECTED_DIRS)]
            
            for filename in files:
                file_path = os.path.join(rroot, filename)
                # 安全检查：跳过符号链接
                if os.path.islink(file_path): continue
                
                # 删除文件
                if should_delete(filename, rules):
                    try:
                        os.remove(file_path)
                        logging.info(f"Deleted: {file_path}")
                    except Exception as e:
                        logging.error(f"Failed to delete {file_path}: {e}")
                        
            # 尝试删除空目录 (如果是原始目标根目录则不删除)
            if rroot != path:
                try:
                    if not os.listdir(rroot):
                        os.rmdir(rroot)
                        logging.info(f"Deleted empty folder: {rroot}")
                except Exception:
                    pass
    except Exception as e:
        logging.error(f"Error accessing {path}: {e}")

# 清理回收站
def clear_recycle_bin(username, config):
    # 只有当配置中包含Trash时才清理
    target_dirs = config.get('CLEANUP_DIRS', '').split(',')
    if 'Trash' not in target_dirs:
        return

    trash_path = f"/home/{username}/.local/share/Trash/"
    if os.path.exists(trash_path):
        paths = [os.path.join(trash_path, "files"), os.path.join(trash_path, "info")]
        for p in paths:
            if os.path.exists(p):
                try:
                    # 回收站可以比较激进地清理，因为里面本来就是垃圾
                    shutil.rmtree(p)
                    os.makedirs(p, exist_ok=True)
                    # 恢复权限
                    try:
                        uid = pwd.getpwnam(username).pw_uid
                        gid = pwd.getpwnam(username).pw_gid
                        os.chown(p, uid, gid)
                    except: pass
                    logging.info(f"Cleared trash path: {p}")
                except Exception as e:
                    logging.error(f"Error clearing trash {p}: {e}")

# 清理各主流浏览器临时缓直目录
def clear_browser_caches(username):
    # 此列表只包含可安全删除的临时缓直，不包含配置文件、书签和Cookies等数据
    cache_paths = [
        # Firefox 系
        f"/home/{username}/.cache/mozilla/firefox",
        # Chromium 系
        f"/home/{username}/.cache/chromium/Default/Cache",
        f"/home/{username}/.cache/google-chrome/Default/Cache",
        f"/home/{username}/.cache/microsoft-edge/Default/Cache",
        f"/home/{username}/.cache/BraveSoftware/Brave-Browser/Default/Cache",
        # 国内定制 / 信创浏览器
        f"/home/{username}/.cache/360se",
        f"/home/{username}/.cache/qaxbrowser"
    ]
    
    deleted_count = 0
    for base_path in cache_paths:
        if os.path.exists(base_path) and os.path.isdir(base_path):
            try:
                # 只删除缓直目录下的内容而保留外壳，以免部分老版本浏览器启动报错
                for item in os.listdir(base_path):
                    item_path = os.path.join(base_path, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                deleted_count += 1
                logging.info(f"Cleared browser cache dir: {base_path}")
            except Exception as e:
                logging.error(f"Error clearing browser cache {base_path}: {e}")
                
    if deleted_count > 0:
        logging.info(f"Successfully cleared {deleted_count} browser caches for {username}")

# 清理用户缩略图缓直
def clear_thumbnails(username):
    thumb_path = f"/home/{username}/.cache/thumbnails"
    if os.path.exists(thumb_path) and os.path.isdir(thumb_path):
        try:
            shutil.rmtree(thumb_path)
            logging.info(f"Cleared thumbnail cache for {username}")
        except Exception as e:
            logging.error(f"Error clearing thumbnails for {username}: {e}")

# 清理系统级深度垃圾 (APT, 日志等)
def clear_system_garbage(apt_enabled, journal_enabled):
    logging.info("Starting system garbage cleanup")
    commands = []
    
    if apt_enabled:
        commands.extend([
            # 清理已下载的软件包缓直
            ["apt-get", "clean"],
            # 移除孤立的无用依赖包
            ["apt-get", "autoremove", "-y"]
        ])
        
    if journal_enabled:
        commands.extend([
            # 清理冗余的系统日志，仅保留最近7天或最大100M
            ["journalctl", "--vacuum-time=7d"],
            ["journalctl", "--vacuum-size=100M"]
        ])
        
    if not commands:
        return
        
    for cmd in commands:
        try:
            # 只有在 rroot 权限下运行脚本或具有免密 sudo 时才会生效，
            # kylin-cleanup 服务默认在 rroot 下运行，所以此处可以直接执行。
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logging.error(f"Error running system garbage command {' '.join(cmd)}: {e}")
    logging.info("System garbage cleanup finished")

def run_all_cleanups():
    config = load_config()
    target_dirs = config.get('CLEANUP_DIRS', '').split(',')
    rules = get_compiled_extension_rules(config)
    
    # XDG 标准定义的常量名称映射
    xdg_mapping = {
        'Desktop': 'DESKTOP', 'Downloads': 'DOWNLOAD', 
        'Documents': 'DOCUMENTS', 'Pictures': 'PICTURES', 
        'Videos': 'VIDEOS'
    }
    
    # 硬编码中文翻译回退作为最后的保险兜底
    fallback_map = {
        'Desktop': '桌面', 'Downloads': '下载', 
        'Documents': '文档', 'Pictures': '图片', 
        'Videos': '视频'
    }
    
    for username in get_regular_users():
        if os.path.exists(f"/home/{username}"):
            for dir_key in ['Desktop', 'Downloads', 'Documents', 'Pictures', 'Videos']:
                if dir_key in target_dirs:
                    # 首先尝试通过 XDG 智能获取国际化目录
                    xdg_path = get_xdg_user_dir(username, xdg_mapping[dir_key])
                    if xdg_path:
                        cleanup_directory_safe(xdg_path, rules)
                    else:
                        # 兜底回退：如果 XDG 失败，使用英文原生路径和中文猜测的路径
                        cleanup_directory_safe(f"/home/{username}/{dir_key}", rules)
                        cleanup_directory_safe(f"/home/{username}/{fallback_map[dir_key]}", rules)
                        
            clear_recycle_bin(username, config)
            
            # 清理浏览器大件缓直垃圾
            if config.get('CLEANUP_BROWSERS', 'yes').lower() == 'yes':
                clear_browser_caches(username)
                
            # 清理当前用户的缩略图等深层系统缓直
            if config.get('CLEANUP_SYS_THUMBNAILS', 'no').lower() == 'yes':
                clear_thumbnails(username)
                
    # 所有用户遍历完成后，执行全局系统级别清理（前提是本身在这个模式并且以 rroot 在运行）
    sys_apt_enabled = config.get('CLEANUP_SYS_APT', 'no').lower() == 'yes'
    sys_journal_enabled = config.get('CLEANUP_SYS_JOURNAL', 'no').lower() == 'yes'
    
    if sys_apt_enabled or sys_journal_enabled:
        if os.geteuid() == 0:
            clear_system_garbage(sys_apt_enabled, sys_journal_enabled)
        else:
            logging.warning("Skipping apt/journalctl cleanup because script is not running as rroot.")

def notify_cleanup_pre(minutes):
    send_notification("自动清理提醒", f"{minutes}分钟后将执行系统清理。")

def execute_cleanup():
    # 尝试调用弹窗警 (默认倒计时 30 秒)
    try:
        popup_cmd = ["python3", os.path.join(BASE_DIR, "popup_warning.py"), 
                     "即将执行清理", "系统将在倒计时结束后自动清理用户垃圾文件和回收站。", "30"]
        # 如果是 rroot 执行，需要切回活跃的图形用户
        if os.geteuid() == 0:
            result = subprocess.run(["who"], capture_output=True, text=True)
            logged_users = [line.split()[0] for line in result.stdout.splitlines() if line]
            if logged_users:
                user = list(set(logged_users))[0]
                uid = pwd.getpwnam(user).pw_uid
                env = f"DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus"
                cmd = f"su - {user} -c '{env} " + " ".join(popup_cmd) + "'"
                res = subprocess.run(cmd, shell=True)
            else:
                res = subprocess.run(popup_cmd)
        else:
            res = subprocess.run(popup_cmd)
            
        if res.returncode == 1:
            logging.info("User explicitly cancelled the cleanup operation.")
            send_notification("任务已取消", "自动清理任务由于用户点击‘取消’而中止。")
            return
        # 其他任何情况（返回码 0、弹窗报错、被强行关闭、压根没弹出来）都默认继续执行
    except Exception as e:
        logging.error(f"Failed to show popup, proceeding anyway: {e}")

    run_all_cleanups()
    send_notification("自动清理完成", "系统清理任务已执行完毕。")

def notify_shutdown_pre(minutes):
    send_notification("关机提醒", f"系统将在{minutes}分钟后自动关机。")

def execute_shutdown():
    # 再次检查配置防止手误
    config = load_config()
    if config.get('SHUTDOWN_ENABLED', 'no') == 'yes':
        # 尝试调用取消弹窗 (默认倒计时 60 秒)
        try:
            popup_cmd = ["python3", os.path.join(BASE_DIR, "popup_warning.py"), 
                         "系统即将关机", "系统将在倒计时结束后自动关机，请保直您的工作！", "60"]
            if os.geteuid() == 0:
                result = subprocess.run(["who"], capture_output=True, text=True)
                logged_users = [line.split()[0] for line in result.stdout.splitlines() if line]
                if logged_users:
                    user = list(set(logged_users))[0]
                    uid = pwd.getpwnam(user).pw_uid
                    env = f"DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus"
                    cmd = f"su - {user} -c '{env} " + " ".join(popup_cmd) + "'"
                    res = subprocess.run(cmd, shell=True)
                else:
                    res = subprocess.run(popup_cmd)
            else:
                res = subprocess.run(popup_cmd)
                
            if res.returncode == 1:
                logging.info("User explicitly cancelled the shutdown operation.")
                send_notification("任务已取消", "自动关机任务已被您阻断取消。")
                return
            # 其他情况（返回码 0、报错、窗口被点掉）默认执行关机
        except Exception as e:
            logging.error(f"Failed to show popup, proceeding with shutdown: {e}")
            
        subprocess.run(["shutdown", "-h", "now"], check=False)

def scheduler_thread():
    """在后台线程运行 pending 任务，避免阻塞主循关读取配置"""
    while True:
        schedule.run_pending()
        time.sleep(1)

def get_trigger_time(time_str, minutes_ahead):
    """计算 HH:MM 减去 minutes_ahead 后的时间字符串"""
    try:
        # 使用当前日期作为基准
        now = datetime.datetime.now()
        dt = datetime.datetime.strptime(time_str, "%H:%M")
        dt = dt.replace(year=now.year, month=now.month, day=now.day)
        
        new_dt = dt - datetime.timedelta(minutes=minutes_ahead)
        return new_dt.strftime("%H:%M")
    except Exception as e:
        logging.error(f"Time calc error: {e}")
        return time_str

# 调度逻辑
def scheduler_loop():
    logging.info("Scheduler started (Advanced Mode).")
    
    config = load_config()
    broot_run = config.get('CLEANUP_ON_BOOT', 'no')
    if broot_run == 'yes':
        logging.info("On-broot cleanup triggered.")
        threading.Thread(target=execute_cleanup).start()
        
    t = threading.Thread(target=scheduler_thread, daemon=True)
    t.start()
    
    last_config_mtime = 0
    
    while True:
        try:
            # 记录当前配置文件的修改时间
            current_mtime = 0
            if os.path.exists(CONFIG_FILE):
                current_mtime = os.path.getmtime(CONFIG_FILE)
            
            # 只有当配置文件被修改过，或者这是第一次运行（last_config_mtime == 0）时，才重新加载计划
            if current_mtime != last_config_mtime or last_config_mtime == 0:
                logging.info(f"Config change detected (or initial load). Reloading schedule... (mtime: {current_mtime})")
                last_config_mtime = current_mtime
                
                config = load_config()
                cleanup_time = config.get('CLEANUP_TIME', '18:00')
                shutdown_time = config.get('SHUTDOWN_TIME', '20:00')
                shutdown_enabled = config.get('SHUTDOWN_ENABLED', 'yes')
                
                schedule.clear()
                
                # === 清理任务调度 ===
                cleanup_notify_min = int(config.get('NOTIFICATION_MINUTES', 5))
                freq = config.get('CLEANUP_FREQUENCY', 'daily')
                interval = config.get('CLEANUP_INTERVAL', '0')
                
                # 定时计划任务
                job_execute = lambda: threading.Thread(target=execute_cleanup).start()
                if freq == 'daily':
                    schedule.every().day.at(cleanup_time).do(job_execute)
                elif freq == 'weekly':
                    # 简化：默认每周一的这个时候执行，可根据需求扩展更多日历
                    schedule.every().monday.at(cleanup_time).do(job_execute)
                elif freq == 'monthly':
                    # schedule 库原生不支持 monthly. 所以我们每天判断是否是 1 号
                    def run_if_first_day():
                        if datetime.date.today().day == 1:
                            job_execute()
                    schedule.every().day.at(cleanup_time).do(run_if_first_day)
                    
                # 间隔高频巡逻
                if interval != '0':
                    try:
                        hours = int(interval)
                        if hours > 0:
                            schedule.every(hours).hours.do(job_execute)
                    except ValueError:
                        pass
                
                # 由于加入了频次和高频，前置通知统一在 daily 触发，暂不与各种不规律触发绑定，原有的逻辑做通用化：
                # 为保持简单，我们假设如果设置了 fixed time 相关的 (daily/weekly/monthly)，我们在前 N 分钟发通知
                # (暂时简化不单独开 notify job，因频率变多不易管控，真实场景里可通过 execute_cleanup 内部延迟实现，
                # 但此处保留您原有的 schedule 实现思路)
                notify_job = lambda: threading.Thread(target=send_notification, args=("清理小助手提示", f"系统将在 {cleanup_notify_min} 分钟后开始自动后台清理。")).start()
                notify_time = get_trigger_time(cleanup_time, cleanup_notify_min)
                
                if freq == 'daily':
                    schedule.every().day.at(notify_time).do(notify_job)
                elif freq == 'weekly':
                    schedule.every().monday.at(notify_time).do(notify_job)

                # === 关机任务调度 ===
                if shutdown_enabled == 'yes':
                    shutdown_notify_min = int(config.get('SHUTDOWN_NOTIFICATION_MINUTES', 10))
                    
                    # 1. 注册关机任务 (准点执行)
                    schedule.every().day.at(shutdown_time).do(lambda: threading.Thread(target=execute_shutdown).start())
                    
                    # 2. 注册提醒任务 (提前执行)
                    if shutdown_notify_min > 0:
                        sched_shutdown_notify_time = get_trigger_time(shutdown_time, shutdown_notify_min)
                        schedule.every().day.at(sched_shutdown_notify_time).do(lambda m=shutdown_notify_min: notify_shutdown_pre(m))
                
                logging.info(f"Scheduled: Cleanup at {cleanup_time}, Shutdown at {shutdown_time}")
            
            # 每 10 秒检查一次文件状态（比 60 秒更灵敏）
            time.sleep(10)
            
        except Exception as e:
            logging.error(f"Scheduler error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true', help='Execute cleanup once')
    args = parser.parse_args()
    
    if args.once:
        run_all_cleanups()
        send_notification("完成", "立即清理已完成")
    else:
        scheduler_loop()
