#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.client import KylinClient
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTextEdit,
    QTableWidget, QTableWidgetItem, QTreeWidget,
    QTreeWidgetItem, QSplitter, QStatusBar, QMenuBar,
    QMenu, QAction, QToolBar, QComboBox, QLineEdit,
    QGroupBox, QFormLayout, QSpinBox, QCheckBox,
    QMessageBox, QProgressBar, QTableView, QHeaderView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor


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


class SystemInfoPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        info_group = QGroupBox("系统信息")
        info_layout = QFormLayout()

        self.hostname_label = QLabel("未知")
        self.os_version_label = QLabel("银河麒麟桌面V10 SP1")
        self.kernel_label = QLabel("未知")
        self.arch_label = QLabel("未知")

        info_layout.addRow("主机名:", self.hostname_label)
        info_layout.addRow("操作系统:", self.os_version_label)
        info_layout.addRow("内核版本:", self.kernel_label)
        info_layout.addRow("架构:", self.arch_label)
        info_group.setLayout(info_layout)

        refresh_btn = QPushButton("刷新信息")
        refresh_btn.clicked.connect(self.load_system_info)

        layout.addWidget(info_group)
        layout.addWidget(refresh_btn)
        layout.addStretch()
        self.setLayout(layout)

    def load_system_info(self):
        def fetch_info():
            return self.client.get_system_info()

        def on_result(result):
            if result.get('status') == 'success':
                data = result.get('data', {})
                self.hostname_label.setText(data.get('hostname', '未知'))
                self.kernel_label.setText(data.get('kernel', '未知'))
                self.arch_label.setText(data.get('architecture', '未知'))

        self.thread = WorkerThread(fetch_info)
        self.thread.finished.connect(on_result)
        self.thread.start()


class SystemStatusPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        splitter = QSplitter(Qt.Vertical)

        cpu_group = QGroupBox("CPU信息")
        cpu_layout = QVBoxLayout()
        self.cpu_text = QTextEdit()
        self.cpu_text.setReadOnly(True)
        cpu_layout.addWidget(self.cpu_text)
        cpu_group.setLayout(cpu_layout)

        memory_group = QGroupBox("内存信息")
        memory_layout = QVBoxLayout()
        self.memory_text = QTextEdit()
        self.memory_text.setReadOnly(True)
        memory_layout.addWidget(self.memory_text)
        memory_group.setLayout(memory_layout)

        splitter.addWidget(cpu_group)
        splitter.addWidget(memory_group)

        process_group = QGroupBox("TOP进程")
        process_layout = QVBoxLayout()
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels(['USER', 'PID', 'CPU%', 'MEM%', 'COMMAND'])
        process_layout.addWidget(self.process_table)
        process_group.setLayout(process_layout)

        refresh_btn = QPushButton("刷新状态")
        refresh_btn.clicked.connect(self.load_status)

        layout.addWidget(splitter)
        layout.addWidget(process_group)
        layout.addWidget(refresh_btn)
        self.setLayout(layout)

    def load_status(self):
        def fetch_cpu():
            return self.client.get_cpu_info()

        def fetch_memory():
            return self.client.get_memory_info()

        def fetch_processes():
            return self.client.get_process_list(20)

        def on_cpu(result):
            if result.get('status') == 'success':
                self.cpu_text.setPlainText(result.get('data', {}).get('cpuinfo', ''))

        def on_memory(result):
            if result.get('status') == 'success':
                self.memory_text.setPlainText(result.get('data', {}).get('meminfo', ''))

        def on_processes(result):
            if result.get('status') == 'success':
                lines = result.get('data', {}).get('processes', '').strip().split('\n')
                self.process_table.setRowCount(len(lines) - 1)
                for i, line in enumerate(lines[1:], 0):
                    parts = line.split()
                    if len(parts) >= 11:
                        for j, item in enumerate([parts[0], parts[1], parts[2], parts[3], ' '.join(parts[10:])]):
                            self.process_table.setItem(i, j, QTableWidgetItem(item))

        self.thread1 = WorkerThread(fetch_cpu)
        self.thread1.finished.connect(on_cpu)
        self.thread1.start()

        self.thread2 = WorkerThread(fetch_memory)
        self.thread2.finished.connect(on_memory)
        self.thread2.start()

        self.thread3 = WorkerThread(fetch_processes)
        self.thread3.finished.connect(on_processes)
        self.thread3.start()


class DiskPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.disk_text = QTextEdit()
        self.disk_text.setReadOnly(True)

        refresh_btn = QPushButton("刷新磁盘信息")
        refresh_btn.clicked.connect(self.load_disk_info)

        layout.addWidget(self.disk_text)
        layout.addWidget(refresh_btn)
        self.setLayout(layout)

    def load_disk_info(self):
        def fetch():
            return self.client.get_disk_info()

        def on_result(result):
            if result.get('status') == 'success':
                self.disk_text.setPlainText(result.get('data', {}).get('disk', ''))

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()


class NetworkPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        info_group = QGroupBox("网络信息")
        info_layout = QVBoxLayout()
        self.network_text = QTextEdit()
        self.network_text.setReadOnly(True)
        info_layout.addWidget(self.network_text)
        info_group.setLayout(info_layout)

        control_group = QGroupBox("网络控制")
        control_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新")
        restart_btn = QPushButton("重启网络")
        restart_btn.clicked.connect(self.restart_network)

        control_layout.addWidget(refresh_btn)
        control_layout.addWidget(restart_btn)
        control_group.setLayout(control_layout)

        layout.addWidget(info_group)
        layout.addWidget(control_group)
        self.setLayout(layout)

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
                QMessageBox.information(self, "成功", result.get('message', '操作成功'))
            else:
                QMessageBox.warning(self, "失败", result.get('message', '操作失败'))

        self.thread = WorkerThread(do_restart)
        self.thread.finished.connect(on_result)
        self.thread.start()


class ServicePage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.service_text = QTextEdit()
        self.service_text.setReadOnly(True)

        refresh_btn = QPushButton("刷新服务列表")
        refresh_btn.clicked.connect(self.load_services)

        layout.addWidget(self.service_text)
        layout.addWidget(refresh_btn)
        self.setLayout(layout)

    def load_services(self):
        def fetch():
            return self.client.get_service_list()

        def on_result(result):
            if result.get('status') == 'success':
                self.service_text.setPlainText(result.get('data', {}).get('services', ''))

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()


class UserManagementPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.user_text = QTextEdit()
        self.user_text.setReadOnly(True)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新用户列表")
        refresh_btn.clicked.connect(self.load_users)

        history_btn = QPushButton("登录历史")
        history_btn.clicked.connect(self.load_login_history)

        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(history_btn)

        layout.addWidget(self.user_text)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_users(self):
        def fetch():
            return self.client.get_users()

        def on_result(result):
            if result.get('status') == 'success':
                self.user_text.setPlainText(result.get('data', {}).get('users', ''))

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def load_login_history(self):
        def fetch():
            return self.client.get_login_history()

        def on_result(result):
            if result.get('status') == 'success':
                self.user_text.setPlainText(result.get('data', {}).get('login_history', ''))

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()


class SoftwarePage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        sources_group = QGroupBox("APT源")
        sources_layout = QVBoxLayout()
        self.sources_text = QTextEdit()
        self.sources_text.setReadOnly(True)
        sources_layout.addWidget(self.sources_text)
        sources_group.setLayout(sources_layout)

        packages_group = QGroupBox("已安装软件包")
        packages_layout = QVBoxLayout()
        self.packages_text = QTextEdit()
        self.packages_text.setReadOnly(True)
        packages_layout.addWidget(self.packages_text)
        packages_group.setLayout(packages_layout)

        btn_layout = QHBoxLayout()
        sources_btn = QPushButton("刷新APT源")
        sources_btn.clicked.connect(self.load_sources)

        packages_btn = QPushButton("刷新软件包")
        packages_btn.clicked.connect(self.load_packages)

        btn_layout.addWidget(sources_btn)
        btn_layout.addWidget(packages_btn)

        layout.addWidget(sources_group)
        layout.addWidget(packages_group)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

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


class LogPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新日志")
        refresh_btn.clicked.connect(self.load_logs)

        cleanup_btn = QPushButton("清理日志")
        cleanup_btn.clicked.connect(self.cleanup_logs)

        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(cleanup_btn)

        layout.addWidget(self.log_text)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_logs(self):
        def fetch():
            return self.client.get_system_logs(100)

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


class SecurityPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        kysec_group = QGroupBox("Kysec安全中心")
        kysec_layout = QVBoxLayout()

        self.kysec_status_label = QLabel("未知")
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("状态:"))
        status_layout.addWidget(self.kysec_status_label)
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

        kysec_layout.addLayout(status_layout)
        kysec_layout.addLayout(btn_layout)
        kysec_group.setLayout(kysec_layout)

        layout.addWidget(kysec_group)
        layout.addStretch()
        self.setLayout(layout)

    def load_kysec_status(self):
        def fetch():
            return self.client.get_kysec_status()

        def on_result(result):
            if result.get('status') == 'success':
                self.kysec_status_label.setText(result.get('data', {}).get('kysec', '未知').strip()[:100])

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def set_kysec(self, action):
        def do_set():
            return self.client.set_kysec(action)

        def on_result(result):
            if result.get('status') == 'success':
                QMessageBox.information(self, "成功", result.get('message', '操作成功'))
                self.load_kysec_status()
            else:
                QMessageBox.warning(self, "失败", result.get('message', '操作失败'))

        self.thread = WorkerThread(do_set)
        self.thread.finished.connect(on_result)
        self.thread.start()


class TerminalPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("输入命令...")
        self.command_input.returnPressed.connect(self.execute_command)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        execute_btn = QPushButton("执行")
        execute_btn.clicked.connect(self.execute_command)

        layout.addWidget(self.command_input)
        layout.addWidget(self.output_text)
        layout.addWidget(execute_btn)
        self.setLayout(layout)

    def execute_command(self):
        cmd = self.command_input.text().strip()
        if not cmd:
            return

        self.output_text.append(f"$ {cmd}")

        def do_execute():
            return self.client.execute_command(cmd)

        def on_result(result):
            if result.get('status') == 'success':
                output = result.get('data', {}).get('output', '')
                self.output_text.append(output)
            else:
                self.output_text.append(f"错误: {result.get('message', '未知错误')}")
            self.output_text.append("")

        self.thread = WorkerThread(do_execute)
        self.thread.finished.connect(on_result)
        self.thread.start()

        self.command_input.clear()


class MainWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.setWindowTitle("麒麟运维百宝箱")
        self.setGeometry(100, 100, 1200, 800)
        self.init_ui()

    def init_ui(self):
        self.statusBar().showMessage("就绪")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        self.tabs = QTabWidget()

        self.system_info_page = SystemInfoPage(self.client)
        self.tabs.addTab(self.system_info_page, "系统信息")

        self.system_status_page = SystemStatusPage(self.client)
        self.tabs.addTab(self.system_status_page, "系统状态")

        self.disk_page = DiskPage(self.client)
        self.tabs.addTab(self.disk_page, "磁盘信息")

        self.network_page = NetworkPage(self.client)
        self.tabs.addTab(self.network_page, "网络设置")

        self.service_page = ServicePage(self.client)
        self.tabs.addTab(self.service_page, "服务管理")

        self.user_page = UserManagementPage(self.client)
        self.tabs.addTab(self.user_page, "用户管理")

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

    def on_tab_changed(self, index):
        if index == 0:
            self.system_info_page.load_system_info()
        elif index == 1:
            self.system_status_page.load_status()
        elif index == 2:
            self.disk_page.load_disk_info()
        elif index == 3:
            self.network_page.load_network_info()
        elif index == 4:
            self.service_page.load_services()
        elif index == 5:
            self.user_page.load_users()
        elif index == 6:
            self.software_page.load_sources()
            self.software_page.load_packages()
        elif index == 7:
            self.log_page.load_logs()
        elif index == 8:
            self.security_page.load_kysec_status()


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
        QMessageBox.critical(None, "连接失败", f"无法连接到服务器 {host}:{port}")
        return 1

    window = MainWindow(client)
    window.show()

    ret = app.exec_()
    client.disconnect()
    return ret


if __name__ == '__main__':
    sys.exit(main())
