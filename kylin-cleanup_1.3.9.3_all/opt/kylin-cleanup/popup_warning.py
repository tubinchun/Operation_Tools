#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 倒计时警告与取消弹窗 (Kylin / openKylin 适配)
# 用法: python3 popup_warning.py "标题" "提示内容" 倒计时秒数

import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon

class WarningDialog(QWidget):
    def __init__(self, title, message, timeout_seconds):
        super().__init__()
        self.title = title
        self.message = message
        self.timeout_seconds = int(timeout_seconds)
        self.remaining = self.timeout_seconds
        
        self.initUI()
        
    def initUI(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(350, 150)
        
        # 将窗口移动到右下角
        desktop = QApplication.desktop().availableGeometry()
        x = desktop.width() - self.width() - 20
        y = desktop.height() - self.height() - 40
        self.move(x, y)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 背景容器
        bg_widget = QWidget()
        bg_widget.setObjectName("bgWidget")
        bg_widget.setStyleSheet("""
            #bgWidget {
                background-color: rgba(40, 44, 52, 240);
                border: 1px solid #3e4451;
                border-radius: 8px;
            }
            QLabel { color: #abb2bf; }
        """)
        layout = QVBoxLayout(bg_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题栏
        title_layout = QHBoxLayout()
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 18px;")
        title_layout.addWidget(icon_label)
        
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Sans Serif", 12, QFont.Bold))
        self.title_label.setStyleSheet("color: #e06c75;")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch(1)
        layout.addLayout(title_layout)
        
        # 消息内容
        self.msg_label = QLabel(self.message)
        self.msg_label.setWordWrap(True)
        self.msg_label.setFont(QFont("Sans Serif", 10))
        layout.addWidget(self.msg_label)
        
        layout.addSpacing(10)
        
        # 底部按钮和倒计时
        bottom_layout = QHBoxLayout()
        self.countdown_label = QLabel(f"{self.remaining} 秒后执行...")
        self.countdown_label.setFont(QFont("Sans Serif", 9))
        self.countdown_label.setStyleSheet("color: #98c379;")
        bottom_layout.addWidget(self.countdown_label)
        
        bottom_layout.addStretch(1)
        
        cancel_btn = QPushButton("取消操作")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e06c75;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #be5046; }
        """)
        cancel_btn.clicked.connect(self.cancel_action)
        bottom_layout.addWidget(cancel_btn)
        
        layout.addLayout(bottom_layout)
        main_layout.addWidget(bg_widget)
        
        # 启动定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)
        
    def update_countdown(self):
        self.remaining -= 1
        if self.remaining <= 0:
            self.timer.stop()
            self.accept_action()
        else:
            self.countdown_label.setText(f"{self.remaining} 秒后执行...")
            
    def cancel_action(self):
        # 用户点击取消，退出码 1 (明确拦截下沉)
        QApplication.instance().exit(1)
        
    def accept_action(self):
        # 倒计时结束，正常允许执行，退出码 0 (默认放行)
        QApplication.instance().exit(0)

    def closeEvent(self, event):
        # 用户点击 X 关闭窗口或 Alt+F4，也视为不拦截 (退出码 0)
        self.timer.stop()
        QApplication.instance().exit(0)
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 参数解析
    title = sys.argv[1] if len(sys.argv) > 1 else "系统提醒"
    message = sys.argv[2] if len(sys.argv) > 2 else "即将执行自动化任务。"
    timeout = sys.argv[3] if len(sys.argv) > 3 else "60"
    
    dialog = WarningDialog(title, message, timeout)
    dialog.show()
    
    # 捕获应用退出码并同步到系统退出码
    exit_code = app.exec_()
    sys.exit(exit_code)
