#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTextEdit,
    QTableWidget, QTableWidgetItem, QGroupBox,
    QFormLayout, QMessageBox, QAction, QMenuBar,
    QMenu, QStatusBar, QToolBar, QComboBox,
    QLineEdit, QSpinBox, QCheckBox, QSplitter,
    QScrollArea, QProgressBar, QDialog, QListWidget,
    QListWidgetItem, QAbstractItemView, QGraphicsDropShadowEffect,
    QFrame, QSizePolicy, QSpacerItem, QStackedWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QEasingCurve, QRect, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QBrush, QPainter, QLinearGradient, QPen


class AppleStyleSheet:
    MAIN_WINDOW = """
    QMainWindow {
        background-color: #f5f5f7;
    }
    QWidget {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
        font-size: 13px;
        color: #1d1d1f;
    }
    """

    SIDEBAR = """
    QListWidget {
        background-color: rgba(244, 244, 246, 0.8);
        border: none;
        border-radius: 12px;
        padding: 8px;
        outline: none;
    }
    QListWidget::item {
        height: 36px;
        border-radius: 8px;
        padding-left: 12px;
        margin: 2px 4px;
        color: #1d1d1f;
    }
    QListWidget::item:selected {
        background-color: rgba(0, 122, 255, 0.15);
        color: #007aff;
    }
    QListWidget::item:hover {
        background-color: rgba(0, 0, 0, 0.04);
    }
    """

    CARD = """
    QFrame#card {
        background-color: white;
        border-radius: 12px;
        border: 1px solid rgba(0, 0, 0, 0.06);
    }
    """

    PUSH_BUTTON = """
    QPushButton {
        background-color: #007aff;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: #0071eb;
    }
    QPushButton:pressed {
        background-color: #0051d4;
    }
    QPushButton:disabled {
        background-color: #c7c7cc;
    }
    """

    PUSH_BUTTON_SECONDARY = """
    QPushButton {
        background-color: rgba(118, 118, 128, 0.12);
        color: #1d1d1f;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: rgba(118, 118, 128, 0.2);
    }
    """

    TEXT_EDIT = """
    QTextEdit {
        background-color: white;
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 8px;
        padding: 12px;
        selection-background-color: #007aff;
    }
    """

    GROUP_BOX = """
    QGroupBox {
        font-size: 12px;
        font-weight: 600;
        color: #86868b;
        border: none;
        margin-top: 16px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
    }
    """

    TABLE_WIDGET = """
    QTableWidget {
        background-color: white;
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 8px;
        gridline-color: #f5f5f7;
        selection-background-color: rgba(0, 122, 255, 0.1);
    }
    QTableWidget::item {
        border: none;
        padding: 8px;
    }
    QHeaderView::section {
        background-color: #f5f5f7;
        border: none;
        border-bottom: 1px solid rgba(0, 0, 0, 0.06);
        padding: 8px;
        font-weight: 600;
        color: #86868b;
    }
    """

    TAB_WIDGET = """
    QTabWidget::pane {
        border: none;
        background-color: transparent;
    }
    QTabBar::tab {
        background-color: transparent;
        color: #86868b;
        padding: 8px 16px;
        border: none;
        font-size: 13px;
    }
    QTabBar::tab:selected {
        color: #007aff;
        font-weight: 600;
    }
    QTabBar::tab:hover {
        color: #1d1d1f;
    }
    """

    PROGRESS_BAR = """
    QProgressBar {
        background-color: rgba(0, 0, 0, 0.06);
        border: none;
        border-radius: 4px;
        height: 8px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #007aff;
        border-radius: 4px;
    }
    """

    LINE_EDIT = """
    QLineEdit {
        background-color: white;
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 14px;
    }
    QLineEdit:focus {
        border: 2px solid #007aff;
    }
    """

    LABEL_TITLE = """
    QLabel {
        font-size: 21px;
        font-weight: 600;
        color: #1d1d1f;
    }
    """

    LABEL_SUBTITLE = """
    QLabel {
        font-size: 13px;
        color: #86868b;
    }
    """

    STATUS_LABEL = """
    QLabel {
        font-size: 11px;
        font-weight: 500;
        color: white;
        background-color: #34c759;
        padding: 3px 8px;
        border-radius: 4px;
    }
    """


class ShadowWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setObjectName("card")

    def add_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)


class AppleCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setAttribute(Qt.WA_StyledBackground)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)


class WorkerThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setFixedSize(420, 380)
        self.setStyleSheet("""
        QDialog {
            background-color: #f5f5f7;
        }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)

        icon_label = QLabel()
        icon_label.setFixedSize(80, 80)
        icon_label.setStyleSheet("""
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #5e5ce6, stop:1 #007aff);
        border-radius: 18px;
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setText("🛠️")
        icon_label.setStyleSheet("font-size: 40px; background: transparent;")

        title = QLabel("麒麟运维百宝箱")
        title.setFont(QFont("-apple-system, BlinkMacSystemFont, Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        version = QLabel("版本 1.0.2")
        version.setFont(QFont("-apple-system, BlinkMacSystemFont, Segoe UI", 13))
        version.setStyleSheet("color: #86868b;")
        version.setAlignment(Qt.AlignCenter)

        desc = QLabel("专为银河麒麟桌面V10 SP1打造的\n系统运维管理工具")
        desc.setFont(QFont("-apple-system, BlinkMacSystemFont, Segoe UI", 13))
        desc.setStyleSheet("color: #1d1d1f;")
        desc.setAlignment(Qt.AlignCenter)

        features = QLabel("✓ 系统信息监控  ✓ 服务管理\n✓ 网络配置  ✓ 日志清理")
        features.setFont(QFont("-apple-system, BlinkMacSystemFont, Segoe UI", 12))
        features.setStyleSheet("color: #86868b;")
        features.setAlignment(Qt.AlignCenter)

        close_btn = QPushButton("好")
        close_btn.setFixedWidth(80)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(AppleStyleSheet.PUSH_BUTTON)

        layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(title)
        layout.addWidget(version)
        layout.addSpacing(10)
        layout.addWidget(desc)
        layout.addSpacing(5)
        layout.addWidget(features)
        layout.addStretch(30)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        self.setLayout(layout)


class SystemInfoPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()
        self.load_system_info()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title = QLabel("系统信息")
        title.setStyleSheet(AppleStyleSheet.LABEL_TITLE)
        header_layout.addWidget(title)
        header_layout.addStretch()

        refresh_btn = QPushButton("↻  刷新")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(AppleStyleSheet.PUSH_BUTTON_SECONDARY)
        refresh_btn.clicked.connect(self.load_system_info)
        header_layout.addWidget(refresh_btn)

        main_layout.addLayout(header_layout)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        left_card = AppleCard()
        left_card.setFixedWidth(320)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(12)

        info_title = QLabel("概览")
        info_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1d1d1f;")
        left_layout.addWidget(info_title)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignLeft)

        self.hostname_val = QLabel("加载中...")
        self.os_val = QLabel("银河麒麟桌面V10 SP1")
        self.kernel_val = QLabel("加载中...")
        self.arch_val = QLabel("加载中...")

        self.uptime_val = QLabel("未知")
        self.boot_time_val = QLabel("未知")
        self.current_time_val = QLabel("未知")

        for label in [self.hostname_val, self.os_val, self.kernel_val, self.arch_val, self.uptime_val, self.boot_time_val, self.current_time_val]:
            label.setStyleSheet("font-size: 14px; color: #1d1d1f;")

        form_layout.addRow("主机名", self.hostname_val)
        form_layout.addRow("操作系统", self.os_val)
        form_layout.addRow("内核版本", self.kernel_val)
        form_layout.addRow("系统架构", self.arch_val)
        form_layout.addRow("运行时间", self.uptime_val)
        form_layout.addRow("启动时间", self.boot_time_val)
        form_layout.addRow("当前时间", self.current_time_val)

        left_layout.addLayout(form_layout)
        left_layout.addStretch()
        left_card.setLayout(left_layout)

        right_card = AppleCard()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(16)

        stats_title = QLabel("资源使用")
        stats_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1d1d1f;")
        right_layout.addWidget(stats_title)

        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU"))
        cpu_layout.addStretch()
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setFixedHeight(8)
        self.cpu_bar.setStyleSheet(AppleStyleSheet.PROGRESS_BAR)
        self.cpu_bar.setValue(35)
        cpu_layout.addWidget(self.cpu_bar, stretch=3)
        self.cpu_val = QLabel("35%")
        self.cpu_val.setStyleSheet("font-size: 13px; color: #86868b;")
        cpu_layout.addWidget(self.cpu_val)
        right_layout.addLayout(cpu_layout)

        mem_layout = QHBoxLayout()
        mem_layout.addWidget(QLabel("内存"))
        mem_layout.addStretch()
        self.mem_bar = QProgressBar()
        self.mem_bar.setFixedHeight(8)
        self.mem_bar.setStyleSheet(AppleStyleSheet.PROGRESS_BAR)
        self.mem_bar.setValue(52)
        mem_layout.addWidget(self.mem_bar, stretch=3)
        self.mem_val = QLabel("52%")
        self.mem_val.setStyleSheet("font-size: 13px; color: #86868b;")
        mem_layout.addWidget(self.mem_val)
        right_layout.addLayout(mem_layout)

        disk_layout = QHBoxLayout()
        disk_layout.addWidget(QLabel("磁盘"))
        disk_layout.addStretch()
        self.disk_bar = QProgressBar()
        self.disk_bar.setFixedHeight(8)
        self.disk_bar.setStyleSheet(AppleStyleSheet.PROGRESS_BAR)
        self.disk_bar.setValue(48)
        disk_layout.addWidget(self.disk_bar, stretch=3)
        self.disk_val = QLabel("48%")
        self.disk_val.setStyleSheet("font-size: 13px; color: #86868b;")
        disk_layout.addWidget(self.disk_val)
        right_layout.addLayout(disk_layout)

        right_layout.addStretch()
        right_card.setLayout(right_layout)

        cards_layout.addWidget(left_card)
        cards_layout.addWidget(right_card, stretch=1)

        main_layout.addLayout(cards_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(5000)

    def load_system_info(self):
        def fetch():
            return self.client.get_system_info()

        def on_result(result):
            if result.get('status') == 'success':
                data = result.get('data', {})
                self.hostname_val.setText(data.get('hostname', '未知'))
                self.os_val.setText(data.get('os_version', '未知'))
                self.kernel_val.setText(data.get('kernel', '未知'))
                self.arch_val.setText(data.get('architecture', '未知'))
                self.uptime_val.setText(data.get('uptime', '未知'))
                self.boot_time_val.setText(data.get('boot_time', '未知'))
                self.current_time_val.setText(data.get('current_time', '未知'))

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def update_stats(self):
        def on_cpu(result):
            if result.get('status') == 'success':
                cpu_percent = result.get('data', {}).get('usage_percent', 0)
                self.cpu_bar.setValue(int(cpu_percent))
                self.cpu_val.setText(f"{cpu_percent:.1f}%")

        def on_mem(result):
            if result.get('status') == 'success':
                mem_percent = result.get('data', {}).get('percent', 0)
                self.mem_bar.setValue(int(mem_percent))
                self.mem_val.setText(f"{mem_percent:.1f}%")

        def on_disk(result):
            if result.get('status') == 'success':
                partitions = result.get('data', {}).get('partitions', [])
                if partitions:
                    disk_percent = partitions[0].get('percent', 0)
                    self.disk_bar.setValue(int(disk_percent))
                    self.disk_val.setText(f"{disk_percent:.1f}%")

        t1 = WorkerThread(self.client.get_cpu_info)
        t1.finished.connect(on_cpu)
        t1.start()

        t2 = WorkerThread(self.client.get_memory_info)
        t2.finished.connect(on_mem)
        t2.start()

        t3 = WorkerThread(self.client.get_disk_info)
        t3.finished.connect(on_disk)
        t3.start()


class SystemStatusPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()
        self.load_status()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title = QLabel("系统状态")
        title.setStyleSheet(AppleStyleSheet.LABEL_TITLE)
        header_layout.addWidget(title)
        header_layout.addStretch()

        refresh_btn = QPushButton("↻  刷新")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(AppleStyleSheet.PUSH_BUTTON_SECONDARY)
        refresh_btn.clicked.connect(self.load_status)
        header_layout.addWidget(refresh_btn)

        main_layout.addLayout(header_layout)

        tabs = QTabWidget()
        tabs.setStyleSheet(AppleStyleSheet.TAB_WIDGET)

        cpu_tab = QWidget()
        cpu_layout = QVBoxLayout()
        cpu_layout.setContentsMargins(12, 12, 12, 12)
        self.cpu_text = QTextEdit()
        self.cpu_text.setReadOnly(True)
        self.cpu_text.setStyleSheet(AppleStyleSheet.TEXT_EDIT)
        cpu_layout.addWidget(self.cpu_text)
        cpu_tab.setLayout(cpu_layout)
        tabs.addTab(cpu_tab, "CPU")

        mem_tab = QWidget()
        mem_layout = QVBoxLayout()
        mem_layout.setContentsMargins(12, 12, 12, 12)
        self.mem_text = QTextEdit()
        self.mem_text.setReadOnly(True)
        self.mem_text.setStyleSheet(AppleStyleSheet.TEXT_EDIT)
        mem_layout.addWidget(self.mem_text)
        mem_tab.setLayout(mem_layout)
        tabs.addTab(mem_tab, "内存")

        process_tab = QWidget()
        process_layout = QVBoxLayout()
        process_layout.setContentsMargins(12, 12, 12, 12)
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels(['用户', 'PID', 'CPU%', '内存%', 'RSS', '命令'])
        self.process_table.setStyleSheet(AppleStyleSheet.TABLE_WIDGET)
        self.process_table.horizontalHeader().setSectionResizeMode(5, 1)
        process_layout.addWidget(self.process_table)
        process_tab.setLayout(process_layout)
        tabs.addTab(process_tab, "进程")

        service_tab = QWidget()
        service_layout = QVBoxLayout()
        service_layout.setContentsMargins(12, 12, 12, 12)
        self.service_text = QTextEdit()
        self.service_text.setReadOnly(True)
        self.service_text.setStyleSheet(AppleStyleSheet.TEXT_EDIT)
        service_layout.addWidget(self.service_text)
        service_tab.setLayout(service_layout)
        tabs.addTab(service_tab, "服务")

        main_layout.addWidget(tabs)
        self.setLayout(main_layout)

    def load_status(self):
        def on_cpu(result):
            if result.get('status') == 'success':
                data = result.get('data', {})
                cpu_raw = data.get('cpuinfo_raw', '')
                display = f"""物理核心: {data.get('physical_cores', 'N/A')}
逻辑核心: {data.get('logical_cores', 'N/A')}
CPU使用率: {data.get('usage_percent', 0):.1f}%
当前频率: {data.get('frequency_current', 0):.2f} GHz
最大频率: {data.get('frequency_max', 0):.2f} GHz
上下文切换: {data.get('context_switches', 0):,}
中断次数: {data.get('interrupts', 0):,}

--- CPU Info ---
{cpu_raw}"""
                self.cpu_text.setPlainText(display)

        def on_mem(result):
            if result.get('status') == 'success':
                data = result.get('data', {})
                mem_raw = data.get('meminfo_raw', '')
                display = f"""总内存: {data.get('total_gb', 0):.2f} GB
已使用: {data.get('used_gb', 0):.2f} GB
可用内存: {data.get('available_gb', 0):.2f} GB
使用率: {data.get('percent', 0):.1f}%

Swap总计: {data.get('swap_total', 0) / (1024**3):.2f} GB
Swap已用: {data.get('swap_used', 0) / (1024**3):.2f} GB
Swap使用率: {data.get('swap_percent', 0):.1f}%

--- Memory Info ---
{mem_raw}"""
                self.mem_text.setPlainText(display)

        def on_proc(result):
            if result.get('status') == 'success':
                proc_data = result.get('data', {}).get('processes', [])
                if isinstance(proc_data, str):
                    lines = proc_data.strip().split('\n')
                    self.process_table.setRowCount(max(0, len(lines) - 1))
                    for i, line in enumerate(lines[1:], 0):
                        parts = line.split()
                        if len(parts) >= 11:
                            items = [parts[0], parts[1], parts[2], parts[3], parts[5], ' '.join(parts[10:])]
                            for j, item in enumerate(items[:6]):
                                self.process_table.setItem(i, j, QTableWidgetItem(item))
                elif isinstance(proc_data, list):
                    self.process_table.setRowCount(len(proc_data))
                    for i, proc in enumerate(proc_data):
                        if isinstance(proc, dict):
                            items = [
                                proc.get('username', ''),
                                str(proc.get('pid', '')),
                                f"{proc.get('cpu_percent', 0):.1f}",
                                f"{proc.get('memory_percent', 0):.1f}",
                                f"{proc.get('memory_rss_mb', 0):.0f} MB",
                                proc.get('name', '')
                            ]
                            for j, item in enumerate(items[:6]):
                                self.process_table.setItem(i, j, QTableWidgetItem(item))

        def on_svc(result):
            if result.get('status') == 'success':
                self.service_text.setPlainText(result.get('data', {}).get('systemctl_output', ''))

        self.t1 = WorkerThread(self.client.get_cpu_info)
        self.t1.finished.connect(on_cpu)
        self.t1.start()

        self.t2 = WorkerThread(self.client.get_memory_info)
        self.t2.finished.connect(on_mem)
        self.t2.start()

        self.t3 = WorkerThread(lambda: self.client.get_process_list(20))
        self.t3.finished.connect(on_proc)
        self.t3.start()

        self.t4 = WorkerThread(self.client.get_service_list)
        self.t4.finished.connect(on_svc)
        self.t4.start()


class UserManagementPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()
        self.load_users()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title = QLabel("用户管理")
        title.setStyleSheet(AppleStyleSheet.LABEL_TITLE)
        header_layout.addWidget(title)
        header_layout.addStretch()

        refresh_btn = QPushButton("↻  刷新")
        refresh_btn.setStyleSheet(AppleStyleSheet.PUSH_BUTTON_SECONDARY)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.load_users)
        header_layout.addWidget(refresh_btn)

        main_layout.addLayout(header_layout)

        content_card = AppleCard()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(16, 16, 16, 16)

        splitter = QSplitter(Qt.Horizontal)

        self.user_list = QListWidget()
        self.user_list.setStyleSheet(AppleStyleSheet.SIDEBAR)
        self.user_list.itemClicked.connect(self.on_user_selected)
        splitter.addWidget(self.user_list)

        detail_card = AppleCard()
        detail_layout = QVBoxLayout()
        detail_layout.setContentsMargins(16, 16, 16, 16)
        self.user_info = QTextEdit()
        self.user_info.setReadOnly(True)
        self.user_info.setStyleSheet(AppleStyleSheet.TEXT_EDIT)
        detail_layout.addWidget(QLabel("用户详情"))
        detail_layout.addWidget(self.user_info)
        detail_card.setLayout(detail_layout)
        splitter.addWidget(detail_card)

        content_layout.addWidget(splitter)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        history_btn = QPushButton("查看登录历史")
        history_btn.setStyleSheet(AppleStyleSheet.PUSH_BUTTON_SECONDARY)
        history_btn.setCursor(Qt.PointingHandCursor)
        history_btn.clicked.connect(self.load_history)
        btn_layout.addWidget(history_btn)

        content_layout.addLayout(btn_layout)
        content_card.setLayout(content_layout)

        main_layout.addWidget(content_card)
        self.setLayout(main_layout)

    def load_users(self):
        def on_result(result):
            if result.get('status') == 'success':
                self.user_list.clear()
                for line in result.get('data', {}).get('users', '').split('\n'):
                    if ':' in line:
                        self.user_list.addItem(line.split(':')[0])

        self.thread = WorkerThread(self.client.get_users)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def load_history(self):
        def on_result(result):
            if result.get('status') == 'success':
                self.user_info.setPlainText(result.get('data', {}).get('login_history', ''))

        self.thread = WorkerThread(self.client.get_login_history)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def on_user_selected(self, item):
        self.user_info.setPlainText(f"选中用户: {item.text()}")


class NetworkPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()
        self.load_network_info()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title = QLabel("网络设置")
        title.setStyleSheet(AppleStyleSheet.LABEL_TITLE)
        header_layout.addWidget(title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        info_card = AppleCard()
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(20, 20, 20, 20)
        self.network_text = QTextEdit()
        self.network_text.setReadOnly(True)
        self.network_text.setStyleSheet(AppleStyleSheet.TEXT_EDIT)
        info_layout.addWidget(self.network_text)
        info_card.setLayout(info_layout)
        main_layout.addWidget(info_card, stretch=1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        refresh_btn = QPushButton("↻  刷新")
        refresh_btn.setStyleSheet(AppleStyleSheet.PUSH_BUTTON_SECONDARY)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.load_network_info)
        btn_layout.addWidget(refresh_btn)

        restart_btn = QPushButton("⟳  重启网络")
        restart_btn.setStyleSheet(AppleStyleSheet.PUSH_BUTTON)
        restart_btn.setCursor(Qt.PointingHandCursor)
        restart_btn.clicked.connect(self.restart_network)
        btn_layout.addWidget(restart_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def load_network_info(self):
        def on_result(result):
            if result.get('status') == 'success':
                self.network_text.setPlainText(result.get('data', {}).get('network', ''))

        self.thread = WorkerThread(self.client.get_network_info)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def restart_network(self):
        def on_result(result):
            if result.get('status') == 'success':
                QMessageBox.information(self, "成功", result.get('message', '操作成功'))
                self.load_network_info()
            else:
                QMessageBox.warning(self, "失败", result.get('message', '操作失败'))

        self.thread = WorkerThread(self.client.restart_network)
        self.thread.finished.connect(on_result)
        self.thread.start()


class SoftwarePage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title = QLabel("软件管理")
        title.setStyleSheet(AppleStyleSheet.LABEL_TITLE)
        header_layout.addWidget(title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        tabs = QTabWidget()
        tabs.setStyleSheet(AppleStyleSheet.TAB_WIDGET)

        sources_tab = QWidget()
        sources_layout = QVBoxLayout()
        sources_layout.setContentsMargins(12, 12, 12, 12)
        self.sources_text = QTextEdit()
        self.sources_text.setReadOnly(True)
        self.sources_text.setStyleSheet(AppleStyleSheet.TEXT_EDIT)
        sources_layout.addWidget(self.sources_text)

        sources_btn_layout = QHBoxLayout()
        sources_btn_layout.addStretch()
        sources_refresh_btn = QPushButton("↻  刷新APT源")
        sources_refresh_btn.setStyleSheet(AppleStyleSheet.PUSH_BUTTON_SECONDARY)
        sources_refresh_btn.setCursor(Qt.PointingHandCursor)
        sources_refresh_btn.clicked.connect(self.load_sources)
        sources_btn_layout.addWidget(sources_refresh_btn)
        sources_layout.addLayout(sources_btn_layout)
        sources_tab.setLayout(sources_layout)
        tabs.addTab(sources_tab, "APT源")

        packages_tab = QWidget()
        packages_layout = QVBoxLayout()
        packages_layout.setContentsMargins(12, 12, 12, 12)
        self.packages_text = QTextEdit()
        self.packages_text.setReadOnly(True)
        self.packages_text.setStyleSheet(AppleStyleSheet.TEXT_EDIT)
        packages_layout.addWidget(self.packages_text)

        packages_btn_layout = QHBoxLayout()
        packages_btn_layout.addStretch()
        packages_refresh_btn = QPushButton("↻  刷新软件包")
        packages_refresh_btn.setStyleSheet(AppleStyleSheet.PUSH_BUTTON_SECONDARY)
        packages_refresh_btn.setCursor(Qt.PointingHandCursor)
        packages_refresh_btn.clicked.connect(self.load_packages)
        packages_btn_layout.addWidget(packages_refresh_btn)
        packages_layout.addLayout(packages_btn_layout)
        packages_tab.setLayout(packages_layout)
        tabs.addTab(packages_tab, "已安装")

        main_layout.addWidget(tabs)
        self.setLayout(main_layout)

    def load_sources(self):
        def on_result(result):
            if result.get('status') == 'success':
                self.sources_text.setPlainText(result.get('data', {}).get('sources', ''))

        self.thread = WorkerThread(self.client.get_apt_sources)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def load_packages(self):
        def on_result(result):
            if result.get('status') == 'success':
                self.packages_text.setPlainText(result.get('data', {}).get('packages', ''))

        self.thread = WorkerThread(self.client.get_installed_packages)
        self.thread.finished.connect(on_result)
        self.thread.start()


class SecurityPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()
        self.load_kysec_status()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title = QLabel("安全设置")
        title.setStyleSheet(AppleStyleSheet.LABEL_TITLE)
        header_layout.addWidget(title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        kysec_card = AppleCard()
        kysec_layout = QVBoxLayout()
        kysec_layout.setContentsMargins(24, 24, 24, 24)
        kysec_layout.setSpacing(20)

        kysec_header = QHBoxLayout()
        icon_label = QLabel("🔒")
        icon_label.setStyleSheet("font-size: 32px;")
        kysec_title = QLabel("Kysec 安全中心")
        kysec_title.setStyleSheet("font-size: 18px; font-weight: 600;")
        kysec_header.addWidget(icon_label)
        kysec_header.addWidget(kysec_title)
        kysec_header.addStretch()
        kysec_layout.addLayout(kysec_header)

        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("当前状态:"))
        self.kysec_status = QLabel("加载中...")
        self.kysec_status.setStyleSheet("font-weight: 600; color: #007aff;")
        status_layout.addWidget(self.kysec_status)
        status_layout.addStretch()
        kysec_layout.addLayout(status_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        refresh_btn = QPushButton("↻  刷新")
        refresh_btn.setStyleSheet(AppleStyleSheet.PUSH_BUTTON_SECONDARY)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.load_kysec_status)
        btn_layout.addWidget(refresh_btn)

        enable_btn = QPushButton("✓  启用")
        enable_btn.setStyleSheet(AppleStyleSheet.PUSH_BUTTON)
        enable_btn.setCursor(Qt.PointingHandCursor)
        enable_btn.clicked.connect(lambda: self.set_kysec('enable'))
        btn_layout.addWidget(enable_btn)

        disable_btn = QPushButton("✕  禁用")
        disable_btn.setStyleSheet("""
        QPushButton {
            background-color: #ff3b30;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton:hover { background-color: #d63030; }
        """)
        disable_btn.setCursor(Qt.PointingHandCursor)
        disable_btn.clicked.connect(lambda: self.set_kysec('disable'))
        btn_layout.addWidget(disable_btn)

        kysec_layout.addLayout(btn_layout)
        kysec_card.setLayout(kysec_layout)

        main_layout.addWidget(kysec_card)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def load_kysec_status(self):
        def on_result(result):
            if result.get('status') == 'success':
                status = result.get('data', {}).get('kysec', '').strip()
                self.kysec_status.setText(status[:200] if status else '未知')

        self.thread = WorkerThread(self.client.get_kysec_status)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def set_kysec(self, action):
        def on_result(result):
            if result.get('status') == 'success':
                QMessageBox.information(self, "成功", f"Kysec已{action}")
                self.load_kysec_status()
            else:
                QMessageBox.warning(self, "失败", result.get('message', '操作失败'))

        self.thread = WorkerThread(self.client.set_kysec, action)
        self.thread.finished.connect(on_result)
        self.thread.start()


class LogPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()
        self.load_logs()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title = QLabel("日志管理")
        title.setStyleSheet(AppleStyleSheet.LABEL_TITLE)
        header_layout.addWidget(title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        log_card = AppleCard()
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(16, 16, 16, 16)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(AppleStyleSheet.TEXT_EDIT)
        log_layout.addWidget(self.log_text)
        log_card.setLayout(log_layout)
        main_layout.addWidget(log_card, stretch=1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        refresh_btn = QPushButton("↻  刷新")
        refresh_btn.setStyleSheet(AppleStyleSheet.PUSH_BUTTON_SECONDARY)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.load_logs)
        btn_layout.addWidget(refresh_btn)

        cleanup_btn = QPushButton("🗑  清理日志")
        cleanup_btn.setStyleSheet("""
        QPushButton {
            background-color: #ff9500;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton:hover { background-color: #d98000; }
        """)
        cleanup_btn.setCursor(Qt.PointingHandCursor)
        cleanup_btn.clicked.connect(self.cleanup_logs)
        btn_layout.addWidget(cleanup_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def load_logs(self):
        def on_result(result):
            if result.get('status') == 'success':
                self.log_text.setPlainText(result.get('data', {}).get('logs', ''))

        self.thread = WorkerThread(lambda: self.client.get_system_logs(200))
        self.thread.finished.connect(on_result)
        self.thread.start()

    def cleanup_logs(self):
        def on_result(result):
            if result.get('status') == 'success':
                QMessageBox.information(self, "成功", "日志清理完成")
                self.load_logs()
            else:
                QMessageBox.warning(self, "失败", result.get('message', '清理失败'))

        self.thread = WorkerThread(self.client.cleanup_logs)
        self.thread.finished.connect(on_result)
        self.thread.start()


class TerminalPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title = QLabel("命令终端")
        title.setStyleSheet(AppleStyleSheet.LABEL_TITLE)
        header_layout.addWidget(title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        terminal_card = AppleCard()
        terminal_layout = QVBoxLayout()
        terminal_layout.setContentsMargins(16, 16, 16, 16)
        terminal_layout.setSpacing(12)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("输入命令并按回车执行...")
        self.command_input.setStyleSheet(AppleStyleSheet.LINE_EDIT)
        self.command_input.returnPressed.connect(self.execute_command)
        terminal_layout.addWidget(self.command_input)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet(AppleStyleSheet.TEXT_EDIT)
        self.output_text.setMinimumHeight(300)
        terminal_layout.addWidget(self.output_text, stretch=1)

        terminal_card.setLayout(terminal_layout)
        main_layout.addWidget(terminal_card, stretch=1)

        execute_btn = QPushButton("▶  执行命令")
        execute_btn.setStyleSheet(AppleStyleSheet.PUSH_BUTTON)
        execute_btn.setCursor(Qt.PointingHandCursor)
        execute_btn.clicked.connect(self.execute_command)
        main_layout.addWidget(execute_btn)

        self.setLayout(main_layout)

    def execute_command(self):
        cmd = self.command_input.text().strip()
        if not cmd:
            return

        self.output_text.append(f"<span style='color: #007aff;'>$ {cmd}</span>")

        def on_result(result):
            if result.get('status') == 'success':
                output = result.get('data', {}).get('output', '')
                self.output_text.append(output if output else "(无输出)")
            else:
                self.output_text.append(f"<span style='color: #ff3b30;'>错误: {result.get('message', '未知错误')}</span>")
            self.output_text.append("")

        self.thread = WorkerThread(self.client.execute_command, cmd)
        self.thread.finished.connect(on_result)
        self.thread.start()

        self.command_input.clear()


class MainWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.setWindowTitle("麒麟运维百宝箱")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(AppleStyleSheet.MAIN_WINDOW)
        self.init_ui()

    def init_ui(self):
        self.statusBar().setStyleSheet("background-color: #f5f5f7; border: none;")
        self.statusBar().showMessage("就绪")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
        background-color: rgba(244, 244, 246, 0.6);
        border-radius: 12px;
        """)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(8, 16, 8, 16)
        sidebar_layout.setSpacing(4)

        logo_label = QLabel("🛠 运维工具")
        logo_label.setStyleSheet("""
        font-size: 16px;
        font-weight: 700;
        color: #1d1d1f;
        padding: 8px 12px;
        """)
        sidebar_layout.addWidget(logo_label)
        sidebar_layout.addSpacing(10)

        nav_items = [
            ("系统信息", "system_info"),
            ("系统状态", "system_status"),
            ("用户管理", "user"),
            ("网络设置", "network"),
            ("软件管理", "software"),
            ("安全设置", "security"),
            ("日志管理", "logs"),
            ("命令终端", "terminal"),
        ]

        self.nav_buttons = {}
        for name, key in nav_items:
            btn = QPushButton(f"  {name}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
                color: #1d1d1f;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.04);
            }
            QPushButton:checked {
                background-color: rgba(0, 122, 255, 0.12);
                color: #007aff;
                font-weight: 600;
            }
            """)
            btn.setCheckable(True)
            self.nav_buttons[key] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        about_btn = QPushButton("  关于")
        about_btn.setCursor(Qt.PointingHandCursor)
        about_btn.setStyleSheet("""
        QPushButton {
            text-align: left;
            background-color: transparent;
            border: none;
            border-radius: 8px;
            padding: 10px 12px;
            font-size: 14px;
            color: #86868b;
        }
        QPushButton:hover { color: #1d1d1f; }
        """)
        about_btn.clicked.connect(self.show_about)
        sidebar_layout.addWidget(about_btn)

        sidebar.setLayout(sidebar_layout)

        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: transparent;")

        self.system_info_page = SystemInfoPage(self.client)
        self.content_stack.addWidget(self.system_info_page)

        self.system_status_page = SystemStatusPage(self.client)
        self.content_stack.addWidget(self.system_status_page)

        self.user_page = UserManagementPage(self.client)
        self.content_stack.addWidget(self.user_page)

        self.network_page = NetworkPage(self.client)
        self.content_stack.addWidget(self.network_page)

        self.software_page = SoftwarePage(self.client)
        self.content_stack.addWidget(self.software_page)

        self.security_page = SecurityPage(self.client)
        self.content_stack.addWidget(self.security_page)

        self.log_page = LogPage(self.client)
        self.content_stack.addWidget(self.log_page)

        self.terminal_page = TerminalPage(self.client)
        self.content_stack.addWidget(self.terminal_page)

        for key, btn in self.nav_buttons.items():
            idx = list(self.nav_buttons.keys()).index(key)
            btn.clicked.connect(lambda checked, i=idx: self.switch_page(i))

        self.nav_buttons["system_info"].setChecked(True)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content_stack)
        central_widget.setLayout(main_layout)

    def switch_page(self, index):
        self.content_stack.setCurrentIndex(index)

    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec_()


def main():
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    app.setStyle("fusion")

    host = 'localhost'
    port = 29876

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    from client.client import KylinClient
    client = KylinClient(host, port)

    if not client.connect():
        QMessageBox.critical(None, "连接失败", f"无法连接到服务器 {host}:{port}\n请确保服务端已启动。")
        return 1

    window = MainWindow(client)
    window.show()

    ret = app.exec_()
    client.disconnect()
    return ret


if __name__ == '__main__':
    sys.exit(main())
