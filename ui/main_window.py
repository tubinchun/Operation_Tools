#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTextEdit,
    QTableWidget, QTableWidgetItem, QGroupBox,
    QFormLayout, QMessageBox, QAction, QMenuBar,
    QMenu, QStatusBar, QToolBar, QComboBox,
    QLineEdit, QSpinBox, QCheckBox, QSplitter,
    QScrollArea, QProgressBar, QDialog, QListWidget,
    QListWidgetItem, QAbstractItemView, QTableView, QHeaderView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

from core.local_client import LocalClient


class WorkerThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._is_running = True

    def stop(self):
        self._is_running = False
        self.wait()

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
        self.setFixedSize(400, 300)
        layout = QVBoxLayout()

        title = QLabel("银河麒麟运维管理工具")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        version = QLabel("版本: 1.0.0")
        version.setAlignment(Qt.AlignCenter)

        desc = QLabel("适配: 银河麒麟桌面V10 SP1\n\n"
                     "功能: 系统信息监控、服务管理、\n"
                     "     网络配置、用户管理、日志清理等")
        desc.setAlignment(Qt.AlignCenter)

        contact = QLabel("技术支持: 400-xxx-xxxx")
        contact.setAlignment(Qt.AlignCenter)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)

        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(desc)
        layout.addWidget(contact)
        layout.addStretch()
        layout.addWidget(close_btn)
        self.setLayout(layout)


class SystemInfoPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self._threads = []
        self.init_ui()
        self.load_system_info()
        # 启动定时器，每3秒刷新一次实时统计
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(3000)

    def cleanup(self):
        """清理资源，停止线程和定时器"""
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()
        # 停止所有线程
        for thread in self._threads:
            if thread.isRunning():
                thread.stop()

    def init_ui(self):
        main_layout = QVBoxLayout()

        header = QLabel("系统信息概览")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        splitter = QSplitter(Qt.Horizontal)

        info_card = QGroupBox("基本信息")
        info_layout = QFormLayout()

        self.hostname_val = QLabel("加载中...")
        self.os_val = QLabel("银河麒麟桌面V10 SP1")
        self.kernel_val = QLabel("加载中...")
        self.arch_val = QLabel("加载中...")
        self.cpu_val = QLabel("加载中...")
        self.memory_val = QLabel("加载中...")

        info_layout.addRow("主机名:", self.hostname_val)
        info_layout.addRow("操作系统:", self.os_val)
        info_layout.addRow("内核版本:", self.kernel_val)
        info_layout.addRow("系统架构:", self.arch_val)
        info_layout.addRow("CPU信息:", self.cpu_val)
        info_layout.addRow("内存状态:", self.memory_val)
        info_card.setLayout(info_layout)

        stats_card = QGroupBox("实时统计")
        stats_layout = QVBoxLayout()

        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximum(100)
        self.cpu_bar.setValue(0)
        stats_layout.addWidget(QLabel("CPU使用率"))
        stats_layout.addWidget(self.cpu_bar)

        self.mem_bar = QProgressBar()
        self.mem_bar.setMaximum(100)
        self.mem_bar.setValue(0)
        stats_layout.addWidget(QLabel("内存使用率"))
        stats_layout.addWidget(self.mem_bar)

        self.disk_bar = QProgressBar()
        self.disk_bar.setMaximum(100)
        self.disk_bar.setValue(0)
        stats_layout.addWidget(QLabel("磁盘使用率"))
        stats_layout.addWidget(self.disk_bar)

        stats_card.setLayout(stats_layout)

        splitter.addWidget(info_card)
        splitter.addWidget(stats_card)

        main_layout.addWidget(splitter)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新信息")
        refresh_btn.clicked.connect(self.load_system_info)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def load_system_info(self):
        def fetch():
            sys_info = self.client.get_system_info()
            cpu_info = self.client.get_cpu_info()
            mem_info = self.client.get_memory_info()
            disk_info = self.client.get_disk_info()
            return {'sys': sys_info, 'cpu': cpu_info, 'mem': mem_info, 'disk': disk_info}

        def on_result(result):
            sys_result = result.get('sys', {})
            if sys_result.get('status') == 'success':
                data = sys_result.get('data', {})
                self.hostname_val.setText(data.get('hostname', '未知'))
                self.kernel_val.setText(data.get('kernel', '未知'))
                self.arch_val.setText(data.get('architecture', '未知'))

            cpu_result = result.get('cpu', {})
            if cpu_result.get('status') == 'success':
                cpu_data = cpu_result.get('data', {}).get('cpuinfo', '')
                self.cpu_val.setText(cpu_data.split('\n')[0][:50] if cpu_data else '未知')

            mem_result = result.get('mem', {})
            if mem_result.get('status') == 'success':
                mem_data = mem_result.get('data', {})
                self.memory_val.setText(f"{mem_data.get('percent', 0)}% 已使用")
                self.mem_bar.setValue(mem_data.get('percent', 0))

            disk_result = result.get('disk', {})
            if disk_result.get('status') == 'success':
                partitions = disk_result.get('data', {}).get('partitions', [])
                if partitions:
                    root_partition = next((p for p in partitions if p.get('mountpoint') == '/'), partitions[0])
                    self.disk_bar.setValue(root_partition.get('percent', 0))

        thread = WorkerThread(fetch)
        thread.finished.connect(on_result)
        thread.start()
        self._threads.append(thread)

    def update_stats(self):
        """定期更新实时统计数据"""
        def fetch():
            cpu_info = self.client.get_cpu_info()
            mem_info = self.client.get_memory_info()
            disk_info = self.client.get_disk_info()
            return {'cpu': cpu_info, 'mem': mem_info, 'disk': disk_info}

        def on_result(result):
            # 更新CPU使用率
            cpu_result = result.get('cpu', {})
            if cpu_result.get('status') == 'success':
                cpu_data = cpu_result.get('data', {})
                cpu_percent = cpu_data.get('usage_percent', 0)
                self.cpu_bar.setValue(int(cpu_percent))

            # 更新内存使用率
            mem_result = result.get('mem', {})
            if mem_result.get('status') == 'success':
                mem_data = mem_result.get('data', {})
                mem_percent = mem_data.get('percent', 0)
                self.mem_bar.setValue(int(mem_percent))
                self.memory_val.setText(f"{mem_percent}% 已使用")

            # 更新磁盘使用率
            disk_result = result.get('disk', {})
            if disk_result.get('status') == 'success':
                disk_data = disk_result.get('data', {})
                partitions = disk_data.get('partitions', [])
                if partitions:
                    # 使用根分区或第一个分区
                    root_partition = next((p for p in partitions if p.get('mountpoint') == '/'), partitions[0])
                    self.disk_bar.setValue(root_partition.get('percent', 0))

        stats_thread = WorkerThread(fetch)
        stats_thread.finished.connect(on_result)
        stats_thread.start()
        self._threads.append(stats_thread)


class MiniChart(QWidget):
    """迷你图表组件，用于显示资源使用趋势"""
    def __init__(self, parent=None, max_points=30):
        super().__init__(parent)
        self.max_points = max_points
        self.data_points = [0] * max_points
        self.setMinimumHeight(40)
        self.setMaximumHeight(60)

    def add_value(self, value):
        self.data_points.pop(0)
        self.data_points.append(value)
        self.update()

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QPen, QColor
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # 绘制背景
        painter.fillRect(self.rect(), QColor(240, 240, 240))

        # 绘制网格线
        pen = QPen(QColor(200, 200, 200))
        pen.setWidth(1)
        painter.setPen(pen)
        for i in range(1, 5):
            y = height * i / 5
            painter.drawLine(0, int(y), width, int(y))

        # 绘制数据线
        if max(self.data_points) > 0:
            pen = QPen(QColor(0, 150, 255))
            pen.setWidth(2)
            painter.setPen(pen)

            step = width / (self.max_points - 1)
            max_val = max(max(self.data_points), 100)

            points = []
            for i, val in enumerate(self.data_points):
                x = i * step
                y = height - (val / max_val) * height
                points.append((int(x), int(y)))

            for i in range(len(points) - 1):
                painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])

        painter.end()


class ResourceItem(QWidget):
    """资源概览项组件"""
    def __init__(self, title, icon_text=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题行
        title_layout = QHBoxLayout()
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.value_label = QLabel("0%")
        self.value_label.setFont(QFont("Arial", 10))
        self.value_label.setAlignment(Qt.AlignRight)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.value_label)
        layout.addLayout(title_layout)

        # 迷你图表
        self.chart = MiniChart(self)
        layout.addWidget(self.chart)

        self.setLayout(layout)

    def update_value(self, value, text=None):
        if text:
            self.value_label.setText(text)
        else:
            self.value_label.setText(f"{value}%")
        self.chart.add_value(value)


class SystemStatusPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self._threads = []
        self.init_ui()
        self.load_status()
        # 启动定时器，每2秒刷新一次
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(2000)
        # 网络IO历史数据
        self.last_net_io = None

    def cleanup(self):
        """清理资源，停止线程和定时器"""
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()
        # 停止所有线程
        for thread in self._threads:
            if thread.isRunning():
                thread.stop()

    def init_ui(self):
        main_layout = QHBoxLayout()

        # 左侧资源概览面板
        left_panel = QWidget()
        left_panel.setMaximumWidth(280)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

        # 处理器
        self.cpu_item = ResourceItem("处理器")
        left_layout.addWidget(self.cpu_item)

        # 内存
        self.mem_item = ResourceItem("内存")
        left_layout.addWidget(self.mem_item)

        # 交换空间
        self.swap_item = ResourceItem("交换空间")
        left_layout.addWidget(self.swap_item)

        # 网络历史
        net_group = QGroupBox("网络历史")
        net_layout = QVBoxLayout()
        net_layout.setSpacing(5)

        # 接收
        recv_layout = QHBoxLayout()
        recv_layout.addWidget(QLabel("●"))
        recv_layout.addWidget(QLabel("接收"))
        recv_layout.addStretch()
        self.recv_label = QLabel("0 KB/s")
        recv_layout.addWidget(self.recv_label)
        net_layout.addLayout(recv_layout)

        # 发送
        send_layout = QHBoxLayout()
        send_layout.addWidget(QLabel("●"))
        self.send_icon = QLabel()
        self.send_icon.setStyleSheet("color: #ff6b6b;")
        send_layout.addWidget(QLabel("发送"))
        send_layout.addStretch()
        self.send_label = QLabel("0 KB/s")
        send_layout.addWidget(self.send_label)
        net_layout.addLayout(send_layout)

        # 网络图表
        self.net_chart = MiniChart(self)
        net_layout.addWidget(self.net_chart)

        net_group.setLayout(net_layout)
        left_layout.addWidget(net_group)

        left_layout.addStretch()
        left_panel.setLayout(left_layout)

        # 右侧进程列表
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        # 标签页
        self.process_tabs = QTabWidget()

        # 应用程序标签
        self.apps_tab = QWidget()
        apps_layout = QVBoxLayout()
        self.apps_table = self.create_process_table()
        apps_layout.addWidget(self.apps_table)
        self.apps_tab.setLayout(apps_layout)
        self.process_tabs.addTab(self.apps_tab, "应用程序(0)")

        # 我的进程标签
        self.my_proc_tab = QWidget()
        my_proc_layout = QVBoxLayout()
        self.my_proc_table = self.create_process_table()
        my_proc_layout.addWidget(self.my_proc_table)
        self.my_proc_tab.setLayout(my_proc_layout)
        self.process_tabs.addTab(self.my_proc_tab, "我的进程(0)")

        # 全部进程标签
        self.all_proc_tab = QWidget()
        all_proc_layout = QVBoxLayout()
        self.all_proc_table = self.create_process_table()
        all_proc_layout.addWidget(self.all_proc_table)
        self.all_proc_tab.setLayout(all_proc_layout)
        self.process_tabs.addTab(self.all_proc_tab, "全部进程(0)")

        right_layout.addWidget(self.process_tabs)

        # 刷新按钮
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_status)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        right_layout.addLayout(btn_layout)

        right_panel.setLayout(right_layout)

        # 添加到主布局
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 3)

        self.setLayout(main_layout)

    def create_process_table(self):
        """创建进程表格"""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            '进程名称', '用户名', '磁盘读写', '处理器', '进程号', '网络', '内存', '优先级'
        ])
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        return table

    def refresh_data(self):
        """定时刷新数据"""
        self.load_status()

    def load_status(self):
        def fetch_all():
            cpu_info = self.client.get_cpu_info()
            mem_info = self.client.get_memory_info()
            proc_info = self.client.get_process_list(50)
            net_info = self.client.get_network_info()
            return {
                'cpu': cpu_info,
                'mem': mem_info,
                'proc': proc_info,
                'net': net_info
            }

        def on_result(result):
            # 更新CPU
            cpu_result = result.get('cpu', {})
            if cpu_result.get('status') == 'success':
                cpu_data = cpu_result.get('data', {})
                cpu_percent = cpu_data.get('usage_percent', 0)
                self.cpu_item.update_value(int(cpu_percent))

            # 更新内存
            mem_result = result.get('mem', {})
            if mem_result.get('status') == 'success':
                mem_data = mem_result.get('data', {})
                mem_percent = mem_data.get('percent', 0)
                total_gb = mem_data.get('total_gb', 0)
                used_gb = mem_data.get('used_gb', 0)
                self.mem_item.update_value(
                    int(mem_percent),
                    f"{used_gb:.1f}GB/{total_gb:.1f}GB"
                )

                # 更新交换空间
                swap_total = mem_data.get('swap_total', 0)
                swap_used = mem_data.get('swap_used', 0)
                if swap_total > 0:
                    swap_percent = (swap_used / swap_total) * 100
                    swap_total_gb = swap_total / (1024**3)
                    swap_used_gb = swap_used / (1024**3)
                    self.swap_item.update_value(
                        int(swap_percent),
                        f"{swap_used_gb:.1f}GB/{swap_total_gb:.1f}GB"
                    )
                else:
                    self.swap_item.update_value(0, "0GB/0GB")

            # 更新网络
            net_result = result.get('net', {})
            if net_result.get('status') == 'success':
                net_data = net_result.get('data', {})
                bytes_recv = net_data.get('bytes_recv', 0)
                bytes_sent = net_data.get('bytes_sent', 0)

                if self.last_net_io:
                    recv_speed = (bytes_recv - self.last_net_io['recv']) / 2  # 2秒间隔
                    send_speed = (bytes_sent - self.last_net_io['sent']) / 2
                    self.recv_label.setText(f"{self.format_speed(recv_speed)}")
                    self.send_label.setText(f"{self.format_speed(send_speed)}")
                    # 更新网络图表（总速度）
                    total_speed = (recv_speed + send_speed) / 1024  # KB/s
                    self.net_chart.add_value(min(int(total_speed), 100))

                self.last_net_io = {'recv': bytes_recv, 'sent': bytes_sent}

            # 更新进程列表
            proc_result = result.get('proc', {})
            if proc_result.get('status') == 'success':
                processes = proc_result.get('data', {}).get('processes', [])
                self.update_process_tables(processes)

        thread = WorkerThread(fetch_all)
        thread.finished.connect(on_result)
        thread.start()
        self._threads.append(thread)

    def format_speed(self, bytes_per_sec):
        """格式化网络速度"""
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.1f} B/s"
        elif bytes_per_sec < 1024 * 1024:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"

    def update_process_tables(self, processes):
        """更新进程表格"""
        # 分类进程
        apps = [p for p in processes if p.get('name', '').endswith(('.desktop', 'app', 'App'))]
        my_procs = processes[:20]  # 简化为前20个
        all_procs = processes[:50]  # 全部进程取前50

        # 更新标签页标题
        self.process_tabs.setTabText(0, f"应用程序({len(apps)})")
        self.process_tabs.setTabText(1, f"我的进程({len(my_procs)})")
        self.process_tabs.setTabText(2, f"全部进程({len(all_procs)})")

        # 填充表格
        self.fill_table(self.all_proc_table, all_procs)
        self.fill_table(self.my_proc_table, my_procs)
        self.fill_table(self.apps_table, apps)

    def fill_table(self, table, processes):
        """填充进程表格"""
        table.setRowCount(len(processes))
        for i, proc in enumerate(processes):
            # 进程名称
            name = proc.get('name', 'Unknown')
            table.setItem(i, 0, QTableWidgetItem(name))

            # 用户名
            username = proc.get('username', 'unknown')
            table.setItem(i, 1, QTableWidgetItem(str(username)))

            # 磁盘读写（模拟数据）
            table.setItem(i, 2, QTableWidgetItem("0 KB/s"))

            # 处理器使用率
            cpu = proc.get('cpu_percent', 0)
            table.setItem(i, 3, QTableWidgetItem(f"{cpu:.1f}%"))

            # 进程号
            pid = proc.get('pid', 0)
            table.setItem(i, 4, QTableWidgetItem(str(pid)))

            # 网络（模拟数据）
            table.setItem(i, 5, QTableWidgetItem("0 KB/s"))

            # 内存
            mem_mb = proc.get('memory_rss_mb', 0)
            table.setItem(i, 6, QTableWidgetItem(f"{mem_mb:.1f}MB"))

            # 优先级
            table.setItem(i, 7, QTableWidgetItem("普通"))


class UserManagementPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()
        self.load_users()

    def init_ui(self):
        main_layout = QVBoxLayout()

        header = QLabel("用户管理")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        splitter = QSplitter(Qt.Horizontal)

        self.user_list = QListWidget()
        self.user_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.user_list.itemClicked.connect(self.on_user_selected)
        splitter.addWidget(self.user_list)

        user_detail = QGroupBox("用户详情")
        detail_layout = QFormLayout()

        self.user_info_text = QTextEdit()
        self.user_info_text.setReadOnly(True)
        detail_layout.addRow(self.user_info_text)
        user_detail.setLayout(detail_layout)
        splitter.addWidget(user_detail)

        main_layout.addWidget(splitter)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新用户")
        refresh_btn.clicked.connect(self.load_users)
        history_btn = QPushButton("登录历史")
        history_btn.clicked.connect(self.load_history)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(history_btn)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def load_users(self):
        def fetch():
            return self.client.get_users()

        def on_result(result):
            if result.get('status') == 'success':
                users = result.get('data', {}).get('users_raw', '')
                self.user_list.clear()
                for line in users.split('\n'):
                    if ':' in line:
                        username = line.split(':')[0]
                        self.user_list.addItem(username)

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def load_history(self):
        def fetch():
            return self.client.get_login_history()

        def on_result(result):
            if result.get('status') == 'success':
                history = result.get('data', {}).get('login_history', '')
                self.user_info_text.setPlainText(history)

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def on_user_selected(self, item):
        self.user_info_text.setPlainText(f"选中用户: {item.text()}")


class NetworkPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()
        self.load_network_info()

    def init_ui(self):
        main_layout = QVBoxLayout()

        header = QLabel("网络设置")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        info_group = QGroupBox("网络信息")
        info_layout = QVBoxLayout()
        self.network_text = QTextEdit()
        self.network_text.setReadOnly(True)
        info_layout.addWidget(self.network_text)
        info_group.setLayout(info_layout)

        control_group = QGroupBox("网络控制")
        control_layout = QHBoxLayout()

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_network_info)

        restart_btn = QPushButton("重启网络服务")
        restart_btn.clicked.connect(self.restart_network)

        control_layout.addWidget(refresh_btn)
        control_layout.addWidget(restart_btn)
        control_layout.addStretch()
        control_group.setLayout(control_layout)

        main_layout.addWidget(info_group)
        main_layout.addWidget(control_group)

        self.setLayout(main_layout)

    def load_network_info(self):
        def fetch():
            return self.client.get_network_info()

        def on_result(result):
            if result.get('status') == 'success':
                self.network_text.setPlainText(result.get('data', {}).get('network', ''))

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def restart_network(self):
        def do_restart():
            return self.client.restart_network()

        def on_result(result):
            if result.get('status') == 'success':
                QMessageBox.information(self, "成功", "网络服务已重启")
                self.load_network_info()
            else:
                QMessageBox.warning(self, "失败", result.get('message', '操作失败'))

        self.thread = WorkerThread(do_restart)
        self.thread.finished.connect(on_result)
        self.thread.start()


class SoftwarePage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        header = QLabel("软件管理")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        self.tabs = QTabWidget()

        sources_tab = QWidget()
        sources_layout = QVBoxLayout()
        self.sources_text = QTextEdit()
        self.sources_text.setReadOnly(True)
        sources_layout.addWidget(self.sources_text)
        sources_btn_layout = QHBoxLayout()
        sources_refresh_btn = QPushButton("刷新APT源")
        sources_refresh_btn.clicked.connect(self.load_sources)
        sources_btn_layout.addWidget(sources_refresh_btn)
        sources_btn_layout.addStretch()
        sources_layout.addLayout(sources_btn_layout)
        sources_tab.setLayout(sources_layout)
        self.tabs.addTab(sources_tab, "APT源")

        packages_tab = QWidget()
        packages_layout = QVBoxLayout()
        self.packages_text = QTextEdit()
        self.packages_text.setReadOnly(True)
        packages_layout.addWidget(self.packages_text)
        packages_btn_layout = QHBoxLayout()
        packages_refresh_btn = QPushButton("刷新软件包")
        packages_refresh_btn.clicked.connect(self.load_packages)
        export_btn = QPushButton("导出清单")
        export_btn.clicked.connect(self.export_packages)
        packages_btn_layout.addWidget(packages_refresh_btn)
        packages_btn_layout.addWidget(export_btn)
        packages_btn_layout.addStretch()
        packages_layout.addLayout(packages_btn_layout)
        packages_tab.setLayout(packages_layout)
        self.tabs.addTab(packages_tab, "已安装软件")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def load_sources(self):
        def fetch():
            return self.client.get_apt_sources()

        def on_result(result):
            if result.get('status') == 'success':
                self.sources_text.setPlainText(result.get('data', {}).get('sources', ''))

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def load_packages(self):
        def fetch():
            return self.client.get_installed_packages()

        def on_result(result):
            if result.get('status') == 'success':
                self.packages_text.setPlainText(result.get('data', {}).get('packages', ''))

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def export_packages(self):
        content = self.packages_text.toPlainText()
        if content:
            QMessageBox.information(self, "导出", f"软件包清单包含 {len(content)} 字符")


class SecurityPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()
        self.load_kysec_status()

    def init_ui(self):
        main_layout = QVBoxLayout()

        header = QLabel("安全设置")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        kysec_group = QGroupBox("Kysec安全中心")
        kysec_layout = QVBoxLayout()

        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("状态:"))
        self.kysec_status = QLabel("加载中...")
        status_layout.addWidget(self.kysec_status)
        status_layout.addStretch()

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新状态")
        refresh_btn.clicked.connect(self.load_kysec_status)
        enable_btn = QPushButton("启用")
        enable_btn.clicked.connect(lambda: self.set_kysec('enable'))
        disable_btn = QPushButton("禁用")
        disable_btn.clicked.connect(lambda: self.set_kysec('disable'))

        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(enable_btn)
        btn_layout.addWidget(disable_btn)
        btn_layout.addStretch()

        kysec_layout.addLayout(status_layout)
        kysec_layout.addLayout(btn_layout)
        kysec_group.setLayout(kysec_layout)

        main_layout.addWidget(kysec_group)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def load_kysec_status(self):
        def fetch():
            return self.client.get_kysec_status()

        def on_result(result):
            if result.get('status') == 'success':
                status = result.get('data', {}).get('kysec', '').strip()
                self.kysec_status.setText(status[:200] if status else '未知')

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def set_kysec(self, action):
        def do_set():
            return self.client.set_kysec(action)

        def on_result(result):
            if result.get('status') == 'success':
                QMessageBox.information(self, "成功", f"Kysec已{action}")
                self.load_kysec_status()
            else:
                QMessageBox.warning(self, "失败", result.get('message', '操作失败'))

        self.thread = WorkerThread(do_set)
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

        header = QLabel("日志管理")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新日志")
        refresh_btn.clicked.connect(self.load_logs)
        cleanup_btn = QPushButton("清理日志")
        cleanup_btn.clicked.connect(self.cleanup_logs)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(cleanup_btn)
        btn_layout.addStretch()

        main_layout.addWidget(self.log_text)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def load_logs(self):
        def fetch():
            return self.client.get_system_logs(200)

        def on_result(result):
            if result.get('status') == 'success':
                self.log_text.setPlainText(result.get('data', {}).get('logs', ''))

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def cleanup_logs(self):
        def do_cleanup():
            return self.client.cleanup_logs()

        def on_result(result):
            if result.get('status') == 'success':
                QMessageBox.information(self, "成功", "日志清理完成")
                self.load_logs()
            else:
                QMessageBox.warning(self, "失败", result.get('message', '清理失败'))

        self.thread = WorkerThread(do_cleanup)
        self.thread.finished.connect(on_result)
        self.thread.start()


class TerminalPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        header = QLabel("命令终端")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("输入命令并按回车执行...")
        self.command_input.returnPressed.connect(self.execute_command)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        execute_btn = QPushButton("执行")
        execute_btn.clicked.connect(self.execute_command)

        main_layout.addWidget(self.command_input)
        main_layout.addWidget(self.output_text)
        main_layout.addWidget(execute_btn)

        self.setLayout(main_layout)

    def execute_command(self):
        cmd = self.command_input.text().strip()
        if not cmd:
            return

        self.output_text.append(f"<b>$ {cmd}</b>")

        def do_execute():
            return self.client.execute_command(cmd)

        def on_result(result):
            if result.get('status') == 'success':
                output = result.get('data', {}).get('output', '')
                self.output_text.append(output if output else "(无输出)")
            else:
                self.output_text.append(f"<font color='red'>错误: {result.get('message', '未知错误')}</font>")
            self.output_text.append("")

        self.thread = WorkerThread(do_execute)
        self.thread.finished.connect(on_result)
        self.thread.start()

        self.command_input.clear()


class MainWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.setWindowTitle("银河麒麟运维管理工具 v1.0.0")
        self.setGeometry(100, 100, 1200, 800)
        self.init_ui()

    def closeEvent(self, event):
        """重写关闭事件，确保所有线程和定时器正确清理"""
        # 清理各个页面的资源
        if hasattr(self, 'system_info_page') and hasattr(self.system_info_page, 'cleanup'):
            self.system_info_page.cleanup()
        if hasattr(self, 'system_status_page') and hasattr(self.system_status_page, 'cleanup'):
            self.system_status_page.cleanup()
        event.accept()

    def init_ui(self):
        self.statusBar().showMessage("就绪")

        self.create_menu_bar()
        self.create_tool_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        self.tabs = QTabWidget()

        self.system_info_page = SystemInfoPage(self.client)
        self.tabs.addTab(self.system_info_page, "系统信息")

        self.system_status_page = SystemStatusPage(self.client)
        self.tabs.addTab(self.system_status_page, "系统状态")

        self.user_page = UserManagementPage(self.client)
        self.tabs.addTab(self.user_page, "用户管理")

        self.network_page = NetworkPage(self.client)
        self.tabs.addTab(self.network_page, "网络设置")

        self.software_page = SoftwarePage(self.client)
        self.tabs.addTab(self.software_page, "软件管理")

        self.log_page = LogPage(self.client)
        self.tabs.addTab(self.log_page, "日志管理")

        self.security_page = SecurityPage(self.client)
        self.tabs.addTab(self.security_page, "安全设置")

        self.terminal_page = TerminalPage(self.client)
        self.tabs.addTab(self.terminal_page, "命令终端")

        layout.addWidget(self.tabs)
        central_widget.setLayout(layout)

        self.tabs.currentChanged.connect(self.on_tab_changed)

    def create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件")
        refresh_action = QAction("刷新", self)
        refresh_action.setShortcut("F5")
        file_menu.addAction(refresh_action)

        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = menubar.addMenu("工具")
        settings_action = QAction("设置", self)
        tools_menu.addAction(settings_action)

        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_tool_bar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(lambda: self.on_tab_changed(self.tabs.currentIndex()))
        toolbar.addWidget(refresh_btn)

        toolbar.addSeparator()

        about_btn = QPushButton("关于")
        about_btn.clicked.connect(self.show_about)
        toolbar.addWidget(about_btn)

    def on_tab_changed(self, index):
        pass

    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec_()


def main():
    app = QApplication(sys.argv)

    client = LocalClient()

    window = MainWindow(client)
    window.show()

    ret = app.exec_()
    return ret


if __name__ == '__main__':
    sys.exit(main())