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
    QListWidgetItem, QAbstractItemView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon


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
        self.setFixedSize(400, 300)
        layout = QVBoxLayout()

        title = QLabel("银河麒麟运维管理工具")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        version = QLabel("版本: 1.0.0")
        version.setAlignment(Qt.AlignCenter)

        desc = QLabel("适配: 银河麒麟桌面V10 SP1\n"
                     "架构: ARM/飞腾CPU\n\n"
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
        self.init_ui()
        self.load_system_info()

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

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(5000)

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
                mem_data = mem_result.get('data', {}).get('meminfo', '')
                lines = mem_data.split('\n') if mem_data else []
                mem_total = mem_free = 0
                for line in lines:
                    if line.startswith('MemTotal:'):
                        mem_total = int(line.split()[1]) if len(line.split()) > 1 else 0
                    elif line.startswith('MemAvailable:'):
                        mem_free = int(line.split()[1]) if len(line.split()) > 1 else 0
                if mem_total > 0:
                    used = (mem_total - mem_free) * 100 // mem_total
                    self.memory_val.setText(f"{used}% 已使用")
                    self.mem_bar.setValue(used)

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

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


class SystemStatusPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()
        self.load_status()

    def init_ui(self):
        main_layout = QVBoxLayout()

        header = QLabel("系统状态监控")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        self.tabs = QTabWidget()

        self.cpu_tab = QWidget()
        cpu_layout = QVBoxLayout()
        self.cpu_text = QTextEdit()
        self.cpu_text.setReadOnly(True)
        cpu_layout.addWidget(self.cpu_text)
        self.cpu_tab.setLayout(cpu_layout)
        self.tabs.addTab(self.cpu_tab, "CPU信息")

        self.mem_tab = QWidget()
        mem_layout = QVBoxLayout()
        self.mem_text = QTextEdit()
        self.mem_text.setReadOnly(True)
        mem_layout.addWidget(self.mem_text)
        self.mem_tab.setLayout(mem_layout)
        self.tabs.addTab(self.mem_tab, "内存信息")

        self.process_tab = QWidget()
        process_layout = QVBoxLayout()
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels(['USER', 'PID', 'CPU%', 'MEM%', 'RSS', 'COMMAND'])
        self.process_table.horizontalHeader().setSectionResizeMode(4, 1)
        process_layout.addWidget(self.process_table)
        self.process_tab.setLayout(process_layout)
        self.tabs.addTab(self.process_tab, "TOP进程")

        self.service_tab = QWidget()
        service_layout = QVBoxLayout()
        self.service_text = QTextEdit()
        self.service_text.setReadOnly(True)
        service_layout.addWidget(self.service_text)
        self.service_tab.setLayout(service_layout)
        self.tabs.addTab(self.service_tab, "系统服务")

        main_layout.addWidget(self.tabs)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新状态")
        refresh_btn.clicked.connect(self.load_status)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def load_status(self):
        def fetch_cpu():
            return self.client.get_cpu_info()

        def fetch_mem():
            return self.client.get_memory_info()

        def fetch_proc():
            return self.client.get_process_list(20)

        def fetch_svc():
            return self.client.get_service_list()

        def on_cpu(result):
            if result.get('status') == 'success':
                self.cpu_text.setPlainText(result.get('data', {}).get('cpuinfo', ''))

        def on_mem(result):
            if result.get('status') == 'success':
                self.mem_text.setPlainText(result.get('data', {}).get('meminfo', ''))

        def on_proc(result):
            if result.get('status') == 'success':
                lines = result.get('data', {}).get('processes', '').strip().split('\n')
                self.process_table.setRowCount(max(0, len(lines) - 1))
                for i, line in enumerate(lines[1:], 0):
                    parts = line.split()
                    if len(parts) >= 11:
                        items = [parts[0], parts[1], parts[2], parts[3], parts[5], ' '.join(parts[10:])]
                        for j, item in enumerate(items[:6]):
                            self.process_table.setItem(i, j, QTableWidgetItem(item))

        def on_svc(result):
            if result.get('status') == 'success':
                self.service_text.setPlainText(result.get('data', {}).get('services', ''))

        self.thread1 = WorkerThread(fetch_cpu)
        self.thread1.finished.connect(on_cpu)
        self.thread1.start()

        self.thread2 = WorkerThread(fetch_mem)
        self.thread2.finished.connect(on_mem)
        self.thread2.start()

        self.thread3 = WorkerThread(fetch_proc)
        self.thread3.finished.connect(on_proc)
        self.thread3.start()

        self.thread4 = WorkerThread(fetch_svc)
        self.thread4.finished.connect(on_svc)
        self.thread4.start()


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
                users = result.get('data', {}).get('users', '')
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

    def init_ui(self):
        self.statusBar().showMessage("就绪 | 未连接")

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
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    host = 'localhost'
    port = 29876

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

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
