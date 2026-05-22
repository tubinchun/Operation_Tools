#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QLabel, QGroupBox, QTableWidget, QTableWidgetItem, QTextEdit,
    QComboBox, QSpinBox, QMessageBox, QProgressBar, QTabWidget,
    QFormLayout, QHeaderView, QFileDialog, QDialog, QCheckBox,
    QScrollArea, QFrame
)
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QLinearGradient, QPainter, QBrush
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect

class PXEInstallProgressWidget(QFrame):
    progress_updated = pyqtSignal(int, str, str)
    status_changed = pyqtSignal(str)
    
    INSTALL_STAGES = {
        'idle': {'name': '等待开始', 'color': '#9E9E9E', 'icon': '⏳'},
        'connecting': {'name': '正在连接', 'color': '#2196F3', 'icon': '🔗'},
        'downloading': {'name': '下载中', 'color': '#4CAF50', 'icon': '📥'},
        'partitioning': {'name': '磁盘分区', 'color': '#FF9800', 'icon': '💾'},
        'installing': {'name': '系统安装', 'color': '#4CAF50', 'icon': '⚙️'},
        'configuring': {'name': '配置系统', 'color': '#9C27B0', 'icon': '🔧'},
        'finishing': {'name': '完成安装', 'color': '#8BC34A', 'icon': '✅'},
        'completed': {'name': '安装完成', 'color': '#4CAF50', 'icon': '🎉'},
        'failed': {'name': '安装失败', 'color': '#f44336', 'icon': '❌'},
        'error': {'name': '发生错误', 'color': '#f44336', 'icon': '⚠️'}
    }
    
    def __init__(self, parent=None, client_mac=None):
        super().__init__(parent)
        self.client_mac = client_mac
        self.current_progress = 0
        self.current_status = 'idle'
        self.current_message = ''
        self.animation_timer = QTimer(self)
        self.animation_position = 0
        
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.init_ui()
        self.setup_animation()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        header_layout = QHBoxLayout()
        
        self.status_icon_label = QLabel(self.INSTALL_STAGES['idle']['icon'])
        self.status_icon_label.setFont(QFont('Arial', 16))
        self.status_icon_label.setAlignment(Qt.AlignCenter)
        self.status_icon_label.setFixedSize(30, 30)
        
        self.status_label = QLabel('等待开始')
        self.status_label.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        self.status_label.setStyleSheet(f"color: {self.INSTALL_STAGES['idle']['color']};")
        
        self.progress_percent_label = QLabel('0%')
        self.progress_percent_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.progress_percent_label.setStyleSheet("color: #4CAF50;")
        self.progress_percent_label.setAlignment(Qt.AlignRight)
        
        header_layout.addWidget(self.status_icon_label)
        header_layout.addWidget(self.status_label, 1)
        header_layout.addWidget(self.progress_percent_label)
        
        main_layout.addLayout(header_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                background-color: #f5f5f5;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #4CAF50,
                    stop: 0.5 #8BC34A,
                    stop: 1 #4CAF50
                );
                border-radius: 8px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        self.message_label = QLabel('')
        self.message_label.setFont(QFont('Microsoft YaHei', 9))
        self.message_label.setStyleSheet("color: #666; padding: 2px;")
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.message_label)
        
        self.stage_indicator_layout = QHBoxLayout()
        self.stage_indicator_layout.setSpacing(5)
        
        self.stage_labels = []
        stages = ['下载', '分区', '安装', '配置', '完成']
        for i, stage in enumerate(stages):
            stage_label = QLabel(stage)
            stage_label.setFont(QFont('Microsoft YaHei', 8))
            stage_label.setAlignment(Qt.AlignCenter)
            stage_label.setFixedHeight(20)
            stage_label.setStyleSheet("""
                QLabel {
                    background-color: #e0e0e0;
                    color: #999;
                    border-radius: 3px;
                    padding: 2px 5px;
                }
            """)
            self.stage_labels.append(stage_label)
            self.stage_indicator_layout.addWidget(stage_label)
            if i < len(stages) - 1:
                arrow_label = QLabel('→')
                arrow_label.setAlignment(Qt.AlignCenter)
                self.stage_indicator_layout.addWidget(arrow_label)
        
        self.stage_indicator_layout.addStretch()
        main_layout.addLayout(self.stage_indicator_layout)
        
        self.setLayout(main_layout)
        self.apply_styles()
    
    def setup_animation(self):
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.setInterval(50)
    
    def update_animation(self):
        self.animation_position = (self.animation_position + 1) % 100
        if self.current_status in ['downloading', 'installing', 'configuring']:
            if not self.animation_timer.isActive():
                self.animation_timer.start()
        else:
            self.animation_timer.stop()
    
    def set_progress(self, progress, status='idle', message=''):
        if not 0 <= progress <= 100:
            return
        
        old_progress = self.current_progress
        self.current_progress = progress
        self.current_status = status
        self.current_message = message
        
        self.progress_bar.setValue(progress)
        self.progress_percent_label.setText(f'{progress}%')
        self.message_label.setText(message)
        
        stage_info = self.INSTALL_STAGES.get(status, self.INSTALL_STAGES['idle'])
        self.status_icon_label.setText(stage_info['icon'])
        self.status_label.setText(stage_info['name'])
        self.status_label.setStyleSheet(f"color: {stage_info['color']}; font-weight: bold;")
        
        self.update_stage_indicators(progress, status)
        self.apply_styles()
        
        self.progress_updated.emit(progress, status, message)
        self.status_changed.emit(status)
    
    def update_stage_indicators(self, progress, status):
        stage_map = {
            'downloading': 0,
            'partitioning': 1,
            'installing': 2,
            'configuring': 3,
            'finishing': 4,
            'completed': 4
        }
        
        current_stage = stage_map.get(status, -1)
        
        for i, label in enumerate(self.stage_labels):
            if i < current_stage:
                label.setStyleSheet("""
                    QLabel {
                        background-color: #4CAF50;
                        color: white;
                        border-radius: 3px;
                        padding: 2px 5px;
                        font-weight: bold;
                    }
                """)
            elif i == current_stage:
                label.setStyleSheet("""
                    QLabel {
                        background-color: #FF9800;
                        color: white;
                        border-radius: 3px;
                        padding: 2px 5px;
                        font-weight: bold;
                    }
                """)
            else:
                label.setStyleSheet("""
                    QLabel {
                        background-color: #e0e0e0;
                        color: #999;
                        border-radius: 3px;
                        padding: 2px 5px;
                    }
                """)
    
    def apply_styles(self):
        if self.current_status == 'completed':
            self.setStyleSheet("""
                QFrame {
                    background-color: #E8F5E9;
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                }
            """)
        elif self.current_status in ['failed', 'error']:
            self.setStyleSheet("""
                QFrame {
                    background-color: #FFEBEE;
                    border: 2px solid #f44336;
                    border-radius: 8px;
                }
            """)
        elif self.current_status in ['downloading', 'installing']:
            self.setStyleSheet("""
                QFrame {
                    background-color: #E3F2FD;
                    border: 2px solid #2196F3;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #FAFAFA;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                }
            """)
    
    def reset(self):
        self.set_progress(0, 'idle', '')
    
    def get_progress(self):
        return self.current_progress
    
    def get_status(self):
        return self.current_status

class PXEClientProgressDialog(QDialog):
    def __init__(self, client_mac, client_ip, iso_name, parent=None):
        super().__init__(parent)
        self.client_mac = client_mac
        self.client_ip = client_ip
        self.iso_name = iso_name
        self.auto_refresh_enabled = True
        self.refresh_timer = QTimer(self)
        
        self.setWindowTitle(f'PXE安装进度 - {iso_name}')
        self.setModal(False)
        self.setMinimumSize(600, 400)
        self.init_ui()
        self.setup_auto_refresh()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        client_info_group = QGroupBox("客户端信息")
        client_info_layout = QFormLayout()
        client_info_layout.setVerticalSpacing(10)
        
        self.mac_label = QLabel(self.client_mac)
        self.mac_label.setStyleSheet("font-weight: bold; color: #1976D2;")
        
        self.ip_label = QLabel(self.client_ip)
        self.ip_label.setStyleSheet("font-weight: bold; color: #1976D2;")
        
        self.iso_label = QLabel(self.iso_name)
        self.iso_label.setStyleSheet("font-weight: bold; color: #1976D2;")
        
        client_info_layout.addRow("MAC地址:", self.mac_label)
        client_info_layout.addRow("IP地址:", self.ip_label)
        client_info_layout.addRow("安装镜像:", self.iso_label)
        client_info_group.setLayout(client_info_layout)
        layout.addWidget(client_info_group)
        
        self.progress_widget = PXEInstallProgressWidget(self, self.client_mac)
        layout.addWidget(self.progress_widget)
        
        control_layout = QHBoxLayout()
        
        self.auto_refresh_checkbox = QCheckBox("自动刷新")
        self.auto_refresh_checkbox.setChecked(True)
        self.auto_refresh_checkbox.stateChanged.connect(self.toggle_auto_refresh)
        self.auto_refresh_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        
        self.refresh_button = QPushButton("刷新状态")
        self.refresh_button.clicked.connect(self.refresh_progress)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        
        control_layout.addWidget(self.auto_refresh_checkbox)
        control_layout.addStretch()
        control_layout.addWidget(self.refresh_button)
        control_layout.addWidget(self.close_button)
        
        layout.addLayout(control_layout)
        
        self.setLayout(layout)
    
    def setup_auto_refresh(self):
        self.refresh_timer.timeout.connect(self.refresh_progress)
        self.refresh_timer.setInterval(2000)
        self.refresh_timer.start()
    
    def toggle_auto_refresh(self):
        self.auto_refresh_enabled = self.auto_refresh_checkbox.isChecked()
        if self.auto_refresh_enabled:
            self.refresh_timer.start()
        else:
            self.refresh_timer.stop()
    
    def refresh_progress(self):
        try:
            if hasattr(self.parent(), 'client'):
                response = self.parent().client.get_pxe_client_list()
                if response.get('status') == 'success':
                    clients = response.get('data', [])
                    for client in clients:
                        if client.get('mac') == self.client_mac:
                            progress = client.get('progress', 0)
                            status_msg = client.get('status', 'idle')
                            
                            status_map = {
                                '等待开始': 'idle',
                                '正在连接': 'connecting',
                                '下载中': 'downloading',
                                '磁盘分区': 'partitioning',
                                '系统安装': 'installing',
                                '配置系统': 'configuring',
                                '完成安装': 'finishing',
                                '安装完成': 'completed',
                                '安装失败': 'failed',
                                '发生错误': 'error'
                            }
                            
                            status = status_map.get(status_msg, 'idle')
                            
                            if status == 'completed':
                                self.progress_widget.set_progress(100, status, '安装已完成，客户端即将重启')
                                self.refresh_timer.stop()
                            elif status == 'failed':
                                self.progress_widget.set_progress(progress, status, status_msg)
                                self.refresh_timer.stop()
                            else:
                                self.progress_widget.set_progress(progress, status, status_msg)
                            break
        except Exception as e:
            pass

class UploadProgressDialog(QDialog):
    progress_updated = pyqtSignal(int, str, str, str)
    upload_finished = pyqtSignal(bool, str)
    
    def __init__(self, source_path, dest_dir, parent=None):
        super().__init__(parent)
        self.source_path = source_path
        self.dest_dir = dest_dir
        self.file_name = os.path.basename(source_path)
        self.total_size = os.path.getsize(source_path)
        self.uploaded_size = 0
        self.is_paused = False
        self.is_cancelled = False
        self.upload_thread = None
        self.start_time = None
        
        self.setWindowTitle(f"上传ISO文件 - {self.file_name}")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        file_info_layout = QVBoxLayout()
        self.file_name_label = QLabel(f"文件: {self.file_name}")
        self.file_name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.file_size_label = QLabel(f"大小: {self._format_size(self.total_size)}")
        self.file_size_label.setStyleSheet("color: #666;")
        
        file_info_layout.addWidget(self.file_name_label)
        file_info_layout.addWidget(self.file_size_label)
        layout.addLayout(file_info_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #d0d0d0;
                border-radius: 5px;
                text-align: center;
                height: 30px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        progress_info_layout = QHBoxLayout()
        self.progress_percent_label = QLabel("0%")
        self.progress_percent_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        
        self.progress_size_label = QLabel(f"0 B / {self._format_size(self.total_size)}")
        
        self.progress_speed_label = QLabel("速度: 0 B/s")
        self.progress_speed_label.setStyleSheet("color: #2196F3;")
        
        progress_info_layout.addWidget(self.progress_percent_label)
        progress_info_layout.addWidget(self.progress_size_label)
        progress_info_layout.addStretch()
        progress_info_layout.addWidget(self.progress_speed_label)
        layout.addLayout(progress_info_layout)
        
        self.status_label = QLabel("准备上传...")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel_upload)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        button_layout.addWidget(self.pause_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        self.progress_updated.connect(self.update_progress)
        self.upload_finished.connect(self.upload_completed)
    
    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def _format_speed(self, bytes_per_second):
        return f"{self._format_size(bytes_per_second)}/s"
    
    def start_upload(self):
        self.start_time = time.time()
        self.upload_thread = UploadThread(
            self.source_path,
            self.dest_dir,
            self
        )
        self.upload_thread.start()
        self.status_label.setText("正在上传...")
        self.status_label.setStyleSheet("color: #2196F3; padding: 5px; font-weight: bold;")
    
    def update_progress(self, percent, speed, uploaded, status):
        self.progress_bar.setValue(percent)
        self.progress_percent_label.setText(f"{percent}%")
        self.progress_size_label.setText(uploaded)
        self.progress_speed_label.setText(f"速度: {speed}")
        self.status_label.setText(status)
        
        if status == "上传中":
            self.status_label.setStyleSheet("color: #2196F3; padding: 5px; font-weight: bold;")
        elif status == "已暂停":
            self.status_label.setStyleSheet("color: #FF9800; padding: 5px; font-weight: bold;")
    
    def upload_completed(self, success, message):
        if success:
            self.progress_bar.setValue(100)
            self.progress_percent_label.setText("100%")
            self.status_label.setText("上传完成！")
            self.status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
            self.pause_btn.setEnabled(False)
            self.cancel_btn.setText("关闭")
            self.accept()
        else:
            self.status_label.setText(f"上传失败: {message}")
            self.status_label.setStyleSheet("color: #f44336; padding: 5px; font-weight: bold;")
            self.pause_btn.setEnabled(False)
            self.cancel_btn.setText("关闭")
    
    def toggle_pause(self):
        if not self.is_paused:
            self.is_paused = True
            self.pause_btn.setText("继续")
            self.pause_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            self.status_label.setText("已暂停")
            self.status_label.setStyleSheet("color: #FF9800; padding: 5px; font-weight: bold;")
            if self.upload_thread:
                self.upload_thread.pause()
        else:
            self.is_paused = False
            self.pause_btn.setText("暂停")
            self.pause_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            self.status_label.setText("正在上传...")
            self.status_label.setStyleSheet("color: #2196F3; padding: 5px; font-weight: bold;")
            if self.upload_thread:
                self.upload_thread.resume()
    
    def cancel_upload(self):
        if self.cancel_btn.text() == "关闭":
            self.accept()
            return
        
        reply = QMessageBox.question(
            self, "确认取消",
            "确定要取消上传吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.is_cancelled = True
            if self.upload_thread:
                self.upload_thread.cancel()
            self.reject()

class UploadThread(QThread):
    def __init__(self, source_path, dest_dir, dialog):
        super().__init__()
        self.source_path = source_path
        self.dest_dir = dest_dir
        self.dialog = dialog
        self._is_paused = False
        self._is_cancelled = False
        self._lock = __import__('threading').Lock()
    
    def run(self):
        try:
            if not os.path.exists(self.dest_dir):
                os.makedirs(self.dest_dir, exist_ok=True)
            
            dest_path = os.path.join(self.dest_dir, os.path.basename(self.source_path))
            
            if os.path.exists(dest_path):
                os.remove(dest_path)
            
            total_size = os.path.getsize(self.source_path)
            chunk_size = 1024 * 1024
            uploaded = 0
            last_update_time = time.time()
            last_uploaded = 0
            
            with open(self.source_path, 'rb') as src_file:
                with open(dest_path, 'wb') as dst_file:
                    while True:
                        if self._is_cancelled:
                            if os.path.exists(dest_path):
                                os.remove(dest_path)
                            return
                        
                        while self._is_paused:
                            if self._is_cancelled:
                                if os.path.exists(dest_path):
                                    os.remove(dest_path)
                                return
                            time.sleep(0.1)
                        
                        chunk = src_file.read(chunk_size)
                        if not chunk:
                            break
                        
                        dst_file.write(chunk)
                        uploaded += len(chunk)
                        
                        current_time = time.time()
                        if current_time - last_update_time >= 0.1:
                            percent = int((uploaded / total_size) * 100)
                            speed = (uploaded - last_uploaded) / (current_time - last_update_time)
                            uploaded_str = f"{self._format_size(uploaded)} / {self._format_size(total_size)}"
                            speed_str = self._format_speed(speed)
                            
                            self.dialog.progress_updated.emit(
                                percent,
                                speed_str,
                                uploaded_str,
                                "上传中"
                            )
                            
                            last_update_time = current_time
                            last_uploaded = uploaded
            
            self.dialog.upload_finished.emit(True, f"文件 {os.path.basename(self.source_path)} 上传成功")
            
        except Exception as e:
            self.dialog.upload_finished.emit(False, str(e))
    
    def pause(self):
        with self._lock:
            self._is_paused = True
    
    def resume(self):
        with self._lock:
            self._is_paused = False
    
    def cancel(self):
        with self._lock:
            self._is_cancelled = True
    
    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def _format_speed(self, bytes_per_second):
        return f"{self._format_size(bytes_per_second)}/s"

class ImageConfigDialog(QDialog):
    def __init__(self, client, iso_name, parent=None):
        super().__init__(parent)
        self.client = client
        self.iso_name = iso_name
        self.setWindowTitle(f"镜像配置 - {iso_name}")
        self.setMinimumSize(800, 600)
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        
        self.basic_tab = QWidget()
        self.grub_tab = QWidget()
        self.external_tab = QWidget()
        self.compatible_tab = QWidget()
        
        self.tabs.addTab(self.basic_tab, "基础配置")
        self.tabs.addTab(self.grub_tab, "GRUB编辑")
        self.tabs.addTab(self.external_tab, "外部文件")
        self.tabs.addTab(self.compatible_tab, "兼容模式")
        
        self.init_basic_tab()
        self.init_grub_tab()
        self.init_external_tab()
        self.init_compatible_tab()
        
        layout.addWidget(self.tabs)
        
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_config)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self.load_config)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def init_basic_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(10)
        
        self.ipxename_edit = QLineEdit()
        self.ipxename_edit.setPlaceholderText("配置ID")
        
        self.isoname_edit = QLineEdit()
        self.isoname_edit.setReadOnly(True)
        
        self.autoinstall_check = QCheckBox("自动安装")
        self.autoinstall_check.stateChanged.connect(self.toggle_autoinstall)
        
        self.compatible_check = QCheckBox("兼容模式")
        
        form_layout.addRow("配置ID:", self.ipxename_edit)
        form_layout.addRow("镜像名称:", self.isoname_edit)
        form_layout.addRow("", self.autoinstall_check)
        form_layout.addRow("", self.compatible_check)
        
        layout.addLayout(form_layout)
        
        self.autoinstall_group = QGroupBox("安装脚本")
        install_layout = QVBoxLayout()
        
        self.autoinstall_edit = QTextEdit()
        self.autoinstall_edit.setPlaceholderText(
            "桌面系统：使用镜像解压出来根目录的ky-installer.cfg。\n"
            "服务器系统：先安装一台，复制/root/anaconda-ks.cfg粘贴到此处。"
        )
        self.autoinstall_edit.setMinimumHeight(300)
        
        install_layout.addWidget(self.autoinstall_edit)
        self.autoinstall_group.setLayout(install_layout)
        self.autoinstall_group.setEnabled(False)
        
        layout.addWidget(self.autoinstall_group)
        layout.addStretch()
        
        self.basic_tab.setLayout(layout)
    
    def init_grub_tab(self):
        layout = QVBoxLayout()
        
        self.grub_edit = QTextEdit()
        self.grub_edit.setPlaceholderText("GRUB配置内容")
        
        layout.addWidget(self.grub_edit)
        
        self.grub_tab.setLayout(layout)
    
    def init_external_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(10)
        
        self.extpathname_edit = QLineEdit()
        self.extpathname_edit.setPlaceholderText("外部文件注入镜像的文件夹名称")
        self.extpathname_edit.setText("mpxe_extfile")
        
        form_layout.addRow("文件夹名称:", self.extpathname_edit)
        layout.addLayout(form_layout)
        
        external_group = QGroupBox("外部文件")
        external_layout = QVBoxLayout()
        
        self.external_edit = QTextEdit()
        self.external_edit.setPlaceholderText(
            "外部文件将挂载在iso根目录的mpxe_extfile（默认）文件夹下，\n"
            "请输入文件/文件夹绝对路径，一行一个"
        )
        self.external_edit.setMinimumHeight(300)
        
        external_layout.addWidget(self.external_edit)
        external_group.setLayout(external_layout)
        layout.addWidget(external_group)
        
        layout.addStretch()
        
        self.external_tab.setLayout(layout)
    
    def init_compatible_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        compat_group = QGroupBox("兼容模式设置")
        compat_layout = QFormLayout()
        compat_layout.setVerticalSpacing(10)
        
        self.boot_timeout_edit = QLineEdit()
        self.boot_timeout_edit.setPlaceholderText("60")
        
        self.language_edit = QLineEdit()
        self.language_edit.setPlaceholderText("zh_CN")
        
        self.keyboard_edit = QLineEdit()
        self.keyboard_edit.setPlaceholderText("us")
        
        self.timezone_edit = QLineEdit()
        self.timezone_edit.setPlaceholderText("Asia/Shanghai")
        
        self.driver_path_edit = QLineEdit()
        self.driver_path_edit.setPlaceholderText("驱动路径")
        
        self.kernel_params_edit = QLineEdit()
        self.kernel_params_edit.setPlaceholderText("nomodeset acpi=off")
        
        compat_layout.addRow("启动超时(秒):", self.boot_timeout_edit)
        compat_layout.addRow("语言设置:", self.language_edit)
        compat_layout.addRow("键盘布局:", self.keyboard_edit)
        compat_layout.addRow("时区:", self.timezone_edit)
        compat_layout.addRow("驱动路径:", self.driver_path_edit)
        compat_layout.addRow("内核参数:", self.kernel_params_edit)
        
        compat_group.setLayout(compat_layout)
        layout.addWidget(compat_group)
        
        driver_group = QGroupBox("额外驱动配置")
        driver_layout = QVBoxLayout()
        
        self.extra_drivers_edit = QTextEdit()
        self.extra_drivers_edit.setPlaceholderText("额外驱动模块，一行一个")
        self.extra_drivers_edit.setMinimumHeight(100)
        
        driver_layout.addWidget(self.extra_drivers_edit)
        driver_group.setLayout(driver_layout)
        layout.addWidget(driver_group)
        
        network_group = QGroupBox("网络配置")
        network_layout = QVBoxLayout()
        
        self.network_config_edit = QTextEdit()
        self.network_config_edit.setPlaceholderText("网络配置内容")
        self.network_config_edit.setMinimumHeight(100)
        
        network_layout.addWidget(self.network_config_edit)
        network_group.setLayout(network_layout)
        layout.addWidget(network_group)
        
        disk_group = QGroupBox("磁盘分区配置")
        disk_layout = QVBoxLayout()
        
        self.disk_partition_edit = QTextEdit()
        self.disk_partition_edit.setPlaceholderText("磁盘分区配置内容")
        self.disk_partition_edit.setMinimumHeight(100)
        
        disk_layout.addWidget(self.disk_partition_edit)
        disk_group.setLayout(disk_layout)
        layout.addWidget(disk_group)
        
        post_group = QGroupBox("安装后脚本")
        post_layout = QVBoxLayout()
        
        self.post_install_edit = QTextEdit()
        self.post_install_edit.setPlaceholderText("安装后执行的脚本")
        self.post_install_edit.setMinimumHeight(100)
        
        post_layout.addWidget(self.post_install_edit)
        post_group.setLayout(post_layout)
        layout.addWidget(post_group)
        
        custom_group = QGroupBox("自定义脚本")
        custom_layout = QVBoxLayout()
        
        self.custom_scripts_edit = QTextEdit()
        self.custom_scripts_edit.setPlaceholderText("自定义脚本内容")
        self.custom_scripts_edit.setMinimumHeight(100)
        
        custom_layout.addWidget(self.custom_scripts_edit)
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
        layout.addStretch()
        
        self.compatible_tab.setLayout(layout)
    
    def toggle_autoinstall(self):
        self.autoinstall_group.setEnabled(self.autoinstall_check.isChecked())
    
    def load_config(self):
        try:
            response = self.client.get_image_config(self.iso_name)
            if response.get('status') == 'success':
                config = response.get('data', {})
                
                self.ipxename_edit.setText(config.get('ipxename', ''))
                self.isoname_edit.setText(config.get('isoname', self.iso_name))
                self.autoinstall_check.setChecked(config.get('autoinstall', 'false') == 'true')
                self.compatible_check.setChecked(config.get('CompatibleMode', 'false') == 'true')
                self.autoinstall_edit.setPlainText(config.get('autoinstallcfg', ''))
                self.grub_edit.setPlainText(config.get('grubcfg', ''))
                self.extpathname_edit.setText(config.get('extpathname', 'mpxe_extfile'))
                self.external_edit.setPlainText(config.get('mpxe_extfile', ''))
                
                self.boot_timeout_edit.setText(config.get('boot_timeout', '60'))
                self.language_edit.setText(config.get('language', 'zh_CN'))
                self.keyboard_edit.setText(config.get('keyboard', 'us'))
                self.timezone_edit.setText(config.get('timezone', 'Asia/Shanghai'))
                self.driver_path_edit.setText(config.get('driver_path', ''))
                self.kernel_params_edit.setText(config.get('kernel_params', ''))
                self.extra_drivers_edit.setPlainText(config.get('extra_drivers', ''))
                self.network_config_edit.setPlainText(config.get('network_config', ''))
                self.disk_partition_edit.setPlainText(config.get('disk_partition', ''))
                self.post_install_edit.setPlainText(config.get('post_install', ''))
                self.custom_scripts_edit.setPlainText(config.get('custom_scripts', ''))
                
                if not config.get('autoinstallcfg') or not config.get('grubcfg'):
                    try:
                        extract_response = self.client.extract_iso_config({'iso_name': self.iso_name})
                        if extract_response.get('status') == 'success':
                            iso_config = extract_response.get('data', {})
                            
                            if not config.get('autoinstallcfg') and iso_config.get('ks_content'):
                                self.autoinstall_edit.setPlainText(iso_config.get('ks_content', ''))
                                self.autoinstall_check.setChecked(True)
                            
                            if not config.get('grubcfg') and iso_config.get('grub_content'):
                                self.grub_edit.setPlainText(iso_config.get('grub_content', ''))
                    except:
                        pass
                
                self.autoinstall_group.setEnabled(self.autoinstall_check.isChecked())
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载配置失败: {str(e)}")
    
    def save_config(self):
        try:
            params = {
                'iso_name': self.iso_name,
                'ipxename': self.ipxename_edit.text(),
                'autoinstall': 'true' if self.autoinstall_check.isChecked() else 'false',
                'CompatibleMode': 'true' if self.compatible_check.isChecked() else 'false',
                'autoinstallcfg': self.autoinstall_edit.toPlainText(),
                'grubcfg': self.grub_edit.toPlainText(),
                'extpathname': self.extpathname_edit.text(),
                'mpxe_extfile': self.external_edit.toPlainText(),
                'boot_timeout': self.boot_timeout_edit.text(),
                'language': self.language_edit.text(),
                'keyboard': self.keyboard_edit.text(),
                'timezone': self.timezone_edit.text(),
                'driver_path': self.driver_path_edit.text(),
                'kernel_params': self.kernel_params_edit.text(),
                'extra_drivers': self.extra_drivers_edit.toPlainText(),
                'network_config': self.network_config_edit.toPlainText(),
                'disk_partition': self.disk_partition_edit.toPlainText(),
                'post_install': self.post_install_edit.toPlainText(),
                'custom_scripts': self.custom_scripts_edit.toPlainText()
            }
            
            response = self.client.save_image_config(params)
            if response.get('status') == 'success':
                QMessageBox.information(self, "成功", response.get('message', '配置保存成功'))
            else:
                QMessageBox.warning(self, "失败", response.get('message', '保存失败'))
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

class PXEPage(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self._is_destroyed = False
        self.init_ui()
        self.load_status()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                padding: 8px 20px;
                margin-right: 4px;
                border-radius: 4px 4px 0 0;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom-color: #ffffff;
            }
        """)

        self.status_tab = QWidget()
        self.config_tab = QWidget()
        self.clients_tab = QWidget()
        self.iso_tab = QWidget()
        self.logs_tab = QWidget()
        self.whitelist_tab = QWidget()

        self.tabs.addTab(self.status_tab, "服务状态")
        self.tabs.addTab(self.config_tab, "网络配置")
        self.tabs.addTab(self.clients_tab, "客户端列表")
        self.tabs.addTab(self.iso_tab, "ISO管理")
        self.tabs.addTab(self.whitelist_tab, "黑白名单")
        self.tabs.addTab(self.logs_tab, "日志")

        self.init_status_tab()
        self.init_config_tab()
        self.init_clients_tab()
        self.init_iso_tab()
        self.init_whitelist_tab()
        self.init_logs_tab()

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def init_status_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        self.status_group = QGroupBox("PXE服务状态")
        status_layout = QFormLayout()
        status_layout.setVerticalSpacing(10)

        self.pxe_status_label = QLabel("状态: <font color='red'>未运行</font>")
        self.dhcp_status_label = QLabel("DHCP: 未运行")
        self.tftp_status_label = QLabel("TFTP: 未运行")
        self.http_status_label = QLabel("HTTP: 未运行")
        self.samba_status_label = QLabel("Samba: 未运行")

        status_layout.addRow("服务状态:", self.pxe_status_label)
        status_layout.addRow("DHCP服务:", self.dhcp_status_label)
        status_layout.addRow("TFTP服务:", self.tftp_status_label)
        status_layout.addRow("HTTP服务:", self.http_status_label)
        status_layout.addRow("Samba服务:", self.samba_status_label)

        self.status_group.setLayout(status_layout)
        layout.addWidget(self.status_group)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.start_button = QPushButton("启动服务")
        self.start_button.clicked.connect(self.start_pxe)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.stop_button = QPushButton("停止服务")
        self.stop_button.clicked.connect(self.stop_pxe)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)

        self.rescan_button = QPushButton("重新扫描ISO")
        self.rescan_button.clicked.connect(self.rescan_isos)
        self.rescan_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.rescan_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        layout.addStretch()

        self.status_tab.setLayout(layout)

    def init_config_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        self.config_group = QGroupBox("网络配置")
        config_layout = QFormLayout()
        config_layout.setVerticalSpacing(10)

        self.nic_combo = QComboBox()
        self.nic_combo.addItem("自动选择")

        self.server_ip_edit = QLineEdit()
        self.server_ip_edit.setPlaceholderText("服务器IP地址")
        self.server_ip_edit.setText("192.168.2.2")

        self.subnet_edit = QLineEdit()
        self.subnet_edit.setPlaceholderText("子网掩码")
        self.subnet_edit.setText("255.255.255.0")

        self.gateway_edit = QLineEdit()
        self.gateway_edit.setPlaceholderText("网关")
        self.gateway_edit.setText("192.168.2.1")

        self.dns_edit = QLineEdit()
        self.dns_edit.setPlaceholderText("DNS服务器")
        self.dns_edit.setText("8.8.8.8")

        self.ip_start_edit = QLineEdit()
        self.ip_start_edit.setPlaceholderText("IP起始地址")
        self.ip_start_edit.setText("192.168.2.100")

        self.ip_end_edit = QLineEdit()
        self.ip_end_edit.setPlaceholderText("IP结束地址")
        self.ip_end_edit.setText("192.168.2.150")

        self.http_port_spin = QSpinBox()
        self.http_port_spin.setRange(1, 65535)
        self.http_port_spin.setValue(80)

        self.tftp_port_spin = QSpinBox()
        self.tftp_port_spin.setRange(1, 65535)
        self.tftp_port_spin.setValue(69)

        config_layout.addRow("网卡:", self.nic_combo)
        config_layout.addRow("服务器IP:", self.server_ip_edit)
        config_layout.addRow("子网掩码:", self.subnet_edit)
        config_layout.addRow("网关:", self.gateway_edit)
        config_layout.addRow("DNS服务器:", self.dns_edit)
        config_layout.addRow("IP起始:", self.ip_start_edit)
        config_layout.addRow("IP结束:", self.ip_end_edit)
        config_layout.addRow("HTTP端口:", self.http_port_spin)
        config_layout.addRow("TFTP端口:", self.tftp_port_spin)

        self.config_group.setLayout(config_layout)
        layout.addWidget(self.config_group)

        self.save_button = QPushButton("保存配置")
        self.save_button.clicked.connect(self.save_config)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        layout.addWidget(self.save_button)
        layout.addStretch()

        self.config_tab.setLayout(layout)

    def init_clients_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        self.client_table = QTableWidget()
        self.client_table.setColumnCount(5)
        self.client_table.setHorizontalHeaderLabels(["MAC地址", "IP地址", "镜像名称", "进度", "状态"])
        self.client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.client_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.client_table)
        layout.addStretch()

        self.clients_tab.setLayout(layout)

    def init_iso_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        iso_path_group = QGroupBox("ISO文件存储位置")
        iso_path_layout = QVBoxLayout()
        
        self.iso_path_label = QLabel()
        self.iso_path_label.setStyleSheet("color: #1976D2; font-weight: bold;")
        self.iso_path_label.setWordWrap(True)
        iso_path_layout.addWidget(self.iso_path_label)
        
        hint_label = QLabel("请将ISO镜像文件上传至上述目录，或使用下方按钮选择文件复制到该目录")
        hint_label.setStyleSheet("color: #666;")
        iso_path_layout.addWidget(hint_label)
        
        iso_path_group.setLayout(iso_path_layout)
        layout.addWidget(iso_path_group)

        iso_list_group = QGroupBox("已上传的ISO文件")
        iso_list_layout = QVBoxLayout()

        self.iso_table = QTableWidget()
        self.iso_table.setColumnCount(5)
        self.iso_table.setHorizontalHeaderLabels(["文件名", "大小", "修改时间", "配置", "删除"])
        self.iso_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.iso_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.iso_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.iso_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.iso_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.iso_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                font-weight: bold;
            }
        """)
        iso_list_layout.addWidget(self.iso_table)

        button_layout = QHBoxLayout()
        
        self.upload_iso_button = QPushButton("上传ISO文件")
        self.upload_iso_button.clicked.connect(self.upload_iso_file)
        self.upload_iso_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.refresh_iso_button = QPushButton("刷新列表")
        self.refresh_iso_button.clicked.connect(self.load_iso_list)
        self.refresh_iso_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        self.open_iso_dir_button = QPushButton("打开ISO目录")
        self.open_iso_dir_button.clicked.connect(self.open_iso_directory)
        self.open_iso_dir_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        
        button_layout.addWidget(self.upload_iso_button)
        button_layout.addWidget(self.refresh_iso_button)
        button_layout.addWidget(self.open_iso_dir_button)
        button_layout.addStretch()
        
        iso_list_layout.addLayout(button_layout)
        iso_list_group.setLayout(iso_list_layout)
        layout.addWidget(iso_list_group)

        layout.addStretch()
        self.iso_tab.setLayout(layout)

    def init_whitelist_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        h_layout = QHBoxLayout()
        h_layout.setSpacing(20)

        self.whitelist_group = QGroupBox("白名单")
        whitelist_layout = QVBoxLayout()
        self.whitelist_edit = QTextEdit()
        self.whitelist_edit.setPlaceholderText("每行一个MAC地址，或用逗号分隔")
        whitelist_layout.addWidget(self.whitelist_edit)
        self.whitelist_group.setLayout(whitelist_layout)

        self.blacklist_group = QGroupBox("黑名单")
        blacklist_layout = QVBoxLayout()
        self.blacklist_edit = QTextEdit()
        self.blacklist_edit.setPlaceholderText("每行一个MAC地址，或用逗号分隔")
        blacklist_layout.addWidget(self.blacklist_edit)
        self.blacklist_group.setLayout(blacklist_layout)

        h_layout.addWidget(self.whitelist_group)
        h_layout.addWidget(self.blacklist_group)

        layout.addLayout(h_layout)

        self.save_whitelist_button = QPushButton("保存黑白名单")
        self.save_whitelist_button.clicked.connect(self.save_blackwhitelist)
        self.save_whitelist_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        layout.addWidget(self.save_whitelist_button)
        layout.addStretch()

        self.whitelist_tab.setLayout(layout)

    def init_logs_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        button_layout = QHBoxLayout()
        
        self.refresh_logs_button = QPushButton("刷新日志")
        self.refresh_logs_button.clicked.connect(self.load_logs)
        self.refresh_logs_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        self.log_type_combo = QComboBox()
        self.log_type_combo.addItem("全部日志", "all")
        self.log_type_combo.addItem("系统日志", "system")
        self.log_type_combo.addItem("客户端日志", "client")
        self.log_type_combo.addItem("DHCP日志", "dhcp")
        
        self.lines_spin = QSpinBox()
        self.lines_spin.setPrefix("显示行数: ")
        self.lines_spin.setRange(100, 5000)
        self.lines_spin.setSingleStep(100)
        self.lines_spin.setValue(500)
        
        button_layout.addWidget(self.refresh_logs_button)
        button_layout.addWidget(self.log_type_combo)
        button_layout.addWidget(self.lines_spin)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        
        layout.addWidget(self.logs_text)
        self.logs_tab.setLayout(layout)

    def load_status(self):
        if self._is_destroyed:
            return
        try:
            response = self.client.get_pxe_status()
            if response.get('status') == 'success':
                data = response.get('data', {})
                running = data.get('running', False)
                service_status = data.get('service_status', {})

                if running:
                    self.pxe_status_label.setText("状态: <font color='green'>运行中</font>")
                else:
                    self.pxe_status_label.setText("状态: <font color='red'>未运行</font>")

                dhcp_status = service_status.get('dhcp', 'unknown')
                tftp_status = service_status.get('tftp', 'unknown')
                http_status = service_status.get('http', 'unknown')
                samba_status = service_status.get('samba', 'unknown')

                self.dhcp_status_label.setText(f"DHCP: {'运行中' if dhcp_status == 'running' else '未运行'}")
                self.tftp_status_label.setText(f"TFTP: {'运行中' if tftp_status == 'running' else '未运行'}")
                self.http_status_label.setText(f"HTTP: {'运行中' if http_status == 'running' else '未运行'}")
                self.samba_status_label.setText(f"Samba: {'运行中' if samba_status == 'running' else '未运行'}")

                config = data.get('config', {})
                if config:
                    self.server_ip_edit.setText(config.get('DHCP_SERVER_IP', ''))
                    self.subnet_edit.setText(config.get('DHCP_SUBNET', ''))
                    self.gateway_edit.setText(config.get('DHCP_ROUTER', ''))
                    self.dns_edit.setText(config.get('DHCP_DNS', ''))
                    self.ip_start_edit.setText(config.get('DHCP_OFFER_BEGIN', ''))
                    self.ip_end_edit.setText(config.get('DHCP_OFFER_END', ''))
                    self.http_port_spin.setValue(config.get('HTTP_PORT', 80))
                    self.tftp_port_spin.setValue(config.get('TFTP_PORT', 69))

        except Exception as e:
            pass

        self.load_network_info()
        self.load_client_list()
        self.load_iso_list()
        self.load_blackwhitelist()
        self.load_logs()

    def load_network_info(self):
        try:
            response = self.client.get_pxe_network_info()
            if response.get('status') == 'success':
                nics = response.get('data', [])
                self.nic_combo.clear()
                self.nic_combo.addItem("自动选择", "")
                for nic in nics:
                    self.nic_combo.addItem(f"{nic.get('name')} ({nic.get('ip_address')})", nic.get('name'))
        except Exception as e:
            pass

    def load_client_list(self):
        try:
            response = self.client.get_pxe_client_list()
            if response.get('status') == 'success':
                clients = response.get('data', [])
                self.client_table.setRowCount(len(clients))
                for i, client in enumerate(clients):
                    self.client_table.setItem(i, 0, QTableWidgetItem(client.get('mac', '')))
                    self.client_table.setItem(i, 1, QTableWidgetItem(client.get('ip', '')))
                    self.client_table.setItem(i, 2, QTableWidgetItem(client.get('isoname', '')))
                    self.client_table.setItem(i, 3, QTableWidgetItem(str(client.get('progress', 0))))
                    self.client_table.setItem(i, 4, QTableWidgetItem(client.get('status', '')))
        except Exception as e:
            pass

    def load_iso_list(self):
        try:
            response = self.client.get_iso_list()
            if response.get('status') == 'success':
                iso_path = response.get('iso_path', '')
                self.iso_path_label.setText(f"📁 {iso_path}")
                
                iso_files = response.get('data', [])
                self.iso_table.setRowCount(len(iso_files))
                for i, iso_file in enumerate(iso_files):
                    name = iso_file.get('name', '')
                    self.iso_table.setItem(i, 0, QTableWidgetItem(name))
                    self.iso_table.setItem(i, 1, QTableWidgetItem(iso_file.get('size', '')))
                    self.iso_table.setItem(i, 2, QTableWidgetItem(iso_file.get('mtime', '')))
                    
                    config_btn = QPushButton("配置")
                    config_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #2196F3;
                            color: white;
                            border: none;
                            padding: 5px 15px;
                            border-radius: 3px;
                        }
                        QPushButton:hover {
                            background-color: #1976D2;
                        }
                    """)
                    config_btn.clicked.connect(lambda checked, n=name: self.open_image_config(n))
                    self.iso_table.setCellWidget(i, 3, config_btn)
                    
                    delete_btn = QPushButton("删除")
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #f44336;
                            color: white;
                            border: none;
                            padding: 5px 15px;
                            border-radius: 3px;
                        }
                        QPushButton:hover {
                            background-color: #da190b;
                        }
                    """)
                    delete_btn.clicked.connect(lambda checked, n=name: self.delete_iso_file(n))
                    self.iso_table.setCellWidget(i, 4, delete_btn)
        except Exception as e:
            pass

    def load_blackwhitelist(self):
        try:
            response = self.client.get_pxe_blackwhitelist()
            if response.get('status') == 'success':
                data = response.get('data', {})
                self.whitelist_edit.setPlainText(data.get('whitelist', ''))
                self.blacklist_edit.setPlainText(data.get('blacklist', ''))
        except Exception as e:
            pass

    def load_logs(self):
        try:
            params = {
                'type': self.log_type_combo.currentData(),
                'lines': self.lines_spin.value()
            }
            response = self.client.get_pxe_logs(params)
            if response.get('status') == 'success':
                self.logs_text.setPlainText(response.get('data', ''))
        except Exception as e:
            pass

    def start_pxe(self):
        try:
            response = self.client.start_samba_service()
            if response.get('status') == 'success':
                print("Samba服务启动成功")
            else:
                print(f"Samba服务启动失败: {response.get('message', '')}")
            
            response = self.client.start_pxe_services()
            if response.get('status') == 'success':
                QMessageBox.information(self, "成功", response.get('message', '服务启动成功'))
            else:
                QMessageBox.warning(self, "失败", response.get('message', '启动失败'))
            self.load_status()
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def stop_pxe(self):
        try:
            response = self.client.stop_pxe_services()
            if response.get('status') == 'success':
                QMessageBox.information(self, "成功", response.get('message', 'PXE服务已停止'))
            else:
                QMessageBox.warning(self, "失败", response.get('message', '停止失败'))
            self.load_status()
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def rescan_isos(self):
        try:
            response = self.client.rescan_pxe_isos()
            if response.get('status') == 'success':
                QMessageBox.information(self, "成功", response.get('message', '重新扫描完成'))
            else:
                QMessageBox.warning(self, "失败", response.get('message', '扫描失败'))
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def upload_iso_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择ISO文件", "", "ISO文件 (*.iso);;所有文件 (*)"
        )
        if file_path:
            try:
                iso_dir = self.client.get_iso_list().get('iso_path', '/var/lib/kylin-system-tools/pxe/iso')
                
                dialog = UploadProgressDialog(file_path, iso_dir, self)
                dialog.start_upload()
                
                if dialog.exec_() == QDialog.Accepted:
                    self.load_iso_list()
            except Exception as e:
                QMessageBox.warning(self, "错误", f"上传失败: {str(e)}")

    def delete_iso_file(self, file_name):
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除ISO文件吗？\n\n文件名: {file_name}\n\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                response = self.client.delete_iso_file(file_name)
                if response.get('status') == 'success':
                    QMessageBox.information(self, "成功", response.get('message', 'ISO文件删除成功'))
                    self.load_iso_list()
                else:
                    QMessageBox.warning(self, "失败", response.get('message', '删除失败'))
            except Exception as e:
                QMessageBox.warning(self, "错误", str(e))

    def open_iso_directory(self):
        try:
            response = self.client.open_iso_directory()
            if response.get('status') != 'success':
                QMessageBox.warning(self, "失败", response.get('message', '打开目录失败'))
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def open_image_config(self, iso_name):
        dialog = ImageConfigDialog(self.client, iso_name, self)
        dialog.exec_()

    def save_config(self):
        params = {
            'ip_address': self.server_ip_edit.text(),
            'gateway': self.gateway_edit.text(),
            'name': self.nic_combo.currentData(),
            'netmask': self.subnet_edit.text(),
            'ip_start': self.ip_start_edit.text(),
            'ip_end': self.ip_end_edit.text()
        }
        try:
            response = self.client.update_pxe_config(params)
            if response.get('status') == 'success':
                QMessageBox.information(self, "成功", response.get('message', '配置保存成功'))
            else:
                QMessageBox.warning(self, "失败", response.get('message', '保存失败'))
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def save_blackwhitelist(self):
        params = {
            'whitelist': self.whitelist_edit.toPlainText(),
            'blacklist': self.blacklist_edit.toPlainText()
        }
        try:
            response = self.client.set_pxe_blackwhitelist(params)
            if response.get('status') == 'success':
                QMessageBox.information(self, "成功", response.get('message', '保存成功'))
            else:
                QMessageBox.warning(self, "失败", response.get('message', '保存失败'))
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def destroy(self):
        self._is_destroyed = True

class PXEToolCard(QWidget):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        icon_label = QLabel()
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                text-align: center;
            }
        """)
        icon_label.setText("📦")

        title_label = QLabel("网络装机")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                text-align: center;
            }
        """)

        desc_label = QLabel("PXE网络启动服务")
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
                text-align: center;
            }
        """)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()

        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            QWidget:hover {
                border-color: #4CAF50;
                box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);
            }
        """)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)
