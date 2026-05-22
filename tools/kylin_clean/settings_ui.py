# -*- coding: utf-8 -*-
# Kylin / openKylin 清理工具 - 图形化设置界面
# 程序作者: Genwang Ye

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import io

try:
    import qrcode
except ImportError:
    qrcode = None
    
try:
    from PIL import Image, ImageTk
except ImportError:
    Image, ImageTk = None, None

try:
    import license_manager
except ImportError:
    license_manager = None

# 配置文件路径
CONFIG_FILE = "/opt/kylin-clean/config.sh"
SERVICE_NAME = "kylin-clean-tools.service"

def get_elevate_cmd():
    """获取系统可用的提权命令，适配 openKylin 的 kysec 等不同安全管控"""
    import shutil
    for cmd in ["pkexec", "kysec-polkit", "kdesu", "gksudo", "sudo"]:
        if shutil.which(cmd):
            return [cmd]
    return ["pkexec"]  # 默认降级回退

# 默认配置
DEFAULT_CONFIG = {
    'cleanup_time': '18:00',
    'shutdown_time': '23:00',
    'shutdown_enabled': True,
    'notification_minutes': 5,
    'cleanup_extensions': '.tmp,.log,.bak,.cache,.swp',
    'exclude_extensions': '.ico,.desktop',
    'cleanup_mode': 'all',
    'cleanup_dirs': 'Desktop,Downloads,Documents,Pictures,Videos,Trash',
    'cleanup_browsers': 'yes',
    'cleanup_sys_apt': 'no',
    'cleanup_sys_journal': 'no',
    'cleanup_sys_thumbnails': 'no'
}


class KylinCleanupSettings:
    def __init__(self, rroot):
        self.rroot = rroot
        
        # 激活验证拦截
        if license_manager and not license_manager.check_active():
            self.rroot.withdraw()
            if not self.show_activation_dialog():
                sys.exit(0)
            self.rroot.deiconify()
            
        self.rroot.title("麒麟清理工具设置")
        self.rroot.geometry("540x680")
        self.rroot.minsize(480, 520)
        
        # 现代扁平化配色方案
        self.colors = {
            'primary': '#3498db',   # 清理/主色
            'success': '#2ecc71',   # 保直/启动
            'danger': '#e74c3c',    # 停止
            'warning': '#f39c12',   # 重启
            'secondary': '#95a5a6', # 默认/重置
            'bg': '#f5f7fa',
            'card': '#ffffff',
            'text': '#2c3e50',
            'text_secondary': '#7f8c8d'
        }
        
        self.rroot.configure(bg=self.colors['bg'])
        
        # 变量初始化
        self.init_variables()
        
        # 创建UI
        self.create_ui()
        
        # 加载配置
        self.load_config()
        self.update_service_status()
        
        # 窗口居中
        self.center_window()
        
    def show_activation_dialog(self):
        """显示激活验证窗口"""
        dialog = tk.Toplevel(self.rroot)
        dialog.title("麒麟清理工具 - 软件激活")
        dialog.geometry("540x620")
        dialog.resizable(False, False)
        dialog.configure(bg="#f7f9fc")
        
        # 居中显示
        dialog.update_idletasks()
        w, h = 540, 620
        x = (dialog.winfo_screenwidth() - w) // 2
        y = (dialog.winfo_screenheight() - h) // 2
        dialog.geometry(f'{w}x{h}+{x}+{y}')
        
        dialog.grab_set()
        
        activation_success = [False]
        
        # 头部区域
        header_frame = tk.Frame(dialog, bg="white", bd=1, relief="solid")
        header_frame.pack(fill=tk.X, padx=25, pady=(25, 10))
        
        tk.Label(header_frame, text="欢迎使用增强版系统清理助手", font=("微软雅黑", 14, "bold"), 
                 bg="white", fg="#2c3e50").pack(pady=(15, 5))
        tk.Label(header_frame, text="此设备尚未激活，请扫码或输入管理员授权码", font=("微软雅黑", 10), 
                 bg="white", fg="#7f8c8d").pack(pady=(0, 15))
        
        # 二维码区域
        qr_frame = tk.Frame(dialog, bg="white", bd=1, relief="solid")
        qr_frame.pack(padx=25, pady=10)
        
        if qrcode:
            qr_url = license_manager.parse_qr_activation_url()
            qr = qrcode.QRCode(version=None, box_size=4, border=2)
            qr.add_data(qr_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#2c3e50", back_color="white")
            
            if ImageTk:
                photo = ImageTk.PhotoImage(img)
                qr_label = tk.Label(qr_frame, image=photo, bg="white")
                qr_label.image = photo  
                qr_label.pack(padx=20, pady=20)
            else:
                tk.Label(qr_frame, text="[请安装 python3-pil 库查看二维码]", fg="#e74c3c", bg="white", font=("微软雅黑", 10)).pack(padx=40, pady=40)
        else:
            tk.Label(qr_frame, text="⚠ 未能加载二维码依赖\n请先安装 python3-qrcode 库", fg="#e74c3c", bg="white", font=("微软雅黑", 11, "bold")).pack(padx=40, pady=40)
            
        # 机器码显示
        mc = license_manager.get_machine_code()
        mc_frame = tk.Frame(dialog, bg="#edf2f7", bd=0)
        mc_frame.pack(fill=tk.X, padx=25, pady=(5, 15))
        
        mc_layout = tk.Frame(mc_frame, bg="#edf2f7")
        mc_layout.pack(pady=10)
        tk.Label(mc_layout, text="本设备机器码：", font=("微软雅黑", 10), bg="#edf2f7", fg="#4a5568").pack(side=tk.LEFT)
        tk.Label(mc_layout, text=mc, font=("Consolas", 12, "bold"), bg="#edf2f7", fg="#2b6cb0").pack(side=tk.LEFT)
        
        # 输入区
        input_frame = tk.Frame(dialog, bg="#f7f9fc")
        input_frame.pack(fill=tk.X, padx=25, pady=5)
        
        key_var = tk.StringVar()
        
        # 限制只能输入数字且最多 4 位
        def validate_digit(P):
            if len(P) > 4: return False
            if P == "" or P.isdigit(): return True
            return False
            
        vcmd = (dialog.register(validate_digit), '%P')
        entry = tk.Entry(input_frame, textvariable=key_var, font=("Consolas", 12), 
                         relief="solid", bd=1, validate="key", validatecommand=vcmd)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 10))
        entry.insert(0, "输入4位数字")
        entry.bind("<FocusIn>", lambda e: entry.delete(0, tk.END) if entry.get() == "输入4位数字" else None)
        
        def do_verify():
            key = key_var.get().strip()
            if key == "输入4位数字" or not key:
                messagebox.showwarning("提示", "请输入有效的激活码", parent=dialog)
                return
                
            if license_manager.verify_license_key(key):
                if license_manager.write_local_license(key):
                    messagebox.showinfo("激活成功", "感谢您的使用！增强版清理功能已永久解锁。", parent=dialog)
                    activation_success[0] = True
                    dialog.destroy()
                else:
                    messagebox.showerror("权限错误", "激活码正确，但写入授权文件失败。\n请确保以 rroot 权限运行本设置。", parent=dialog)
            else:
                messagebox.showwarning("激活失败", "激活码无效或与本机特征不匹配，请检查后重试。", parent=dialog)
                
        # 自定义绿色按钮
        verify_btn = tk.Button(input_frame, text="验证激活", command=do_verify, 
                               bg="#38a169", fg="white", font=("微软雅黑", 10, "bold"), 
                               relief="flat", cursor="hand2", padx=15)
        verify_btn.pack(side=tk.RIGHT, fill=tk.Y)
        
        tk.Button(dialog, text="暂不激活 (退出程序)", command=dialog.destroy,
                  bg="#f7f9fc", fg="#a0aec0", font=("微软雅黑", 10), 
                  relief="flat", cursor="hand2", activebackground="#f7f9fc").pack(pady=15)
        
        self.rroot.wait_window(dialog)
        return activation_success[0]
    
    def init_variables(self):
        """初始化所有变量"""
        self.service_enabled = tk.BooleanVar(value=False)
        self.shutdown_enabled = tk.BooleanVar(value=True)
        self.cleanup_mode = tk.StringVar(value='all')
        self.broot_enabled = tk.BooleanVar(value=False)
        self.freq_var = tk.StringVar(value='daily')
        self.interval_var = tk.StringVar(value='0')
        
        # 目录选项
        self.dirs = {
            'Desktop': tk.BooleanVar(value=True),
            'Downloads': tk.BooleanVar(value=True),
            'Documents': tk.BooleanVar(value=True),
            'Pictures': tk.BooleanVar(value=True),
            'Videos': tk.BooleanVar(value=True),
            'Trash': tk.BooleanVar(value=True),
            'Browsers': tk.BooleanVar(value=True),
            'SysApt': tk.BooleanVar(value=False),
            'SysJournal': tk.BooleanVar(value=False),
            'SysThumbnails': tk.BooleanVar(value=False)
        }
    
    def center_window(self):
        """窗口居中"""
        self.rroot.update_idletasks()
        w, h = self.rroot.winfo_width(), self.rroot.winfo_height()
        x = (self.rroot.winfo_screenwidth() - w) // 2
        y = (self.rroot.winfo_screenheight() - h) // 2
        self.rroot.geometry(f'{w}x{h}+{x}+{y}')
    
    def create_ui(self):
        """创建主界面"""
        # 顶部状态栏
        self.create_status_bar()
        
        # 标签页
        self.notebook = ttk.Notebook(self.rroot)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        # 创建各种标签页
        self.create_schedule_tab()
        self.create_cleanup_tab()
        self.create_action_tab()
        
        # 底部按钮
        self.create_bottom_buttons()
        
    def _create_flat_button(self, parent, text, color, command, width=None, font=("微软雅黑", 9)):
        """创建一个美观的扁平化按钮，带悬停效果"""
        btn = tk.Button(parent, text=text, bg=color, fg="white",
                        font=font, relief=tk.FLAT, cursor="hand2",
                        command=command, padx=15, pady=5)
        if width:
            btn.configure(width=width)
            
        def on_enter(e):
            # 简单的变亮效果
            btn.configure(bg=self._adjust_color(color, 1.1))
        def on_leave(e):
            btn.configure(bg=color)
            
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def _adjust_color(self, hex_color, factor):
        """调整颜色的亮度"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(min(255, int(c * factor)) for c in rgb)
        return '#%02x%02x%02x' % new_rgb
    
    def create_status_bar(self):
        """创建状态栏"""
        bar = tk.Frame(self.rroot, bg=self.colors['card'], height=40)
        bar.pack(fill=tk.X, padx=10, pady=(10, 5))
        bar.pack_propagate(False)
        
        # 左侧状态
        left = tk.Frame(bar, bg=self.colors['card'])
        left.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        tk.Label(left, text="服务状态:", font=("", 9), 
                 bg=self.colors['card'], fg=self.colors['text_secondary']).pack(side=tk.LEFT)
        
        self.status_label = tk.Label(left, text="检测中...", font=("", 9, "bold"),
                                      bg=self.colors['card'], fg=self.colors['text_secondary'])
        self.status_label.pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Checkbutton(left, text="开机自启", variable=self.service_enabled,
                        command=self.toggle_autostart).pack(side=tk.LEFT)
        
        # 右侧刷新
        tk.Button(bar, text="🔄", font=("", 9), relief=tk.FLAT, cursor="hand2",
                  bg=self.colors['card'], command=self.update_service_status).pack(side=tk.RIGHT, padx=10)
    
    def create_schedule_tab(self):
        """定时任务标签页"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text=" 📅 定时设置 ")
        
        # 清理时间
        group1 = ttk.LabelFrame(tab, text="定时清理", padding=10)
        group1.pack(fill=tk.X, pady=(0, 10))
        
        row1 = ttk.Frame(group1)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="每日清理时间:").pack(side=tk.LEFT)
        
        self.cleanup_hour = ttk.Combobox(row1, values=[f"{h:02d}" for h in range(24)], 
                                          width=4, state="readonly")
        self.cleanup_hour.set("18")
        self.cleanup_hour.pack(side=tk.LEFT, padx=(10, 2))
        ttk.Label(row1, text=":").pack(side=tk.LEFT)
        self.cleanup_minute = ttk.Combobox(row1, values=[f"{m:02d}" for m in range(0, 60, 5)],
                                            width=4, state="readonly")
        self.cleanup_minute.set("00")
        self.cleanup_minute.pack(side=tk.LEFT, padx=(2, 0))
        
        # 执行频率
        row_freq = ttk.Frame(group1)
        row_freq.pack(fill=tk.X, pady=2)
        ttk.Label(row_freq, text="执行频率:").pack(side=tk.LEFT)
        self.freq_combo = ttk.Combobox(row_freq, width=15, state="readonly",
                                       values=["每天 (Daily)", "每周 (Weekly)", "每月 (Monthly)"])
        self.freq_combo.set("每天 (Daily)")
        self.freq_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # 间隔执行模式
        row_interval = ttk.Frame(group1)
        row_interval.pack(fill=tk.X, pady=2)
        ttk.Label(row_interval, text="高频后台巡逻:").pack(side=tk.LEFT)
        self.interval_combo = ttk.Combobox(row_interval, width=15, state="readonly",
                                          values=["关闭 (按计划执行)", "每隔 2 小时", "每隔 4 小时", "每隔 8 小时", "每隔 12 小时"])
        self.interval_combo.set("关闭 (按计划执行)")
        self.interval_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # 开机立即运行
        row_broot = ttk.Frame(group1)
        row_broot.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(row_broot, text="每次开机时自动执行一次后台系统清理", 
                        variable=self.broot_enabled).pack(side=tk.LEFT, padx=0)
        
        row2 = ttk.Frame(group1)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="提前提醒:").pack(side=tk.LEFT)
        self.notify_combo = ttk.Combobox(row2, values=[1, 3, 5, 10, 15, 30], width=4, state="readonly")
        self.notify_combo.set("5")
        self.notify_combo.pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(row2, text="分钟").pack(side=tk.LEFT)
        
        # 定时关机
        group2 = ttk.LabelFrame(tab, text="定时关机", padding=10)
        group2.pack(fill=tk.X, pady=(0, 10))
        
        row3 = ttk.Frame(group2)
        row3.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(row3, text="启用定时关机", variable=self.shutdown_enabled,
                        command=self.toggle_shutdown).pack(side=tk.LEFT)
        
        row4 = ttk.Frame(group2)
        row4.pack(fill=tk.X, pady=2)
        ttk.Label(row4, text="关机时间:").pack(side=tk.LEFT)
        self.shutdown_hour = ttk.Combobox(row4, values=[f"{h:02d}" for h in range(24)],
                                           width=4, state="readonly")
        self.shutdown_hour.set("23")
        self.shutdown_hour.pack(side=tk.LEFT, padx=(10, 2))
        ttk.Label(row4, text=":").pack(side=tk.LEFT)
        self.shutdown_minute = ttk.Combobox(row4, values=[f"{m:02d}" for m in range(0, 60, 5)],
                                             width=4, state="readonly")
        self.shutdown_minute.set("00")
        self.shutdown_minute.pack(side=tk.LEFT, padx=(2, 0))
        
        ttk.Label(group2, text="⚠ 关机前10分钟会收到提醒通知", 
                  foreground=self.colors['warning']).pack(anchor=tk.W, pady=(5, 0))
    
    def create_cleanup_tab(self):
        """清理设置标签页"""
        tab_container = ttk.Frame(self.notebook)
        self.notebook.add(tab_container, text=" 🗑️ 清理设置 ")
        
        # 添加滚动条支持
        canvas = tk.Canvas(tab_container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab_container, orient="vertical", command=canvas.yview)
        tab = ttk.Frame(canvas, padding=15)
        
        tab.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=tab, anchor="nw", 
                             width=canvas.winfo_reqwidth())
        
        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            # Windows/Mac
            if event.delta:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            # Linux (X11)
            elif event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
                
        # 针对 Linux 和 Windows 的滚轮绑定
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)
        
        # 当画布调整大小时，也调整内部 frame 的宽度
        def _configure_canvas(event):
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)
        canvas.bind("<Configure>", _configure_canvas)

        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 清理目录
        group1 = ttk.LabelFrame(tab, text="清理目录", padding=10)
        group1.pack(fill=tk.X, pady=(0, 10))
        
        dir_frame = ttk.Frame(group1)
        dir_frame.pack(fill=tk.X)
        
        dir_names = {'Desktop': '桌面', 'Downloads': '下载', 'Documents': '文档',
                     'Pictures': '图片', 'Videos': '视频', 'Trash': '回收站'}
        
        for i, (key, name) in enumerate(dir_names.items()):
            ttk.Checkbutton(dir_frame, text=name, variable=self.dirs[key]).grid(
                row=i//3, column=i%3, sticky=tk.W, padx=10, pady=2)
                
        # 浏览器清理独立选项        
        ttk.Checkbutton(group1, text="深度清理常用浏览器缓直 (Firefox, Chrome, Edge, 360等)", 
                        variable=self.dirs['Browsers']).pack(anchor=tk.W, padx=10, pady=(5,0))
                        
        # 系统级垃圾清理精细化选项
        sys_group = ttk.LabelFrame(group1, text="高级系统清理")
        sys_group.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Checkbutton(sys_group, text="清理陈旧的 APT 安装包缓直", variable=self.dirs['SysApt']).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Checkbutton(sys_group, text="清理 Systemd 历史运行日志 (保留最近7天)", variable=self.dirs['SysJournal']).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Checkbutton(sys_group, text="清理陈旧的图片与视频缩略图缓直", variable=self.dirs['SysThumbnails']).pack(anchor=tk.W, padx=5, pady=2)
        
        # 清理模式
        group2 = ttk.LabelFrame(tab, text="清理模式", padding=10)
        group2.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Radiobutton(group2, text="清理全部文件（保留排除扩展名）", 
                        variable=self.cleanup_mode, value="all").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(group2, text="仅清理指定扩展名的文件",
                        variable=self.cleanup_mode, value="ext_only").pack(anchor=tk.W, pady=2)
        
        # 扩展名设置
        group3 = ttk.LabelFrame(tab, text="扩展名设置", padding=10)
        group3.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(group3, text="清理扩展名 (逗号分隔):").pack(anchor=tk.W)
        self.cleanup_ext = ttk.Entry(group3, width=50)
        self.cleanup_ext.insert(0, DEFAULT_CONFIG['cleanup_extensions'])
        self.cleanup_ext.pack(fill=tk.X, pady=(2, 8))
        
        ttk.Label(group3, text="排除扩展名 (不会被清理):").pack(anchor=tk.W)
        self.exclude_ext = ttk.Entry(group3, width=50)
        self.exclude_ext.insert(0, DEFAULT_CONFIG['exclude_extensions'])
        self.exclude_ext.pack(fill=tk.X, pady=(2, 0))
        self.exclude_ext.pack(fill=tk.X, pady=(2, 0))
    
    def create_action_tab(self):
        """快捷操作标签页"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text=" 🛡 快捷操作 ")
        
        # 服务控制
        group1 = ttk.LabelFrame(tab, text="服务控制", padding=10)
        group1.pack(fill=tk.X, pady=(0, 10))
        
        btn_frame = ttk.Frame(group1)
        btn_frame.pack(fill=tk.X)
        
        self._create_flat_button(btn_frame, "▶ 启动服务", self.colors['success'], 
                                   self.start_service, width=12).pack(side=tk.LEFT, padx=(0, 8))
        
        self._create_flat_button(btn_frame, "■ 停止服务", self.colors['danger'], 
                                   self.stop_service, width=12).pack(side=tk.LEFT, padx=(0, 8))
        
        self._create_flat_button(btn_frame, "↻ 重启服务", self.colors['warning'], 
                                   self.restart_service, width=12).pack(side=tk.LEFT)
        
        # 清理操作
        group2 = ttk.LabelFrame(tab, text="清理操作", padding=10)
        group2.pack(fill=tk.X, pady=(0, 10))
        
        self._create_flat_button(group2, "🗑 立即执行清理", self.colors['primary'], 
                                   self.run_cleanup_now, font=("微软雅黑", 10, "bold")).pack(fill=tk.X, pady=2)
        
        ttk.Label(group2, text="将根据当前保直的设置执行清理",
                  foreground=self.colors['text_secondary']).pack(anchor=tk.W, pady=(2, 0))
        
        # 日志查看
        group3 = ttk.LabelFrame(tab, text="运行日志", padding=10)
        group3.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self._create_flat_button(group3, "📋 查看运行日志", "#8e44ad", 
                                   self.show_logs).pack(anchor=tk.W)
    
    def create_bottom_buttons(self):
        """底部按钮"""
        bottom = tk.Frame(self.rroot, bg=self.colors['bg'])
        bottom.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self._create_flat_button(bottom, "💾 保直设置", self.colors['success'], 
                                   self.save_config, width=12, font=("微软雅黑", 10, "bold")).pack(side=tk.RIGHT)
        
        self._create_flat_button(bottom, "↩ 恢复默认", self.colors['secondary'], 
                                   self.reset_to_default, width=12).pack(side=tk.RIGHT, padx=(0, 8))
    
    # ========== 功能方法 ==========
    
    def toggle_autostart(self):
        """切换自启动"""
        enabled = self.service_enabled.get()
        try:
            cmd_args = "enable" if enabled else "disable"
            subprocess.run(get_elevate_cmd() + ["systemctl", cmd_args, SERVICE_NAME],
                           check=True, capture_output=True)
            messagebox.showinfo("成功", f"已{'启用' if enabled else '禁用'}开机自启动")
        except:
            messagebox.showerror("错误", "操作失败")
            self.service_enabled.set(not enabled)
        self.update_service_status()
    
    def toggle_shutdown(self):
        """切换关机设置"""
        state = "readonly" if self.shutdown_enabled.get() else "disabled"
        self.shutdown_hour.configure(state=state)
        self.shutdown_minute.configure(state=state)
    
    def update_service_status(self):
        """更新服务状态"""
        def check():
            try:
                result = subprocess.run(["systemctl", "is-active", SERVICE_NAME],
                                        capture_output=True, text=True)
                active = result.returncode == 0
                
                result = subprocess.run(["systemctl", "is-enabled", SERVICE_NAME],
                                        capture_output=True, text=True)
                enabled = result.returncode == 0
                
                self.rroot.after(0, lambda: self._update_status_ui(active, enabled))
            except:
                self.rroot.after(0, lambda: self.status_label.config(text="未知", fg="gray"))
        
        threading.Thread(target=check, daemon=True).start()
    
    def _update_status_ui(self, active, enabled):
        """更新状态UI"""
        if active:
            self.status_label.config(text="✔ 运行中", fg=self.colors['success'])
        else:
            self.status_label.config(text="✘ 已停止", fg=self.colors['danger'])
        self.service_enabled.set(enabled)
    
    def load_config(self):
        """加载配置"""
        if not os.path.exists(CONFIG_FILE):
            return
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                content = f.read()
            
            for line in content.split('\n'):
                line = line.strip()
                if '=' not in line or line.startswith('#'):
                    continue
                
                key, val = line.split('=', 1)
                val = val.strip('"')
                
                if key == 'CLEANUP_TIME' and ':' in val:
                    h, m = val.split(':')
                    self.cleanup_hour.set(h)
                    self.cleanup_minute.set(m)
                elif key == 'SHUTDOWN_TIME' and ':' in val:
                    h, m = val.split(':')
                    self.shutdown_hour.set(h)
                    self.shutdown_minute.set(m)
                elif key == 'SHUTDOWN_ENABLED':
                    self.shutdown_enabled.set(val.lower() == 'yes')
                elif key == 'NOTIFICATION_MINUTES':
                    self.notify_combo.set(val)
                elif key == 'CLEANUP_EXTENSIONS':
                    self.cleanup_ext.delete(0, tk.END)
                    self.cleanup_ext.insert(0, val)
                elif key == 'EXCLUDE_EXTENSIONS':
                    self.exclude_ext.delete(0, tk.END)
                    self.exclude_ext.insert(0, val)
                elif key == 'CLEANUP_MODE':
                    self.cleanup_mode.set(val)
                elif key == 'CLEANUP_DIRS':
                    dirs = val.split(',')
                    for d in dir_names.keys():
                        self.dirs[d].set(d in dirs)
                elif key == 'CLEANUP_BROWSERS':
                    self.dirs['Browsers'].set(val.lower() == 'yes')
                elif key == 'CLEANUP_SYS_APT':
                    self.dirs['SysApt'].set(val.lower() == 'yes')
                elif key == 'CLEANUP_SYS_JOURNAL':
                    self.dirs['SysJournal'].set(val.lower() == 'yes')
                elif key == 'CLEANUP_SYS_THUMBNAILS':
                    self.dirs['SysThumbnails'].set(val.lower() == 'yes')
                elif key == 'CLEANUP_FREQUENCY':
                    freq_map = {'daily': 0, 'weekly': 1, 'monthly': 2}
                    self.freq_combo.current(freq_map.get(val.lower(), 0))
                elif key == 'CLEANUP_ON_BOOT':
                    self.broot_enabled.set(val.lower() == 'yes')
                elif key == 'CLEANUP_INTERVAL':
                    interval_map = {'0': 0, '2': 1, '4': 2, '8': 3, '12': 4}
                    self.interval_combo.current(interval_map.get(val, 0))
        except Exception as e:
            print(f"加载配置失败: {e}")
        
        self.toggle_shutdown()
    
    def save_config(self):
        """保直配置"""
        cleanup_time = f"{self.cleanup_hour.get()}:{self.cleanup_minute.get()}"
        shutdown_time = f"{self.shutdown_hour.get()}:{self.shutdown_minute.get()}"
        
        dirs = [d for d, v in self.dirs.items() if d not in ('Browsers', 'SysApt', 'SysJournal', 'SysThumbnails') and v.get()]
        clean_browsers = 'yes' if self.dirs['Browsers'].get() else 'no'
        sys_apt = 'yes' if self.dirs['SysApt'].get() else 'no'
        sys_jour = 'yes' if self.dirs['SysJournal'].get() else 'no'
        sys_thumb = 'yes' if self.dirs['SysThumbnails'].get() else 'no'
        
        broot_run = 'yes' if self.broot_enabled.get() else 'no'
        freq_list = ['daily', 'weekly', 'monthly']
        freq = freq_list[self.freq_combo.current()]
        
        interval_opts = ['0', '2', '4', '8', '12']
        interval = interval_opts[self.interval_combo.current()]
        
        config = f'''# Kylin / openKylin 清理工具配置文件
CLEANUP_TIME="{cleanup_time}"
NOTIFICATION_MINUTES="{self.notify_combo.get()}"
SHUTDOWN_TIME="{shutdown_time}"
SHUTDOWN_ENABLED="{'yes' if self.shutdown_enabled.get() else 'no'}"
CLEANUP_EXTENSIONS="{self.cleanup_ext.get().strip()}"
EXCLUDE_EXTENSIONS="{self.exclude_ext.get().strip()}"
CLEANUP_MODE="{self.cleanup_mode.get()}"
CLEANUP_DIRS="{','.join(dirs)}"
CLEANUP_BROWSERS="{clean_browsers}"
CLEANUP_SYS_APT="{sys_apt}"
CLEANUP_SYS_JOURNAL="{sys_jour}"
CLEANUP_SYS_THUMBNAILS="{sys_thumb}"
CLEANUP_FREQUENCY="{freq}"
CLEANUP_ON_BOOT="{broot_run}"
CLEANUP_INTERVAL="{interval}"
'''
        try:
            # 1. 尝试直接写入 (配合 postinst 设置的 666 权限可免弹窗)
            try:
                with open(CONFIG_FILE, 'w') as f:
                    f.write(config)
                messagebox.showinfo("成功", "设置已保直！")
                return
            except PermissionError:
                # 2. 如果直接写入失败，再调用提权命令（弹出密码框）
                p = subprocess.Popen(get_elevate_cmd() + ["tee", CONFIG_FILE],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate(input=config.encode())
                if p.returncode == 0:
                    messagebox.showinfo("成功", "设置已保直！")
                else:
                    messagebox.showerror("失败", "无法写入配置文件，请检查权限")
        except Exception as e:
            messagebox.showerror("错误", f"保直失败: {e}")
    
    def reset_to_default(self):
        """恢复默认"""
        if messagebox.askyesno("确认", "确定恢复默认设置吗？"):
            self.cleanup_hour.set("18")
            self.cleanup_minute.set("00")
            self.notify_combo.set("5")
            self.shutdown_hour.set("23")
            self.shutdown_minute.set("00")
            self.shutdown_enabled.set(True)
            self.cleanup_ext.delete(0, tk.END)
            self.cleanup_ext.insert(0, DEFAULT_CONFIG['cleanup_extensions'])
            self.exclude_ext.delete(0, tk.END)
            self.exclude_ext.insert(0, DEFAULT_CONFIG['exclude_extensions'])
            self.cleanup_mode.set("all")
            for d in ['Desktop', 'Downloads', 'Documents', 'Pictures', 'Videos', 'Trash']:
                self.dirs[d].set(True)
            self.dirs['Browsers'].set(DEFAULT_CONFIG.get('cleanup_browsers', 'yes') == 'yes')
            self.dirs['SysApt'].set(DEFAULT_CONFIG.get('cleanup_sys_apt', 'no') == 'yes')
            self.dirs['SysJournal'].set(DEFAULT_CONFIG.get('cleanup_sys_journal', 'no') == 'yes')
            self.dirs['SysThumbnails'].set(DEFAULT_CONFIG.get('cleanup_sys_thumbnails', 'no') == 'yes')
            self.freq_combo.current(0)
            self.interval_combo.current(0)
            self.broot_enabled.set(False)
            self.toggle_shutdown()
            messagebox.showinfo("提示", "已恢复默认，请点击保直生效")
    
    def start_service(self):
        """启动服务"""
        try:
            subprocess.run(get_elevate_cmd() + ["systemctl", "start", SERVICE_NAME], check=True, capture_output=True)
            messagebox.showinfo("成功", "服务已启动")
            self.update_service_status()
        except:
            messagebox.showerror("错误", "启动失败")
    
    def stop_service(self):
        """停止服务"""
        try:
            subprocess.run(get_elevate_cmd() + ["systemctl", "stop", SERVICE_NAME], check=True, capture_output=True)
            messagebox.showinfo("成功", "服务已停止")
            self.update_service_status()
        except:
            messagebox.showerror("错误", "停止失败")
    
    def restart_service(self):
        """重启服务"""
        try:
            subprocess.run(get_elevate_cmd() + ["systemctl", "restart", SERVICE_NAME], check=True, capture_output=True)
            messagebox.showinfo("成功", "服务已重启")
            self.update_service_status()
        except:
            messagebox.showerror("错误", "重启失败")
    
    def run_cleanup_now(self):
        """立即清理"""
        if messagebox.askyesno("确认", "确定立即执行清理吗？"):
            try:
                subprocess.Popen(get_elevate_cmd() + ["python3", "/opt/kylin-clean/clean_linux.py", "--once"])
                messagebox.showinfo("提示", "清理任务已启动")
            except Exception as e:
                messagebox.showerror("错误", f"启动失败: {e}")
    
    def show_logs(self):
        """显示日志"""
        win = tk.Toplevel(self.rroot)
        win.title("运行日志")
        win.geometry("600x400")
        win.transient(self.rroot)
        
        text = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Consolas", 9))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        log_paths = ["/opt/kylin-clean/cleanup_and_shutdown.log", "/tmp/kylin-clean.log"]
        content = "暂无日志"
        
        for path in log_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = "".join(f.readlines()[-100:])
                    break
                except:
                    pass
        
        text.insert(tk.END, content)
        text.config(state=tk.DISABLED)
        text.see(tk.END)
        
        tk.Button(win, text="关闭", command=win.destroy, width=8).pack(pady=8)


def main():
    rroot = tk.Tk()
    try:
        rroot.iconphoto(True, tk.PhotoImage(file="/opt/kylin-clean/icon.png"))
    except:
        pass
    KylinCleanupSettings(rroot)
    rroot.mainloop()


if __name__ == "__main__":
    main()
