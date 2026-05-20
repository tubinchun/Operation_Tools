#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Kylin / openKylin 清理工具 - 图形化设置界面 (Qt Version)
# 程序作者: Genwang Ye

import sys
import os
import subprocess
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QLabel, QPushButton, 
                             QCheckBox, QComboBox, QTimeEdit, QLineEdit, 
                             QRadioButton, QButtonGroup, QGroupBox, QTextEdit, 
                             QMessageBox, QScrollArea, QFrame, QSizePolicy, QProgressBar,
                             QPlainTextEdit, QDialog)
import shutil
import io

try:
    import qrcode
except ImportError:
    qrcode = None
    
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QIcon, QFont, QPixmap, QImage

try:
    import license_manager
except ImportError:
    license_manager = None

try:
    import ui_assets
except ImportError:
    ui_assets = None

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
    'shutdown_time': '20:00',
    'shutdown_enabled': True,
    'notification_minutes': 5,
    'shutdown_notification_minutes': 10,
    'cleanup_extensions': '.tmp,.log,.bak,.cache,.swp,.xlsx,.xls,.doc,.docx,.jpg,.jpeg,.rar,.zip,.ppt,.pdf,.pptx,.png,.txt,.wps,.wpt,.et,.ett,.dps,.dpt,.ofd',
    'exclude_extensions': '.ico,.desktop',
    'cleanup_mode': 'all',
    'cleanup_dirs': 'Desktop,Downloads,Documents,Pictures,Videos,Trash',
    'cleanup_browsers': 'yes',
    'cleanup_sys_apt': 'no',
    'cleanup_sys_journal': 'no',
    'cleanup_sys_thumbnails': 'no',
    'cleanup_frequency': 'daily',  # daily, weekly, monthly
    'cleanup_on_boot': 'no',
    'cleanup_interval': '0'        # 0=off, otherwise hours (e.g., 2, 4, 8)
}

class KylinCleanupSettings(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 导出扁平化图标
        if ui_assets:
            self.icon_paths = ui_assets.export_icons("/opt/kylin-clean/icons")
        else:
            self.icon_paths = {}
            
        # 激活验证拦截
        if license_manager and not license_manager.check_active():
            # The instruction's dialog creation here is redundant with show_activation_dialog
            # Keeping the original call to show_activation_dialog which handles dialog creation
            if not self.show_activation_dialog():
                sys.exit(0) # 用户取消或关闭了激活界面，直接退出
                
        self.setWindowTitle("麒麟清理工具设置")
        self.resize(650, 720)
        self.setMinimumSize(580, 620)
        
        # 设置应用图标
        self.setWindowIcon(self._get_icon("preferences-system", "kylin-cleanup-settings.svg"))

        # 初始化数据
        self.config = DEFAULT_CONFIG.copy()
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)

        # 1. 顶部状态栏
        self.create_status_bar()
        
        # 2. 标签页
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        self.create_schedule_tab()
        self.create_cleanup_tab()
        self.create_action_tab()
        
        # 3. 底部按钮
        self.create_bottom_buttons()
        
        # 加载配置
        self.load_config()
        
        # 定时更新服务状态
        self.update_service_timer = QTimer(self)
        self.update_service_timer.timeout.connect(self.check_service_status)
        self.update_service_timer.start(5000) # 每5秒刷新一次
        self.check_service_status() # 立即检查一次
        
        # 磁盘容量更新
        self.update_disk_timer = QTimer(self)
        self.update_disk_timer.timeout.connect(self.update_disk_usage)
        self.update_disk_timer.start(10000) # 每10秒刷新
        self.update_disk_usage()

    def show_activation_dialog(self):
        """显示未授权拦截的激活二维码对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("麒麟清理工具 - 软件激活")
        dialog.setFixedSize(540, 620)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dialog.setStyleSheet("QDialog { background-color: #f7f9fc; }")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # 头部区域
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #e1e4e8;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 15, 15, 15)
        
        main_title = QLabel("欢迎使用增强版系统清理助手")
        main_title.setAlignment(Qt.AlignCenter)
        main_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(main_title)
        
        sub_title = QLabel("此设备尚未激活，请使用手机扫描下方二维码获取授权码")
        sub_title.setAlignment(Qt.AlignCenter)
        sub_title.setStyleSheet("font-size: 13px; color: #7f8c8d; margin-top: 5px;")
        header_layout.addWidget(sub_title)
        
        layout.addWidget(header_frame)
        
        # 二维码区域 (带阴影感背景)
        qr_frame = QFrame()
        qr_frame.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #e1e4e8;")
        qr_layout = QVBoxLayout(qr_frame)
        qr_layout.setContentsMargins(20, 20, 20, 20)
        
        if qrcode:
            qr_url = license_manager.parse_qr_activation_url()
            qr = qrcode.QRCode(version=None, box_size=5, border=2)
            qr.add_data(qr_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#2c3e50", back_color="white")
            
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            qimage = QImage()
            qimage.loadFromData(img_buffer.getvalue())
            pixmap = QPixmap.fromImage(qimage)
            
            qr_label = QLabel()
            # 允许等比缩小避免越界
            qr_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            qr_label.setFixedSize(200, 200)
            qr_label.setAlignment(Qt.AlignCenter)
            qr_layout.addWidget(qr_label)
        else:
            qr_label = QLabel()
            qr_label.setText("⚠ 未能加载二维码依赖\\n请先联网安装 python3-qrcode 库")
            qr_label.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold; padding: 40px;")
            qr_label.setAlignment(Qt.AlignCenter)
            qr_layout.addWidget(qr_label)
            
        layout.addWidget(qr_frame, alignment=Qt.AlignCenter)
        
        # 机器码显示 (仿代码块设计)
        mc = license_manager.get_machine_code()
        mc_frame = QFrame()
        mc_frame.setStyleSheet("background-color: #edf2f7; border-radius: 6px; padding: 10px;")
        mc_layout = QHBoxLayout(mc_frame)
        mc_layout.setContentsMargins(10, 5, 10, 5)
        
        mc_title = QLabel("本设备机器码：")
        mc_title.setStyleSheet("color: #4a5568; font-size: 13px;")
        mc_layout.addWidget(mc_title)
        
        mc_val = QLabel(mc)
        mc_val.setStyleSheet("color: #2b6cb0; font-size: 14px; font-weight: bold; font-family: monospace;")
        mc_layout.addWidget(mc_val)
        mc_layout.addStretch()
        
        layout.addWidget(mc_frame)
        
        layout.addStretch()
        
        # 底部输入区
        input_layout = QHBoxLayout()
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("在此输入 4 位数字激活码")
        self.key_input.setMaxLength(4)
        # 只允许输入数字
        from PyQt5.QtGui import QIntValidator
        self.key_input.setValidator(QIntValidator(0, 9999))
        self.key_input.setStyleSheet("padding: 10px 15px; font-size: 14px; border: 1px solid #cbd5e0; border-radius: 5px; background: white;")
        input_layout.addWidget(self.key_input)
        
        verify_btn = QPushButton("验证激活")
        verify_btn.setCursor(Qt.PointingHandCursor)
        verify_btn.setStyleSheet("""
            QPushButton {
                background-color: #38a169; color: white; font-weight: bold; font-size: 14px; 
                padding: 10px 20px; border-radius: 5px; border: none;
            }
            QPushButton:hover { background-color: #2f855a; }
            QPushButton:pressed { background-color: #276749; }
        """)
        verify_btn.clicked.connect(lambda: self.verify_key(dialog))
        input_layout.addWidget(verify_btn)
        
        layout.addLayout(input_layout)
        
        # 退出按钮
        cancel_btn = QPushButton("暂不激活 (退出程序)")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #a0aec0; font-size: 13px;
                border: none; padding: 5px; margin-top: 5px;
            }
            QPushButton:hover { color: #718096; text-decoration: underline; }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        
        return dialog.exec_() == QDialog.Accepted
        
    def verify_key(self, dialog):
        key = self.key_input.text().strip()
        if license_manager.verify_license_key(key):
            if license_manager.write_local_license(key):
                QMessageBox.information(dialog, "激活成功", "感谢您的使用！增强版清理功能已永久解锁。")
                dialog.accept()
            else:
                QMessageBox.critical(dialog, "权限错误", "激活码正确，但写入授权文件失败，请确保以管理员权限运行。")
        else:
            QMessageBox.warning(dialog, "激活失败", "激活码无效或与本机不匹配，请检查后重试。")

    def create_status_bar(self):
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_frame.setStyleSheet("#statusFrame { background-color: #f5f5f5; border-radius: 5px; }")
        layout = QHBoxLayout(status_frame)
        layout.setContentsMargins(10, 8, 10, 8)
        
        layout.addWidget(QLabel("服务状态:"))
        
        self.status_label = QLabel("检测中...")
        self.status_label.setStyleSheet("font-weight: bold; color: gray;")
        layout.addWidget(self.status_label)
        
        layout.addStretch(1)
        
        self.autostart_check = QCheckBox("开机自启动")
        self.autostart_check.clicked.connect(self.toggle_autostart)
        layout.addWidget(self.autostart_check)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.clicked.connect(self.check_service_status)
        layout.addWidget(refresh_btn)
        
        self.main_layout.addWidget(status_frame)
        
        # 磁盘容量显示
        disk_frame = QFrame()
        disk_frame.setObjectName("diskFrame")
        disk_frame.setStyleSheet("#diskFrame { background-color: #f5f5f5; border-radius: 5px; }")
        d_layout = QVBoxLayout(disk_frame)
        d_layout.setContentsMargins(10, 8, 10, 8)
        d_layout.setSpacing(5)
        
        bg = QHBoxLayout()
        bg.addWidget(QLabel("磁盘容量 (/home):"))
        self.disk_label = QLabel("正在计算...")
        bg.addWidget(self.disk_label)
        bg.addStretch(1)
        d_layout.addLayout(bg)
        
        self.disk_bar = QProgressBar()
        self.disk_bar.setTextVisible(True)
        self.disk_bar.setStyleSheet("QProgressBar { border: 1px solid grey; border-radius: 3px; text-align: center; } QProgressBar::chunk { background-color: #3498db; }")
        d_layout.addWidget(self.disk_bar)
        
        self.main_layout.addWidget(disk_frame)

    def create_schedule_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 定时清理组
        group_clean = QGroupBox("定时清理")
        glayout_clean = QVBoxLayout(group_clean)
        
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("每日定时清理准点:"))
        self.cleanup_time_edit = QTimeEdit()
        self.cleanup_time_edit.setDisplayFormat("HH:mm")
        h1.addWidget(self.cleanup_time_edit)
        h1.addStretch(1)
        glayout_clean.addLayout(h1)
        
        # 执行频率
        hfreq = QHBoxLayout()
        hfreq.addWidget(QLabel("执行频率:"))
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["每天 (Daily)", "每周 (Weekly)", "每月 (Monthly)"])
        hfreq.addWidget(self.freq_combo)
        hfreq.addStretch(1)
        glayout_clean.addLayout(hfreq)
        
        # 间隔执行模式
        hinterval = QHBoxLayout()
        hinterval.addWidget(QLabel("高频后台巡逻:"))
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["关闭 (按计划执行)", "每隔 2 小时", "每隔 4 小时", "每隔 8 小时", "每隔 12 小时"])
        hinterval.addWidget(self.interval_combo)
        hinterval.addStretch(1)
        glayout_clean.addLayout(hinterval)
        
        # 开机立即清理
        hboot = QHBoxLayout()
        self.boot_check = QCheckBox("每次开机时自动执行一次后台系统清理")
        hboot.addWidget(self.boot_check)
        hboot.addStretch(1)
        glayout_clean.addLayout(hboot)
        
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("提前提醒:"))
        self.notify_combo = QComboBox()
        self.notify_combo.addItems(["1", "3", "5", "10", "15", "30"])
        h2.addWidget(self.notify_combo)
        h2.addWidget(QLabel("分钟"))
        h2.addStretch(1)
        glayout_clean.addLayout(h2)
        
        layout.addWidget(group_clean)
        
        # 定时关机组
        group_shutdown = QGroupBox("定时关机")
        glayout_shutdown = QVBoxLayout(group_shutdown)
        
        self.shutdown_check = QCheckBox("启用定时关机")
        self.shutdown_check.toggled.connect(self.toggle_shutdown_widgets)
        glayout_shutdown.addWidget(self.shutdown_check)
        
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("每日关机时间:"))
        self.shutdown_time_edit = QTimeEdit()
        self.shutdown_time_edit.setDisplayFormat("HH:mm")
        h3.addWidget(self.shutdown_time_edit)
        h3.addStretch(1)
        glayout_shutdown.addLayout(h3)
        
        warn_label = QLabel("⚠ 关机前 10 分钟会收到系统通知提醒")
        warn_label.setStyleSheet("color: #e67e22; font-size: 11px;")
        glayout_shutdown.addWidget(warn_label)
        
        layout.addWidget(group_shutdown)
        layout.addStretch(1)
        
        self.tabs.addTab(tab, QIcon.fromTheme("alarm"), "定时任务")

    def create_cleanup_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 滚动区域以防内容过多
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(15)
        
        # 清理目录
        group_dirs = QGroupBox("清理目录")
        glayout_dirs = QVBoxLayout(group_dirs)
        
        self.dir_checks = {}
        dirs_layout = QVBoxLayout() # 使用网格布局可能更好，这里保持简单列表或多列
        
        # 使用网格排列目录选项
        grid = QHBoxLayout()
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()
        
        dirs_list = [
            ('Desktop', '桌面'), ('Downloads', '下载'), ('Documents', '文档'),
            ('Pictures', '图片'), ('Videos', '视频'), ('Trash', '回收站')
        ]
        
        for i, (key, name) in enumerate(dirs_list):
            cb = QCheckBox(name)
            self.dir_checks[key] = cb
            if i % 2 == 0:
                col1.addWidget(cb)
            else:
                col2.addWidget(cb)
        
        grid.addLayout(col1)
        grid.addLayout(col2)
        glayout_dirs.addLayout(grid)
        
        # 浏览器清理独立选项
        self.browser_check = QCheckBox("深度清理常用浏览器缓存 (Firefox, Chrome, Edge, 360等)")
        self.browser_check.setStyleSheet("color: #2980b9; font-weight: bold; margin-top: 5px;")
        glayout_dirs.addWidget(self.browser_check)
        
        # 系统深层垃圾精细化选项
        sys_group = QGroupBox("高级系统清理")
        sys_group.setStyleSheet("QGroupBox { color: #e67e22; font-weight: bold; }")
        sys_layout = QVBoxLayout(sys_group)
        sys_layout.setContentsMargins(5, 10, 5, 5)
        
        self.sys_apt_check = QCheckBox("清理陈旧的 APT 安装包缓存 (释放大量系统盘空间)")
        self.sys_journal_check = QCheckBox("清理 Systemd 历史运行日志 (仅保留最近7天)")
        self.sys_thumbnails_check = QCheckBox("清理陈旧的图片与视频缩略图缓存")
        
        sys_layout.addWidget(self.sys_apt_check)
        sys_layout.addWidget(self.sys_journal_check)
        sys_layout.addWidget(self.sys_thumbnails_check)
        
        glayout_dirs.addWidget(sys_group)
        
        content_layout.addWidget(group_dirs)
        
        # 清理模式
        group_mode = QGroupBox("清理模式")
        glayout_mode = QVBoxLayout(group_mode)
        
        self.mode_group = QButtonGroup(self)
        self.radio_all = QRadioButton("清理全部文件 (保留排除扩展名)")
        self.radio_ext = QRadioButton("仅清理指定扩展名的文件")
        self.mode_group.addButton(self.radio_all, 1)
        self.mode_group.addButton(self.radio_ext, 2)
        
        glayout_mode.addWidget(self.radio_all)
        glayout_mode.addWidget(self.radio_ext)
        content_layout.addWidget(group_mode)
        
        # 扩展名设置
        group_ext = QGroupBox("扩展名设置")
        glayout_ext = QVBoxLayout(group_ext)
        
        glayout_ext.addWidget(QLabel("清理扩展名 (逗号分隔):"))
        self.edit_cleanup_ext = QPlainTextEdit()
        self.edit_cleanup_ext.setPlainText(DEFAULT_CONFIG['cleanup_extensions'])
        self.edit_cleanup_ext.setMaximumHeight(60)
        self.edit_cleanup_ext.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        glayout_ext.addWidget(self.edit_cleanup_ext)
        
        glayout_ext.addWidget(QLabel("排除扩展名 (不会被清理):"))
        self.edit_exclude_ext = QPlainTextEdit()
        self.edit_exclude_ext.setPlainText(DEFAULT_CONFIG['exclude_extensions'])
        self.edit_exclude_ext.setMaximumHeight(40)
        self.edit_exclude_ext.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        glayout_ext.addWidget(self.edit_exclude_ext)
        
        content_layout.addWidget(group_ext)
        
        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        self.tabs.addTab(tab, self._get_icon("user-trash", "cleanup"), "清理设置")

    def create_action_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 服务控制
        group_svc = QGroupBox("服务控制")
        glayout_svc = QHBoxLayout(group_svc)
        
        btn_start = QPushButton("启动服务")
        btn_start.setIcon(self._get_icon("media-playback-start", "start"))
        btn_start.clicked.connect(self.start_service)
        glayout_svc.addWidget(btn_start)
        
        btn_stop = QPushButton("停止服务")
        btn_stop.setIcon(self._get_icon("media-playback-stop", "stop"))
        btn_stop.clicked.connect(self.stop_service)
        glayout_svc.addWidget(btn_stop)
        
        btn_restart = QPushButton("重启服务")
        btn_restart.setIcon(self._get_icon("system-reboot", "restart"))
        btn_restart.clicked.connect(self.restart_service)
        glayout_svc.addWidget(btn_restart)
        
        layout.addWidget(group_svc)
        
        # 立即清理
        group_now = QGroupBox("清理操作")
        glayout_now = QVBoxLayout(group_now)
        
        btn_clean = QPushButton(" 立即执行清理")
        btn_clean.setIcon(self._get_icon("user-trash", "cleanup"))
        btn_clean.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        btn_clean.clicked.connect(self.run_cleanup_now)
        glayout_now.addWidget(btn_clean)
        
        info_label = QLabel("将根据当前的「清理设置」立即执行一次任务")
        info_label.setStyleSheet("color: gray; font-size: 11px;")
        info_label.setAlignment(Qt.AlignCenter)
        glayout_now.addWidget(info_label)
        
        layout.addWidget(group_now)
        
        # 日志
        group_log = QGroupBox("运行日志 (最后100行)")
        glayout_log = QVBoxLayout(group_log)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Monospace"))
        glayout_log.addWidget(self.log_text)
        
        btn_refresh_log = QPushButton("刷新日志")
        btn_refresh_log.clicked.connect(self.load_logs)
        glayout_log.addWidget(btn_refresh_log)
        
        layout.addWidget(group_log)
        self.tabs.addTab(tab, self._get_icon("utilities-terminal", "admin"), "快捷操作")

    def create_bottom_buttons(self):
        layout = QHBoxLayout()
        layout.addStretch(1)
        
        btn_reset = QPushButton("恢复默认")
        btn_reset.setIcon(self._get_icon("edit-undo", "reset"))
        btn_reset.clicked.connect(self.reset_to_default)
        layout.addWidget(btn_reset)
        
        btn_save = QPushButton(" 保存设置")
        btn_save.setIcon(self._get_icon("document-save", "save"))
        btn_save.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 8px 25px; border-radius: 5px;")
        btn_save.clicked.connect(self.save_config)
        layout.addWidget(btn_save)
        
        self.main_layout.addLayout(layout)

    def _get_icon(self, theme_name, icon_key=None):
        """优先使用扁平化图标，系统主题作为兜底"""
        if icon_key:
            # 1. 检查运行时的导出的图标路径
            if hasattr(self, 'icon_paths') and icon_key in self.icon_paths:
                path = self.icon_paths[icon_key]
                if os.path.exists(path):
                    return QIcon(path)
            
            # 2. 检查标准安装路径
            for folder in ["/opt/kylin-clean/icons", "/usr/share/pixmaps", "/opt/kylin-clean"]:
                exts = [".svg", ".png"]
                for ext in exts:
                    filename = f"flat_{icon_key}{ext}" if "flat_" not in icon_key else f"{icon_key}{ext}"
                    # 兼容传入带后缀的 local_name 如 kylin-cleanup.svg
                    if "." in icon_key:
                        filename = icon_key
                    
                    path = os.path.join(folder, filename)
                    if os.path.exists(path):
                        return QIcon(path)
        
        # 3. 系统主题兜底
        if QIcon.hasThemeIcon(theme_name):
            return QIcon.fromTheme(theme_name)
        
        return QIcon()

    # ========== 逻辑方法 ==========
    
    def toggle_shutdown_widgets(self):
        state = self.shutdown_check.isChecked()
        self.shutdown_time_edit.setEnabled(state)

    def check_service_status(self):
        def run_check():
            try:
                # 检查运行状态
                res_active = subprocess.run(["systemctl", "is-active", SERVICE_NAME], 
                                            capture_output=True, text=True)
                is_active = res_active.returncode == 0
                
                # 检查自启状态
                res_enabled = subprocess.run(["systemctl", "is-enabled", SERVICE_NAME], 
                                             capture_output=True, text=True)
                is_enabled = res_enabled.returncode == 0
                
                # 更新UI (需要在主线程)
                QApplication.instance().postEvent(self, UILoadEvent(is_active, is_enabled))
            except:
                pass
        
        # 简单起见，这里直接在主线程运行，或者用QThread。因为systemctl通常很快。
        # 为了避免界面卡顿，如果是很慢的操作才需要线程。systemctl query通常是毫秒级。
        try:
            res_active = subprocess.run(["systemctl", "is-active", SERVICE_NAME], 
                                        capture_output=True, text=True)
            is_active = res_active.returncode == 0
            
            res_enabled = subprocess.run(["systemctl", "is-enabled", SERVICE_NAME], 
                                         capture_output=True, text=True)
            is_enabled = res_enabled.returncode == 0
            
            if is_active:
                self.status_label.setText("✔ 运行中")
                self.status_label.setStyleSheet("font-weight: bold; color: green;")
            else:
                self.status_label.setText("✘ 已停止")
                self.status_label.setStyleSheet("font-weight: bold; color: red;")
            
            # 使用 blockSignals 防止触发 toggled 事件
            self.autostart_check.blockSignals(True)
            self.autostart_check.setChecked(is_enabled)
            self.autostart_check.blockSignals(False)
            
        except:
            self.status_label.setText("未知")

    def update_disk_usage(self):
        try:
            # 优先检查 /home，如果是同一分区则也可反映系统情况
            path = "/home" if os.path.exists("/home") else "/"
            total, used, free = shutil.disk_usage(path)
            
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            percent = int((used / total) * 100)
            
            self.disk_bar.setValue(percent)
            self.disk_label.setText(f"已用 {used_gb:.1f} GB / 总共 {total_gb:.1f} GB")
            
            # 根据使用率改变颜色
            if percent > 90:
                self.disk_bar.setStyleSheet("QProgressBar { border: 1px solid grey; border-radius: 3px; text-align: center; } QProgressBar::chunk { background-color: #e74c3c; }")
            elif percent > 75:
                self.disk_bar.setStyleSheet("QProgressBar { border: 1px solid grey; border-radius: 3px; text-align: center; } QProgressBar::chunk { background-color: #f39c12; }")
            else:
                self.disk_bar.setStyleSheet("QProgressBar { border: 1px solid grey; border-radius: 3px; text-align: center; } QProgressBar::chunk { background-color: #3498db; }")
        except:
            self.disk_label.setText("无法获取容量信息")

    def toggle_autostart(self, checked):
        action = "enable" if checked else "disable"
        try:
            subprocess.run(get_elevate_cmd() + ["systemctl", action, SERVICE_NAME], check=True)
            QMessageBox.information(self, "成功", f"开机自启动已{'启用' if checked else '禁用'}")
        except subprocess.CalledProcessError:
            QMessageBox.warning(self, "错误", "操作失败或取消")
            self.autostart_check.setChecked(not checked) # 恢复状态
        self.check_service_status()

    def start_service(self):
        self._run_systemctl("start", "启动")

    def stop_service(self):
        self._run_systemctl("stop", "停止")

    def restart_service(self):
        self._run_systemctl("restart", "重启")

    def _run_systemctl(self, action, name):
        try:
            subprocess.run(get_elevate_cmd() + ["systemctl", action, SERVICE_NAME], check=True)
            QMessageBox.information(self, "成功", f"服务已{name}")
            self.check_service_status()
        except subprocess.CalledProcessError:
            QMessageBox.warning(self, "错误", f"{name}服务失败")

    def run_cleanup_now(self):
        reply = QMessageBox.question(self, "确认", "确定根据当前配置立即执行清理吗？", 
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                subprocess.Popen(get_elevate_cmd() + ["python3", "/opt/kylin-clean/clean_linux.py", "--once"])
                QMessageBox.information(self, "提示", "清理任务已启动，请查看系统通知。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"启动失败: {e}")

    def load_logs(self):
        paths = ["/opt/kylin-clean/cleanup_and_shutdown.log", "/tmp/kylin-clean.log"]
        content = "暂无日志"
        for p in paths:
            if os.path.exists(p):
                try:
                    with open(p, 'r') as f:
                        lines = f.readlines()
                        content = "".join(lines[-100:])
                    break
                except: pass
        self.log_text.setText(content)
        # 滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
            
        try:
            with open(CONFIG_FILE, 'r') as f:
                content = f.read()
            
            cfg = self.config # 引用
            for line in content.split('\n'):
                if '=' in line and not line.strip().startswith('#'):
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"')
                    
                    if k == 'CLEANUP_TIME': self.cleanup_time_edit.setTime(QTime.fromString(v, "HH:mm"))
                    elif k == 'SHUTDOWN_TIME': self.shutdown_time_edit.setTime(QTime.fromString(v, "HH:mm"))
                    elif k == 'NOTIFICATION_MINUTES': 
                        index = self.notify_combo.findText(v)
                        if index >= 0: self.notify_combo.setCurrentIndex(index)
                    elif k == 'SHUTDOWN_ENABLED': 
                        self.shutdown_check.setChecked(v.lower() == 'yes')
                    elif k == 'CLEANUP_EXTENSIONS': self.edit_cleanup_ext.setPlainText(v)
                    elif k == 'EXCLUDE_EXTENSIONS': self.edit_exclude_ext.setPlainText(v)
                    elif k == 'CLEANUP_MODE':
                        if v == 'ext_only': self.radio_ext.setChecked(True)
                        else: self.radio_all.setChecked(True)
                    elif k == 'CLEANUP_DIRS':
                        dirs = v.split(',')
                        for key, cb in self.dir_checks.items():
                            cb.setChecked(key in dirs)
                    elif k == 'CLEANUP_BROWSERS':
                        self.browser_check.setChecked(v.lower() == 'yes')
                    elif k == 'CLEANUP_SYS_APT':
                        self.sys_apt_check.setChecked(v.lower() == 'yes')
                    elif k == 'CLEANUP_SYS_JOURNAL':
                        self.sys_journal_check.setChecked(v.lower() == 'yes')
                    elif k == 'CLEANUP_SYS_THUMBNAILS':
                        self.sys_thumbnails_check.setChecked(v.lower() == 'yes')
                    elif k == 'CLEANUP_FREQUENCY':
                        freq_map = {'daily': 0, 'weekly': 1, 'monthly': 2}
                        self.freq_combo.setCurrentIndex(freq_map.get(v.lower(), 0))
                    elif k == 'CLEANUP_ON_BOOT':
                        self.boot_check.setChecked(v.lower() == 'yes')
                    elif k == 'CLEANUP_INTERVAL':
                        interval_map = {'0': 0, '2': 1, '4': 2, '8': 3, '12': 4}
                        self.interval_combo.setCurrentIndex(interval_map.get(v, 0))
        except Exception as e:
            print(f"Error loading config: {e}")
        
        self.toggle_shutdown_widgets()
        self.load_logs()

    def save_config(self):
        # 收集数据
        cleanup_time = self.cleanup_time_edit.time().toString("HH:mm")
        shutdown_time = self.shutdown_time_edit.time().toString("HH:mm")
        shutdown_enable = "yes" if self.shutdown_check.isChecked() else "no"
        notify_min = self.notify_combo.currentText()
        clean_ext = self.edit_cleanup_ext.toPlainText().strip().replace('\n', ',')
        exclude_ext = self.edit_exclude_ext.toPlainText().strip().replace('\n', ',')
        mode = "ext_only" if self.radio_ext.isChecked() else "all"
        
        dirs = []
        for key, cb in self.dir_checks.items():
            if cb.isChecked(): dirs.append(key)
        dirs_str = ",".join(dirs)
        
        clean_browsers = "yes" if self.browser_check.isChecked() else "no"
        sys_apt = "yes" if self.sys_apt_check.isChecked() else "no"
        sys_jour = "yes" if self.sys_journal_check.isChecked() else "no"
        sys_thumb = "yes" if self.sys_thumbnails_check.isChecked() else "no"
        
        boot_run = "yes" if self.boot_check.isChecked() else "no"
        freq_list = ['daily', 'weekly', 'monthly']
        freq = freq_list[self.freq_combo.currentIndex()]
        
        interval_opts = ['0', '2', '4', '8', '12']
        interval = interval_opts[self.interval_combo.currentIndex()]
        
        config_str = f'''# Kylin / openKylin 清理工具配置文件
CLEANUP_TIME="{cleanup_time}"
NOTIFICATION_MINUTES="{notify_min}"
SHUTDOWN_TIME="{shutdown_time}"
SHUTDOWN_ENABLED="{shutdown_enable}"
CLEANUP_EXTENSIONS="{clean_ext}"
EXCLUDE_EXTENSIONS="{exclude_ext}"
CLEANUP_MODE="{mode}"
CLEANUP_DIRS="{dirs_str}"
CLEANUP_BROWSERS="{clean_browsers}"
CLEANUP_SYS_APT="{sys_apt}"
CLEANUP_SYS_JOURNAL="{sys_jour}"
CLEANUP_SYS_THUMBNAILS="{sys_thumb}"
CLEANUP_FREQUENCY="{freq}"
CLEANUP_ON_BOOT="{boot_run}"
CLEANUP_INTERVAL="{interval}"
'''
        try:
            # 1. 尝试直接写入 (如果 postinst 已经设置了 666 权限，则不需要弹窗)
            try:
                with open(CONFIG_FILE, 'w') as f:
                    f.write(config_str)
                QMessageBox.information(self, "成功", "设置已保存!")
                return
            except PermissionError:
                # 2. 如果直接写入失败，再调用提权命令（弹出密码框）
                p = subprocess.Popen(get_elevate_cmd() + ["tee", CONFIG_FILE], 
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate(input=config_str.encode())
                
                if p.returncode == 0:
                    QMessageBox.information(self, "成功", "设置已保存!")
                else:
                    QMessageBox.warning(self, "失败", "无法写入配置文件，请检查权限")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存出错: {e}")

    def reset_to_default(self):
        reply = QMessageBox.question(self, "确认", "确定恢复默认配置吗？", 
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.cleanup_time_edit.setTime(QTime.fromString(DEFAULT_CONFIG['cleanup_time'], "HH:mm"))
            self.shutdown_time_edit.setTime(QTime.fromString(DEFAULT_CONFIG['shutdown_time'], "HH:mm"))
            self.shutdown_check.setChecked(DEFAULT_CONFIG['shutdown_enabled'])
            self.notify_combo.setCurrentText(str(DEFAULT_CONFIG['notification_minutes']))
            self.edit_cleanup_ext.setPlainText(DEFAULT_CONFIG['cleanup_extensions'])
            self.edit_exclude_ext.setPlainText(DEFAULT_CONFIG['exclude_extensions'])
            self.radio_all.setChecked(True)
            self.browser_check.setChecked(DEFAULT_CONFIG['cleanup_browsers'] == 'yes')
            self.sys_apt_check.setChecked(DEFAULT_CONFIG['cleanup_sys_apt'] == 'yes')
            self.sys_journal_check.setChecked(DEFAULT_CONFIG['cleanup_sys_journal'] == 'yes')
            self.sys_thumbnails_check.setChecked(DEFAULT_CONFIG['cleanup_sys_thumbnails'] == 'yes')
            
            self.freq_combo.setCurrentIndex(0)
            self.interval_combo.setCurrentIndex(0)
            self.boot_check.setChecked(False)
            
            def_dirs = DEFAULT_CONFIG['cleanup_dirs'].split(',')
            for key, cb in self.dir_checks.items():
                cb.setChecked(key in def_dirs)
                
            self.toggle_shutdown_widgets()
            QMessageBox.information(self, "提示", "已恢复界面默认值，请点击「保存设置」生效。")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion") 
    
    window = KylinCleanupSettings()
    window.show()
    sys.exit(app.exec_())
