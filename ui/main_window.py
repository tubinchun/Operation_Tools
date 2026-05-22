#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTextEdit,
    QTableWidget, QTableWidgetItem, QGroupBox,
    QFormLayout, QMessageBox, QAction, QMenuBar,
    QMenu, QStatusBar, QToolBar, QComboBox,
    QLineEdit, QSpinBox, QCheckBox, QSplitter,
    QScrollArea, QProgressBar, QDialog, QListWidget,
    QListWidgetItem, QAbstractItemView, QTableView, QHeaderView,
    QGridLayout, QFrame, QSizePolicy, QFileDialog, QRadioButton
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QPointF, QRect
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPainter, QPainterPath, QLinearGradient, QPen, QBrush

from core.local_client import LocalClient

# ==================== 苹果风格UI样式定义 ====================

# 颜色常量
MAC_BLUE = "#007AFF"
MAC_GREEN = "#34C759"
MAC_RED = "#FF3B30"
MAC_ORANGE = "#FF9500"
MAC_PURPLE = "#AF52DE"
MAC_PINK = "#FF2D55"
MAC_CYAN = "#5AC8FA"
TEXT_PRIMARY = "#1C1C1E"
TEXT_SECONDARY = "#8E8E93"
TEXT_DISABLED = "#C7C7CC"
DIVIDER = "#EFEFF4"
BACKGROUND_MAIN = "#FFFFFF"
BACKGROUND_SECONDARY = "#F5F5F7"
BACKGROUND_HOVER = "#F0F0F2"
SIDE_BAR_BG = "#1C1C1E"
SIDE_BAR_ACTIVE = "#007AFF"
SIDE_BAR_TEXT = "#FFFFFF"
SIDE_BAR_TEXT_HOVER = "#B3B3B3"

# 字体常量
FONT_FAMILY = "SF Pro Display, PingFang SC, Microsoft YaHei, Arial"
FONT_SIZE_SMALL = 12
FONT_SIZE_NORMAL = 13
FONT_SIZE_MEDIUM = 14
FONT_SIZE_LARGE = 16
FONT_SIZE_XLARGE = 18

# 间距常量
SPACING_TINY = 4
SPACING_SMALL = 8
SPACING_MEDIUM = 16
SPACING_LARGE = 24
SPACING_XLARGE = 32

# 圆角常量
CORNER_BUTTON = 8
CORNER_CARD = 12
CORNER_DIALOG = 16

# 主按钮样式
PRIMARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {MAC_BLUE};
    color: white;
    border: none;
    border-radius: {CORNER_BUTTON}px;
    padding: 8px 24px;
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_NORMAL}px;
    font-weight: 500;
    min-height: 32px;
}}
QPushButton:hover {{
    background-color: #0066CC;
}}
QPushButton:pressed {{
    background-color: #0052AA;
}}
QPushButton:disabled {{
    background-color: {TEXT_DISABLED};
}}
"""

# 危险按钮样式
DANGER_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {MAC_RED};
    color: white;
    border: none;
    border-radius: {CORNER_BUTTON}px;
    padding: 8px 24px;
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_NORMAL}px;
    font-weight: 500;
    min-height: 32px;
}}
QPushButton:hover {{
    background-color: #CC0000;
}}
QPushButton:pressed {{
    background-color: #AA0000;
}}
QPushButton:disabled {{
    background-color: {TEXT_DISABLED};
}}
"""

# 次要按钮样式
SECONDARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: {MAC_BLUE};
    border: 1px solid {DIVIDER};
    border-radius: {CORNER_BUTTON}px;
    padding: 8px 24px;
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_NORMAL}px;
    font-weight: 500;
    min-height: 32px;
}}
QPushButton:hover {{
    background-color: {BACKGROUND_HOVER};
    border-color: {MAC_BLUE};
}}
QPushButton:pressed {{
    background-color: {BACKGROUND_SECONDARY};
}}
"""

LINE_EDIT_STYLE = f"""
QLineEdit {{
    background-color: {BACKGROUND_SECONDARY};
    border-radius: {CORNER_BUTTON}px;
    border: 1px solid {DIVIDER};
    padding: 8px 12px;
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_NORMAL}px;
    color: {TEXT_PRIMARY};
}}
QLineEdit:hover {{
    border-color: {MAC_BLUE};
}}
QLineEdit:focus {{
    border-color: {MAC_BLUE};
    background-color: {BACKGROUND_MAIN};
}}
QLineEdit:disabled {{
    background-color: {BACKGROUND_HOVER};
    color: {TEXT_DISABLED};
}}
"""

COMBO_BOX_STYLE = f"""
QComboBox {{
    background-color: {BACKGROUND_SECONDARY};
    border-radius: {CORNER_BUTTON}px;
    border: 1px solid {DIVIDER};
    padding: 8px 12px;
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_NORMAL}px;
    color: {TEXT_PRIMARY};
    min-height: 32px;
}}
QComboBox:hover {{
    border-color: {MAC_BLUE};
}}
QComboBox:focus {{
    border-color: {MAC_BLUE};
    background-color: {BACKGROUND_MAIN};
}}
QComboBox QAbstractItemView {{
    background-color: {BACKGROUND_MAIN};
    border: 1px solid {DIVIDER};
    border-radius: {CORNER_BUTTON}px;
    selection-background-color: {MAC_BLUE};
}}
"""

CHECKBOX_STYLE = f"""
QCheckBox {{
    color: {TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_NORMAL}px;
}}
QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 6px;
    border: 2px solid {DIVIDER};
    background-color: {BACKGROUND_MAIN};
}}
QCheckBox::indicator:checked {{
    background-color: {MAC_BLUE};
    border-color: {MAC_BLUE};
}}
QCheckBox::indicator:checked::unchecked {{
    background-color: {BACKGROUND_MAIN};
}}
"""

TAB_WIDGET_STYLE = f"""
QTabWidget::pane {{
    border: none;
    background-color: {BACKGROUND_SECONDARY};
}}
QTabBar::tab {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    padding: 12px 24px;
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_NORMAL}px;
    font-weight: 500;
    border-radius: {CORNER_BUTTON}px {CORNER_BUTTON}px 0 0;
    margin-right: 4px;
}}
QTabBar::tab:hover {{
    background-color: {BACKGROUND_HOVER};
    color: {TEXT_PRIMARY};
}}
QTabBar::tab:selected {{
    background-color: {BACKGROUND_MAIN};
    color: {MAC_BLUE};
}}
"""

# 文字按钮样式
TEXT_BUTTON_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_SMALL}px;
}}
QPushButton:hover {{
    color: {TEXT_PRIMARY};
    background-color: {BACKGROUND_HOVER};
}}
"""

# 卡片样式
CARD_STYLE = f"""
QFrame {{
    background-color: {BACKGROUND_MAIN};
    border-radius: {CORNER_CARD}px;
    border: 1px solid {DIVIDER};
}}
"""

# 窗口背景样式
WINDOW_STYLE = f"""
QMainWindow {{
    background-color: {BACKGROUND_SECONDARY};
}}
"""

# 工具卡片样式
TOOL_CARD_STYLE = f"""
QFrame {{
    background-color: {BACKGROUND_MAIN};
    border-radius: {CORNER_CARD}px;
    border: 1px solid {DIVIDER};
}}
QFrame:hover {{
    border-color: {MAC_BLUE};
    border-width: 2px;
}}
"""

def create_font(size=FONT_SIZE_NORMAL, weight="normal"):
    font = QFont(FONT_FAMILY, size)
    if weight == "bold":
        font.setWeight(QFont.Bold)
    elif weight == "medium":
        font.setWeight(QFont.Medium)
    elif weight == "semibold":
        font.setWeight(QFont.DemiBold)
    return font

def create_macos_palette():
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BACKGROUND_SECONDARY))
    palette.setColor(QPalette.WindowText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Button, QColor(BACKGROUND_MAIN))
    palette.setColor(QPalette.ButtonText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Highlight, QColor(MAC_BLUE))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Text, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Foreground, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.PlaceholderText, QColor(TEXT_DISABLED))
    return palette


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

        title = QLabel("麒麟运维百宝箱")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        version = QLabel("版本: 1.0.2")
        version.setAlignment(Qt.AlignCenter)

        desc = QLabel("适配: 银河麒麟桌面V10 SP1\n\n"
                     "功能: 系统信息监控、U盘工具箱、\n"
                     "     系统清理等")
        desc.setAlignment(Qt.AlignCenter)

        contact = QLabel("技术支持: linuxk8s@qq.com")
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

        painter.fillRect(self.rect(), QColor(240, 240, 240))

        pen = QPen(QColor(200, 200, 200))
        pen.setWidth(1)
        painter.setPen(pen)
        for i in range(1, 5):
            y = height * i / 5
            painter.drawLine(0, int(y), width, int(y))

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


class LineChartWidget(QWidget):
    """折线图组件，支持动态数据展示、悬停查看、平滑过渡"""
    def __init__(self, title="", color='#007aff', max_points=50, show_legend=True, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        self.max_points = max_points
        self.show_legend = show_legend
        self.values = []
        self.last_value = 0
        self.hover_point = None
        self.hover_value = None
        self.legend_height = 24 if show_legend and title else 0
        self.setMouseTracking(True)
        self.setFixedHeight(80 + self.legend_height)

    def add_value(self, value):
        """添加新数据点"""
        self.values.append(value)
        if len(self.values) > self.max_points:
            self.values = self.values[-self.max_points:]
        self.last_value = value
        self.update()

    def set_values(self, values):
        """设置数据点列表"""
        self.values = values[-self.max_points:]
        if self.values:
            self.last_value = self.values[-1]
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        
        if self.show_legend and self.title:
            legend_layout_y = 0
            
            color_dot = QRect(8, legend_layout_y + 8, 8, 8)
            painter.setBrush(QColor(self.color))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(color_dot, 4, 4)
            
            title_font = create_font(FONT_SIZE_SMALL)
            painter.setFont(title_font)
            painter.setPen(QColor(TEXT_SECONDARY))
            painter.drawText(QRect(20, legend_layout_y, 100, 24), Qt.AlignVCenter, self.title)
            
            value_font = create_font(FONT_SIZE_NORMAL, "semibold")
            painter.setFont(value_font)
            painter.setPen(QColor(self.color))
            value_text = f"{self.last_value}%"
            painter.drawText(QRect(0, legend_layout_y, rect.width() - 8, 24), 
                            Qt.AlignRight | Qt.AlignVCenter, value_text)
        
        chart_top = self.legend_height
        chart_rect = QRect(8, chart_top, rect.width() - 16, 80)
        
        painter.setBrush(QColor(BACKGROUND_SECONDARY))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(chart_rect, 8, 8)
        
        if not self.values:
            painter.end()
            return
        
        padding = 10
        inner_rect = chart_rect.adjusted(padding, padding, -padding, -padding)
        width = inner_rect.width()
        height = inner_rect.height()
        
        max_val = max(self.values) if self.values else 100
        min_val = min(self.values) if self.values else 0
        
        val_range = max_val - min_val
        if val_range < 5:
            min_val = max(0, min_val - 2)
            max_val = min(100, max_val + 2)
            val_range = max_val - min_val
        
        val_range = val_range if val_range > 0 else 1
        
        points = []
        num_points = len(self.values)
        step_x = width / (self.max_points - 1) if self.max_points > 1 else width
        
        for i, val in enumerate(self.values):
            x = inner_rect.left() + i * step_x
            normalized_val = (val - min_val) / val_range
            y = inner_rect.bottom() - normalized_val * height
            points.append(QPointF(x, y))
        
        if points:
            gradient = QLinearGradient(inner_rect.topLeft(), inner_rect.bottomLeft())
            gradient.setColorAt(0, QColor(self.color).lighter(110))
            gradient.setColorAt(1, QColor(self.color).lighter(180))
            
            path = QPainterPath()
            path.moveTo(points[0])
            
            if len(points) >= 3:
                for i in range(1, len(points)):
                    if i < len(points) - 1:
                        xc = (points[i].x() + points[i-1].x()) / 2
                        yc = (points[i].y() + points[i-1].y()) / 2
                        path.quadTo(points[i-1], QPointF(xc, yc))
                    else:
                        path.lineTo(points[i])
            else:
                for i in range(1, len(points)):
                    path.lineTo(points[i])
            
            path.lineTo(points[-1].x(), inner_rect.bottom())
            path.lineTo(points[0].x(), inner_rect.bottom())
            path.closeSubpath()
            
            painter.fillPath(path, gradient)
            
            pen = QPen(QColor(self.color), 2)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            
            if len(points) >= 3:
                smrooth_path = QPainterPath()
                smrooth_path.moveTo(points[0])
                for i in range(1, len(points)):
                    if i < len(points) - 1:
                        prev_point = points[i-1]
                        curr_point = points[i]
                        next_point = points[i+1]
                        
                        cpx1 = curr_point.x() - (next_point.x() - prev_point.x()) / 6
                        cpy1 = curr_point.y() - (next_point.y() - prev_point.y()) / 6
                        cpx2 = curr_point.x() + (next_point.x() - prev_point.x()) / 6
                        cpy2 = curr_point.y() + (next_point.y() - prev_point.y()) / 6
                        
                        smrooth_path.cubicTo(QPointF(cpx1, cpy1), QPointF(cpx2, cpy2), next_point)
                    else:
                        smrooth_path.lineTo(points[i])
                painter.drawPath(smrooth_path)
            else:
                for i in range(1, len(points)):
                    painter.drawLine(points[i-1], points[i])
            
            if self.hover_point is not None and 0 <= self.hover_point < len(self.values):
                point = points[self.hover_point]
                painter.setPen(QPen(QColor(self.color), 1, Qt.DashLine))
                painter.drawLine(point.x(), inner_rect.top(), point.x(), inner_rect.bottom())
                painter.drawLine(inner_rect.left(), point.y(), inner_rect.right(), point.y())
                
                tooltip_rect = QRect(point.x() + 8, point.y() - 25, 60, 20)
                tooltip_rect = tooltip_rect.normalized()
                if tooltip_rect.right() > inner_rect.right():
                    tooltip_rect.moveRight(inner_rect.right() - 8)
                
                painter.setBrush(QColor(self.color))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(tooltip_rect, 4, 4)
                
                painter.setPen(Qt.white)
                painter.setFont(create_font(FONT_SIZE_SMALL))
                painter.drawText(tooltip_rect, Qt.AlignCenter, f"{self.hover_value}%")
        
        painter.end()

    def mouseMoveEvent(self, event):
        rect = self.rect()
        chart_top = self.legend_height
        chart_rect = QRect(8, chart_top, rect.width() - 16, 80)
        padding = 10
        inner_rect = chart_rect.adjusted(padding, padding, -padding, -padding)
        
        pos = event.pos()
        
        if inner_rect.contains(pos):
            width = inner_rect.width()
            step_x = width / (self.max_points - 1) if self.max_points > 1 else width
            index = int((pos.x() - inner_rect.left()) / step_x)
            index = max(0, min(index, len(self.values) - 1))
            
            self.hover_point = index
            self.hover_value = self.values[index]
        else:
            self.hover_point = None
            self.hover_value = None
        
        self.update()

    def leaveEvent(self, event):
        self.hover_point = None
        self.hover_value = None
        self.update()


class ResourceItem(QWidget):
    """资源概览项组件"""
    def __init__(self, title, color='#007aff', show_chart=True, show_progress=True, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        self.show_chart = show_chart
        self.show_progress = show_progress
        self.values = []
        self.max_values = 50
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        self.title_label = QLabel(self.title)
        self.title_label.setFont(create_font(FONT_SIZE_NORMAL))
        self.title_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        header_layout.addWidget(self.title_label)
        
        self.value_label = QLabel("0%")
        self.value_label.setFont(create_font(FONT_SIZE_NORMAL))
        self.value_label.setStyleSheet(f"color: {self.color};")
        self.value_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(self.value_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)

        if self.show_progress:
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    height: 6px;
                    background-color: {BACKGROUND_SECONDARY};
                    border-radius: 3px;
                }}
                QProgressBar::chunk {{
                    background-color: {self.color};
                    border-radius: 3px;
                }}
            """)
            layout.addWidget(self.progress_bar)

        if self.show_chart:
            self.chart_area = QWidget()
            self.chart_area.setFixedHeight(40)
            self.chart_layout = QHBoxLayout(self.chart_area)
            self.chart_layout.setSpacing(1)
            self.chart_layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.chart_area)

        self.setLayout(layout)

    def update_value(self, value, text=None):
        if text:
            self.value_label.setText(text)
        else:
            self.value_label.setText(f"{value}%")
        
        if self.show_progress:
            self.progress_bar.setValue(min(value, 100))
        
        if self.show_chart:
            self.values.append(value)
            if len(self.values) > self.max_values:
                self.values = self.values[-self.max_values:]
            
            for i in reversed(range(self.chart_layout.count())):
                self.chart_layout.itemAt(i).widget().deleteLater()
            
            max_val = max(self.values) if self.values else 1
            for val in self.values:
                bar = QWidget()
                height = int((val / max_val) * 40) if max_val > 0 else 4
                bar.setFixedHeight(max(height, 4))
                bar.setFixedWidth(2)
                bar.setStyleSheet(f"background-color: {self.color}; border-radius: 1px;")
                self.chart_layout.addWidget(bar, alignment=Qt.AlignBottom)


class SystemStatusPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self._threads = []
        self._is_destroyed = False
        self.init_ui()
        self.load_status()
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(2000)
        self.last_net_io = None

    def cleanup(self):
        """清理资源，停止线程和定时器"""
        self._is_destroyed = True
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()
        for thread in self._threads:
            if thread.isRunning():
                thread.stop()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(16)

        left_panel = QWidget()
        left_panel.setMaximumWidth(320)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(16)

        self.cpu_chart = LineChartWidget("CPU", color='#007aff')
        left_layout.addWidget(self.cpu_chart)

        self.mem_chart = LineChartWidget("内存", color='#34c759')
        left_layout.addWidget(self.mem_chart)

        swap_group = QWidget()
        swap_layout = QVBoxLayout(swap_group)
        swap_layout.setSpacing(6)
        
        swap_header = QHBoxLayout()
        swap_header.setSpacing(8)
        swap_title = QLabel("交换空间")
        swap_title.setFont(create_font(FONT_SIZE_NORMAL))
        swap_title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        swap_header.addWidget(swap_title)
        swap_header.addStretch()
        self.swap_label = QLabel("0GB/0GB")
        self.swap_label.setFont(create_font(FONT_SIZE_NORMAL))
        self.swap_label.setStyleSheet(f"color: {MAC_GREEN};")
        swap_header.addWidget(self.swap_label)
        swap_layout.addLayout(swap_header)
        
        self.swap_progress = QProgressBar()
        self.swap_progress.setRange(0, 100)
        self.swap_progress.setValue(0)
        self.swap_progress.setTextVisible(False)
        self.swap_progress.setStyleSheet(f"""
            QProgressBar {{
                height: 6px;
                background-color: {BACKGROUND_SECONDARY};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {MAC_GREEN};
                border-radius: 3px;
            }}
        """)
        swap_layout.addWidget(self.swap_progress)
        left_layout.addWidget(swap_group)

        net_group = QWidget()
        net_layout = QVBoxLayout(net_group)
        net_layout.setSpacing(12)

        net_header = QLabel("网络流量")
        net_header.setFont(create_font(FONT_SIZE_NORMAL))
        net_header.setStyleSheet(f"color: {TEXT_PRIMARY};")
        net_layout.addWidget(net_header)

        speed_layout = QHBoxLayout()
        speed_layout.setSpacing(16)
        
        recv_layout = QVBoxLayout()
        recv_layout.setSpacing(2)
        recv_title = QLabel("接收")
        recv_title.setFont(create_font(FONT_SIZE_SMALL))
        recv_title.setStyleSheet(f"color: {TEXT_SECONDARY};")
        recv_layout.addWidget(recv_title)
        self.recv_label = QLabel("0.0 KB/s")
        self.recv_label.setFont(create_font(FONT_SIZE_NORMAL, "semibold"))
        self.recv_label.setStyleSheet("color: #af52de;")
        recv_layout.addWidget(self.recv_label)
        speed_layout.addLayout(recv_layout)
        
        send_layout = QVBoxLayout()
        send_layout.setSpacing(2)
        send_title = QLabel("发送")
        send_title.setFont(create_font(FONT_SIZE_SMALL))
        send_title.setStyleSheet(f"color: {TEXT_SECONDARY};")
        send_layout.addWidget(send_title)
        self.send_label = QLabel("0.0 KB/s")
        self.send_label.setFont(create_font(FONT_SIZE_NORMAL, "semibold"))
        self.send_label.setStyleSheet("color: #ff3b30;")
        send_layout.addWidget(self.send_label)
        speed_layout.addLayout(send_layout)
        
        speed_layout.addStretch()
        net_layout.addLayout(speed_layout)

        self.net_chart = LineChartWidget("", color='#af52de', show_legend=False)
        self.net_chart.setObjectName("netChart")
        net_layout.addWidget(self.net_chart)

        left_layout.addWidget(net_group)

        left_layout.addStretch()
        left_panel.setLayout(left_layout)

        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(16)

        right_header = QHBoxLayout()
        right_header.setSpacing(12)

        process_label = QLabel("进程管理")
        process_label.setFont(create_font(FONT_SIZE_LARGE, "semibold"))
        process_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        right_header.addWidget(process_label)
        right_header.addStretch()
        right_layout.addLayout(right_header)

        self.process_tabs = QTabWidget()
        self.process_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {DIVIDER};
                border-radius: {CORNER_CARD}px;
                background-color: {BACKGROUND_MAIN};
            }}
            QTabBar::tab {{
                padding: 8px 16px;
                margin-right: 4px;
                border-radius: {CORNER_BUTTON}px;
                background-color: {BACKGROUND_SECONDARY};
                color: {TEXT_SECONDARY};
            }}
            QTabBar::tab:selected {{
                background-color: {MAC_BLUE};
                color: white;
            }}
        """)

        self.current_user_tab = QWidget()
        current_user_layout = QVBoxLayout()
        self.current_user_table = self.create_process_table()
        current_user_layout.addWidget(self.current_user_table)
        self.current_user_tab.setLayout(current_user_layout)
        self.process_tabs.addTab(self.current_user_tab, "当前用户进程(0)")

        self.all_proc_tab = QWidget()
        all_proc_layout = QVBoxLayout()
        self.all_proc_table = self.create_process_table()
        all_proc_layout.addWidget(self.all_proc_table)
        self.all_proc_tab.setLayout(all_proc_layout)
        self.process_tabs.addTab(self.all_proc_tab, "全部进程(0)")

        right_layout.addWidget(self.process_tabs)

        right_panel.setLayout(right_layout)

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 3)

        self.setLayout(main_layout)

    def create_process_table(self):
        """创建进程表格"""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(['进程名称', 'PID', '用户', 'CPU', '内存', '操作'])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        table.horizontalHeader().setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {BACKGROUND_SECONDARY};
                color: {TEXT_PRIMARY};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {DIVIDER};
                font-weight: 500;
            }}
        """)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BACKGROUND_MAIN};
                border: none;
                gridline-color: {DIVIDER};
            }}
            QTableWidget::item {{
                padding: 8px;
                border: none;
                color: {TEXT_PRIMARY};
            }}
            QTableWidget::item:selected {{
                background-color: {MAC_BLUE}30;
            }}
        """)
        return table

    def refresh_data(self):
        """定时刷新数据"""
        self.load_status()

    def load_status(self):
        def fetch_all():
            cpu_info = self.client.get_cpu_info()
            mem_info = self.client.get_memory_info()
            all_proc_info = self.client.get_process_list(50)
            current_user_proc_info = self.client.get_process_list_by_user(
                self.get_current_username(), 50
            )
            net_info = self.client.get_network_info()
            return {
                'cpu': cpu_info,
                'mem': mem_info,
                'all_proc': all_proc_info,
                'current_user_proc': current_user_proc_info,
                'net': net_info
            }

        def on_result(result):
            if self._is_destroyed:
                return
            cpu_result = result.get('cpu', {})
            if cpu_result.get('status') == 'success':
                cpu_data = cpu_result.get('data', {})
                cpu_percent = cpu_data.get('usage_percent', 0)
                self.cpu_chart.add_value(int(cpu_percent))

            mem_result = result.get('mem', {})
            if mem_result.get('status') == 'success':
                mem_data = mem_result.get('data', {})
                mem_percent = mem_data.get('percent', 0)
                self.mem_chart.add_value(int(mem_percent))

                swap_total = mem_data.get('swap_total', 0)
                swap_used = mem_data.get('swap_used', 0)
                if swap_total > 0:
                    swap_percent = (swap_used / swap_total) * 100
                    swap_total_gb = swap_total / (1024**3)
                    swap_used_gb = swap_used / (1024**3)
                    self.swap_progress.setValue(int(swap_percent))
                    self.swap_label.setText(f"{swap_used_gb:.1f}GB/{swap_total_gb:.1f}GB")
                else:
                    self.swap_progress.setValue(0)
                    self.swap_label.setText("0GB/0GB")

            net_result = result.get('net', {})
            if net_result.get('status') == 'success':
                net_data = net_result.get('data', {})
                bytes_recv = net_data.get('bytes_recv', 0)
                bytes_sent = net_data.get('bytes_sent', 0)

                if self.last_net_io:
                    recv_speed = (bytes_recv - self.last_net_io['recv']) / 2
                    send_speed = (bytes_sent - self.last_net_io['sent']) / 2
                    self.recv_label.setText(f"{self.format_speed(recv_speed)}")
                    self.send_label.setText(f"{self.format_speed(send_speed)}")
                    
                    net_percent = min(int(((recv_speed + send_speed) / 1024) * 10), 100)
                    self.net_chart.add_value(net_percent)

                self.last_net_io = {'recv': bytes_recv, 'sent': bytes_sent}

            all_proc_result = result.get('all_proc', {})
            if all_proc_result.get('status') == 'success':
                all_processes = all_proc_result.get('data', {}).get('processes', [])
                self.process_tabs.setTabText(1, f"全部进程({len(all_processes)})")
                self.fill_table(self.all_proc_table, all_processes)

            current_user_proc_result = result.get('current_user_proc', {})
            if current_user_proc_result.get('status') == 'success':
                current_user_processes = current_user_proc_result.get('data', {}).get('processes', [])
                self.process_tabs.setTabText(0, f"当前用户进程({len(current_user_processes)})")
                self.fill_table(self.current_user_table, current_user_processes)

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

    def get_current_username(self):
        """获取当前登录用户名"""
        try:
            import getpass
            return getpass.getuser()
        except:
            return 'rroot'

    def fill_table(self, table, processes):
        """填充进程表格"""
        table.setRowCount(len(processes))
        for i, proc in enumerate(processes):
            name = proc.get('name', 'Unknown')
            table.setItem(i, 0, QTableWidgetItem(name))

            pid = proc.get('pid', 0)
            pid_item = QTableWidgetItem(str(pid))
            pid_item.setData(Qt.UserRole, pid)
            table.setItem(i, 1, pid_item)

            username = proc.get('username', 'unknown')
            table.setItem(i, 2, QTableWidgetItem(str(username)))

            cpu = proc.get('cpu_percent', 0)
            table.setItem(i, 3, QTableWidgetItem(f"{cpu:.1f}%"))

            mem_mb = proc.get('memory_rss_mb', 0)
            table.setItem(i, 4, QTableWidgetItem(f"{mem_mb:.1f}MB"))

            kill_btn = QPushButton("结束")
            kill_btn.setStyleSheet(DANGER_BUTTON_STYLE)
            kill_btn.clicked.connect(lambda checked, p=pid, n=name: self.kill_process(p, n))
            table.setCellWidget(i, 5, kill_btn)

    def kill_process(self, pid, name):
        """结束进程"""
        dialog = QMessageBox.question(
            self,
            "确认结束进程",
            f"确定要结束进程 '{name}' (PID: {pid}) 吗？\n\n"
            "选择操作方式：\n"
            "• 是: 仅结束当前进程\n"
            "• 全部: 结束所有同名进程",
            QMessageBox.Yes | QMessageBox.YesToAll | QMessageBox.No,
            QMessageBox.No
        )
        
        if dialog == QMessageBox.Yes:
            self._kill_process_async(pid, name, "single")
        elif dialog == QMessageBox.YesToAll:
            self._kill_process_async(pid, name, "all")

    def _kill_process_async(self, pid, name, mode="single"):
        """异步结束进程"""
        def execute_kill():
            if mode == "all":
                result = self.client.kill_process_by_name(name)
                return {'result': result, 'pid': None, 'name': name, 'mode': mode}
            else:
                result = self.client.kill_process(pid)
                return {'result': result, 'pid': pid, 'name': name, 'mode': mode}

        def on_result(data):
            if self._is_destroyed:
                return
            result = data.get('result', {})
            pid = data.get('pid')
            name = data.get('name')
            mode = data.get('mode', 'single')
            
            if result.get('status') == 'success':
                if mode == "all":
                    QMessageBox.information(
                        self,
                        "操作成功",
                        f"所有名为 '{name}' 的进程已成功结束。"
                    )
                else:
                    QMessageBox.information(
                        self,
                        "操作成功",
                        f"进程 '{name}' (PID: {pid}) 已成功结束。"
                    )
                self.load_status()
            else:
                error_msg = result.get('message', '未知错误')
                if mode == "all":
                    QMessageBox.warning(
                        self,
                        "操作失败",
                        f"无法结束所有名为 '{name}' 的进程\n\n错误信息: {error_msg}"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "操作失败",
                        f"无法结束进程 '{name}' (PID: {pid})\n\n错误信息: {error_msg}"
                    )

        thread = WorkerThread(execute_kill)
        thread.finished.connect(on_result)
        thread.start()
        self._threads.append(thread)


class UserManagementPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self._threads = []
        self._is_destroyed = False
        self.init_ui()
        self.load_users()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM)
        main_layout.setSpacing(SPACING_MEDIUM)

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header_icon = QLabel()
        header_icon.setPixmap(QIcon.fromTheme("system-users").pixmap(24, 24))
        header_layout.addWidget(header_icon)
        
        header = QLabel("用户管理")
        header.setFont(create_font(FONT_SIZE_LARGE, "semibold"))
        header.setStyleSheet(f"color: {TEXT_PRIMARY};")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        main_layout.addWidget(header_widget)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(SPACING_MEDIUM)

        user_list_card = QFrame()
        user_list_card.setStyleSheet(CARD_STYLE)
        user_list_layout = QVBoxLayout(user_list_card)
        user_list_layout.setContentsMargins(SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM)
        user_list_layout.setSpacing(SPACING_SMALL)

        list_header = QLabel("用户列表")
        list_header.setFont(create_font(FONT_SIZE_NORMAL, "medium"))
        list_header.setStyleSheet(f"color: {TEXT_SECONDARY};")
        user_list_layout.addWidget(list_header)

        self.user_list = QListWidget()
        self.user_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.user_list.itemClicked.connect(self.on_user_selected)
        self.user_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {BACKGROUND_SECONDARY};
                border-radius: {CORNER_BUTTON}px;
                border: none;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {DIVIDER};
            }}
            QListWidget::item:hover {{
                background-color: {BACKGROUND_HOVER};
            }}
            QListWidget::item:selected {{
                background-color: {MAC_BLUE};
                color: white;
            }}
        """)
        user_list_layout.addWidget(self.user_list)
        content_layout.addWidget(user_list_card, stretch=1)

        right_panel = QFrame()
        right_panel.setStyleSheet(CARD_STYLE)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.detail_tabs = QTabWidget()
        self.detail_tabs.setStyleSheet(TAB_WIDGET_STYLE)
        self.detail_tabs.setTabPosition(QTabWidget.North)

        user_info_tab = QWidget()
        user_info_layout = QVBoxLayout(user_info_tab)
        user_info_layout.setContentsMargins(SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM)
        user_info_layout.setSpacing(SPACING_MEDIUM)

        self.user_info_text = QTextEdit()
        self.user_info_text.setReadOnly(True)
        self.user_info_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BACKGROUND_SECONDARY};
                border-radius: {CORNER_BUTTON}px;
                border: none;
                padding: 12px;
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_NORMAL}px;
                color: {TEXT_PRIMARY};
            }}
        """)
        self.user_info_text.setPlaceholderText("请从左侧选择用户查看详情")
        user_info_layout.addWidget(self.user_info_text, stretch=1)
        self.detail_tabs.addTab(user_info_tab, "用户详情")

        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        history_layout.setContentsMargins(SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM)
        history_layout.setSpacing(SPACING_MEDIUM)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["用户", "终端", "来源IP", "登录时间"])
        self.history_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BACKGROUND_SECONDARY};
                border-radius: {CORNER_BUTTON}px;
                border: none;
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_SMALL}px;
            }}
            QHeaderView::section {{
                background-color: {BACKGROUND_MAIN};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {DIVIDER};
                font-weight: 500;
                color: {TEXT_SECONDARY};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {DIVIDER};
            }}
            QTableWidget::item:selected {{
                background-color: {MAC_BLUE};
                color: white;
            }}
        """)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        history_layout.addWidget(self.history_table, stretch=1)
        
        history_btn = QPushButton()
        history_btn.setIcon(QIcon.fromTheme("view-refresh"))
        history_btn.setText("刷新登录历史")
        history_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        history_btn.clicked.connect(self.load_history)
        history_layout.addWidget(history_btn)
        
        self.detail_tabs.addTab(history_tab, "登录历史")

        right_layout.addWidget(self.detail_tabs)
        content_layout.addWidget(right_panel, stretch=2)

        main_layout.addLayout(content_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        refresh_btn = QPushButton()
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.setText("刷新用户")
        refresh_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        refresh_btn.clicked.connect(self.load_users)
        btn_layout.addWidget(refresh_btn)
        
        history_btn = QPushButton()
        history_btn.setIcon(QIcon.fromTheme("document-open"))
        history_btn.setText("登录历史")
        history_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        history_btn.clicked.connect(self.load_history)
        btn_layout.addWidget(history_btn)
        
        reset_btn = QPushButton()
        reset_btn.setIcon(QIcon.fromTheme("lock"))
        reset_btn.setText("重置密码")
        reset_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        reset_btn.clicked.connect(self.show_reset_password_dialog)
        btn_layout.addWidget(reset_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def show_reset_password_dialog(self):
        selected_items = self.user_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警", "请先选择一个用户")
            return
        
        username = selected_items[0].text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"重置 {username} 的密码")
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM)
        layout.setSpacing(SPACING_MEDIUM)
        
        password_label = QLabel("新密码:")
        password_label.setFont(create_font(FONT_SIZE_NORMAL))
        password_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("请输入新密码")
        self.password_input.setStyleSheet(LINE_EDIT_STYLE)
        layout.addWidget(self.password_input)
        
        confirm_label = QLabel("确认密码:")
        confirm_label.setFont(create_font(FONT_SIZE_NORMAL))
        confirm_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(confirm_label)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setPlaceholderText("请再次输入密码")
        self.confirm_input.setStyleSheet(LINE_EDIT_STYLE)
        layout.addWidget(self.confirm_input)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        ok_btn.clicked.connect(lambda: self.reset_password(username, dialog))
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec_()

    def reset_password(self, username, dialog):
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        if not password:
            QMessageBox.warning(self, "警", "请输入密码")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "警", "两次输入的密码不一致")
            return
        
        def fetch():
            return self.client.reset_user_password(username, password)
        
        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                QMessageBox.information(self, "成功", result.get('message', '密码重置成功'))
                dialog.accept()
            else:
                QMessageBox.error(self, "错误", result.get('message', '密码重置失败'))
        
        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def load_users(self):
        for t in self._threads:
            t.stop()
        self._threads = []
        
        def fetch():
            return self.client.get_users()

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                users = result.get('data', {}).get('users_raw', '')
                self.user_list.clear()
                for line in users.split('\n'):
                    if ':' in line:
                        username = line.split(':')[0]
                        self.user_list.addItem(username)

        self.thread = WorkerThread(fetch)
        self._threads.append(self.thread)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def load_history(self, username=None):
        def fetch():
            return self.client.get_login_history(username)

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                history = result.get('data', {}).get('login_history', '')
                self.parse_and_display_history(history, username)

        self.thread = WorkerThread(fetch)
        self._threads.append(self.thread)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def parse_and_display_history(self, history_text, username=None):
        self.history_table.setRowCount(0)
        
        if not history_text:
            return
        
        lines = history_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('wtmp') or line.startswith('---'):
                continue
            
            parts = line.split()
            if len(parts) >= 8:
                login_user = parts[0]
                
                if username and login_user != username:
                    continue
                
                terminal = parts[1]
                ip = parts[2] if parts[2] != '0' else '-'
                
                date_parts = parts[3:8]
                login_time = ' '.join(date_parts)
                
                row = self.history_table.rowCount()
                self.history_table.insertRow(row)
                self.history_table.setItem(row, 0, QTableWidgetItem(login_user))
                self.history_table.setItem(row, 1, QTableWidgetItem(terminal))
                self.history_table.setItem(row, 2, QTableWidgetItem(ip))
                self.history_table.setItem(row, 3, QTableWidgetItem(login_time))
        
        self.history_table.resizeColumnsToContents()

    def on_user_selected(self, item):
        username = item.text()
        
        def fetch():
            return self.client.get_user_info(username)
        
        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                data = result.get('data', {})
                info_text = f"用户名: {data.get('username', '未知')}\n\n"
                info_text += f"用户ID (UID): {data.get('uid', '未知')}\n\n"
                info_text += f"组ID (GID): {data.get('gid', '未知')}\n\n"
                info_text += f"家目录: {data.get('home', '未知')}\n\n"
                info_text += f"登录Shell: {data.get('shell', '未知')}\n\n"
                info_text += f"用户类型: {data.get('user_type', '未知')}\n\n"
                info_text += f"密码状态: {data.get('password_status', '未知')}\n\n"
                info_text += f"所属组: {data.get('groups', '未知')}"
                self.user_info_text.setPlainText(info_text)
            else:
                self.user_info_text.setPlainText(f"获取用户信息失败: {result.get('message', '未知错误')}")
        
        self.thread = WorkerThread(fetch)
        self._threads.append(self.thread)
        self.thread.finished.connect(on_result)
        self.thread.start()
        
        self.load_history(username)

    def cleanup(self):
        for t in self._threads:
            t.stop()
        self._threads = []


class NetworkPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self._is_destroyed = False
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
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                self.network_text.setPlainText(result.get('data', {}).get('network', ''))

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def restart_network(self):
        def fetch():
            return self.client.restart_network()

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                QMessageBox.information(self, "成功", "网络服务已重启")
                self.load_network_info()
            else:
                QMessageBox.warning(self, "失败", result.get('message', '操作失败'))

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()


class SoftwarePage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self._is_destroyed = False
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
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                self.sources_text.setPlainText(result.get('data', {}).get('sources', ''))

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def load_packages(self):
        def fetch():
            return self.client.get_installed_packages()

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                self.packages_text.setPlainText(result.get('data', {}).get('packages', ''))

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def export_packages(self):
        content = self.packages_text.toPlainText()
        if content:
            QMessageBox.information(self, "导出", f"软件包清单包含 {len(content)} 字符")





class HostsEditorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("自定义本地域名解析文件")
        self.setMinimumSize(600, 400)
        self.resize(700, 500)
        self.setStyleSheet(f"background-color: {BACKGROUND_MAIN};")
        
        self.hosts_path = '/etc/hosts'
        self.original_content = ""
        self.backup_content = ""
        self.history = []
        self.force_restore = False
        
        self.init_ui()
        self.load_hosts_file()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        header = QLabel("自定义本地域名解析文件")
        header.setFont(create_font(FONT_SIZE_LARGE, "semibold"))
        header.setStyleSheet(f"color: {TEXT_PRIMARY};")
        main_layout.addWidget(header)

        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Consolas", 11))
        self.text_edit.setLineWrapMode(QTextEdit.NoWrap)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BACKGROUND_SECONDARY};
                border: 1px solid {DIVIDER};
                border-radius: {CORNER_BUTTON}px;
                padding: 12px;
                color: {TEXT_PRIMARY};
            }}
            QTextEdit QScrollBar {{
                width: 12px;
                height: 12px;
            }}
            QTextEdit QScrollBar::handle {{
                background-color: {TEXT_DISABLED};
                border-radius: 6px;
            }}
            QTextEdit QScrollBar::handle:hover {{
                background-color: {TEXT_SECONDARY};
            }}
        """)
        main_layout.addWidget(self.text_edit, stretch=1)

        self.status_label = QLabel("")
        self.status_label.setFont(create_font(FONT_SIZE_SMALL))
        self.status_label.setStyleSheet(f"color: {MAC_GREEN};")
        main_layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        restore_btn = QPushButton("恢复默认")
        restore_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        restore_btn.clicked.connect(self.restore_default)
        btn_layout.addWidget(restore_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        save_btn.clicked.connect(self.save_hosts)
        btn_layout.addWidget(save_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def load_hosts_file(self):
        try:
            with open(self.hosts_path, 'r') as f:
                self.original_content = f.read()
                self.backup_content = self.original_content
                self.text_edit.setPlainText(self.original_content)
                self.status_label.setText("已加载 hosts 文件")
        except Exception as e:
            QMessageBox.warning(self, "警", f"无法读取 hosts 文件: {str(e)}")
            self.text_edit.setPlainText("# hosts file\n127.0.0.1 localhost")

    def restore_default(self):
        default_content = """127.0.0.1	localhost

127.0.1.1	kylin-pc

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters"""
        self.text_edit.setPlainText(default_content)
        self.force_restore = True
        self.status_label.setText("已恢复到默认内容（可点击保直）")

    def save_hosts(self):
        new_content = self.text_edit.toPlainText()
        
        if new_content == self.backup_content and not self.force_restore:
            QMessageBox.information(self, "提示", "内容未发生变化")
            return

        try:
            from core.auth_service import AuthService
            auth_service = AuthService()
            
            result = auth_service.execute(['cp', self.hosts_path, f'{self.hosts_path}.bak'])
            if not result.get('success'):
                QMessageBox.warning(self, "警告", "无法创建备份文件")
            
            result = auth_service.execute(['bash', '-c', f'cat > {self.hosts_path} << "EOF"\n{new_content}\nEOF'])
            
            if result.get('success'):
                self.history.append(self.backup_content)
                self.backup_content = new_content
                self.force_restore = False
                self.status_label.setText("保存成功")
                QMessageBox.information(self, "成功", "hosts 文件已更新")
                self.accept()
            else:
                error_msg = result.get('error', result.get('stderr', "保存失败"))
                QMessageBox.error(self, "错误", f"保存失败: {error_msg}")
                
        except Exception as e:
            QMessageBox.error(self, "错误", f"保存失败: {str(e)}")


class InfoCard(QFrame):
    def __init__(self, title, icon_name, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BACKGROUND_SECONDARY};
                border-radius: 12px;
                border: none;
            }}
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(16)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        icon_label = QLabel()
        icon_label.setPixmap(QIcon.fromTheme(icon_name).pixmap(22, 22))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setFont(create_font(FONT_SIZE_NORMAL, "semibold"))
        title_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        self.layout.addLayout(header_layout)
        
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(10)
        self.layout.addLayout(self.content_layout)
    
    def add_info_row(self, label_text, value_text, highlight=False):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)
        
        label = QLabel(label_text)
        label.setFont(create_font(FONT_SIZE_SMALL))
        label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        label.setFixedWidth(100)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row_layout.addWidget(label)
        
        value = QLabel(value_text)
        value.setFont(create_font(FONT_SIZE_SMALL))
        value.setStyleSheet(f"color: {MAC_GREEN if highlight else TEXT_PRIMARY};")
        value.setWordWrap(True)
        value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        row_layout.addWidget(value, stretch=1)
        
        self.content_layout.addWidget(row_widget)


class SystemInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统信息查看")
        self.setMinimumSize(900, 700)
        self.resize(900, 700)
        self.setStyleSheet(f"background-color: {BACKGROUND_MAIN};")
        self.client = LocalClient()
        self._is_destroyed = False
        self.init_ui()
        self.load_system_info()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header_icon = QLabel()
        header_icon.setPixmap(QIcon.fromTheme("computer").pixmap(36, 36))
        header_layout.addWidget(header_icon)
        
        header_label = QLabel("系统信息")
        header_label.setFont(create_font(FONT_SIZE_LARGE, "semibold"))
        header_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_btn.setText("刷新")
        self.refresh_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self.refresh_btn.clicked.connect(self.load_system_info)
        header_layout.addWidget(self.refresh_btn)
        
        main_layout.addWidget(header_widget)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll_content = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(16)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area, stretch=1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        copy_btn = QPushButton()
        copy_btn.setIcon(QIcon.fromTheme("edit-copy"))
        copy_btn.setText("复制信息")
        copy_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        copy_btn.clicked.connect(self.copy_info)
        btn_layout.addWidget(copy_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

        self.hardware_card = InfoCard("硬件信息", "hardware")
        self.software_card = InfoCard("软件信息", "software")
        self.storage_card = InfoCard("直储信息", "harddisk")
        self.network_card = InfoCard("网络信息", "network")
        
        self.scroll_layout.addWidget(self.hardware_card, 0, 0)
        self.scroll_layout.addWidget(self.software_card, 0, 1)
        self.scroll_layout.addWidget(self.storage_card, 1, 0)
        self.scroll_layout.addWidget(self.network_card, 1, 1)
        
        self.scroll_layout.setColumnStretch(0, 1)
        self.scroll_layout.setColumnStretch(1, 1)
        
        self.raw_output = ""

    def parse_system_info(self, output):
        import re
        
        def remove_ansi_escape_sequences(text):
            # 处理 ANSI 转义序列
            ansi_escape = re.compile(r'(?:\x1B|\033)\[(?:\d+;)*\d*[a-zA-Z]')
            text = ansi_escape.sub('', text)
            # 处理其他控制字符（除了换行和制表符）
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
            # 移除回车符
            text = text.replace('\r', '')
            return text
        
        # 清理ANSI转义序列，但保留原始空格格式
        output = remove_ansi_escape_sequences(output)
        
        # 调试输出，保留原始输出的副本
        self.raw_output = output
        
        info = {
            'system_model': 'Unknown',
            'serial_number': 'Unknown',
            'cpu_model': 'Unknown',
            'cpu_cores': 'Unknown',
            'cpu_usage': 'Unknown',
            'memory_total': 'Unknown',
            'memory_free': 'Unknown',
            'gpu': 'Unknown',
            'disk_size': 'Unknown',
            'disk_free': 'Unknown',
            'disks': [],
            'network': [],
            'system_id': 'Unknown',
            'kylin_serial': 'Unknown',
            'service_status': 'Unknown',
            'kernel': 'Unknown',
            'install_time': 'Unknown',
            'build_id': 'Unknown',
            'hwid': 'Unknown',
            'register_code': 'Unknown',
            'activation': 'Unknown'
        }
        
        # 用于检测是否进入了磁盘信息区域
        in_disk_section = False
        
        for line in output.split('\n'):
            original_line = line
            line = line.strip()
            
            if not line:
                continue
            
            # 检测是否进入磁盘信息区域
            if '磁盘名称' in line and '磁盘大小' in line:
                in_disk_section = True
                continue
            
            # 检测是否离开磁盘信息区域（分隔线之后的内容）
            if in_disk_section and ('-------------------------' in line or '软件信息' in line):
                in_disk_section = False
                continue
            
            # 主机型号和序列号在同一行（处理各种格式）
            if '主机型号' in original_line:
                # 使用原始行进行解析，避免strip()导致问题
                cleaned_line = re.sub(r'^\s*\d+、', '', original_line)
                
                # 查找主机型号开始位置
                model_key = '主机型号：'
                model_start = cleaned_line.find(model_key)
                if model_start >= 0:
                    model_start += len(model_key)
                    sn_key = '主机SN码：'
                    sn_pos = cleaned_line.find(sn_key)
                    if sn_pos > model_start:
                        info['system_model'] = cleaned_line[model_start:sn_pos].strip()
                        sn_start = sn_pos + len(sn_key)
                        serial = cleaned_line[sn_start:].strip()
                        serial = ' '.join(serial.split())
                        info['serial_number'] = serial
                    else:
                        info['system_model'] = cleaned_line[model_start:].strip()
            
            # 单独处理主机SN码行（如果在不同行）
            if '主机SN码' in original_line and '主机型号' not in original_line:
                cleaned_line = re.sub(r'^\s*\d+、', '', original_line)
                sn_key = '主机SN码：'
                sn_start = cleaned_line.find(sn_key)
                if sn_start >= 0:
                    sn_start += len(sn_key)
                    serial = cleaned_line[sn_start:].strip()
                    serial = ' '.join(serial.split())
                    info['serial_number'] = serial
            
            if 'CPU型号' in original_line:
                line_content = re.sub(r'^\s*\d+、', '', original_line)
                cpu_start = line_content.find('CPU型号【')
                if cpu_start >= 0:
                    cpu_start += 5
                    remaining = line_content[cpu_start:]
                    first_bracket = remaining.find('】')
                    if first_bracket > 0:
                        info['cpu_cores'] = remaining[:first_bracket].strip()
                        remaining = remaining[first_bracket+1:]
                        usage_start = remaining.find('【')
                        if usage_start > 0:
                            usage_end = remaining.find('】', usage_start)
                            if usage_end > usage_start:
                                info['cpu_usage'] = remaining[usage_start+1:usage_end].strip()
                                if usage_end + 1 < len(remaining):
                                    info['cpu_model'] = remaining[usage_end+1:].strip()
                        else:
                            info['cpu_model'] = remaining.strip()
            
            if '总内存/空闲内存' in original_line:
                line_content = re.sub(r'^\s*\d+、', '', original_line)
                parts = line_content.split(':')
                if len(parts) > 1:
                    mem_info = parts[1].strip()
                    mem_parts = mem_info.split('/')
                    if len(mem_parts) >= 2:
                        info['memory_total'] = mem_parts[0].strip()
                        info['memory_free'] = mem_parts[1].strip()
            
            if '显卡：' in original_line:
                line_content = re.sub(r'^\s*\d+、', '', original_line)
                parts = line_content.split('显卡：')
                if len(parts) > 1:
                    info['gpu'] = parts[1].strip()
            
            if '系统根目录空间' in original_line:
                line_content = re.sub(r'^\s*\d+、', '', original_line)
                parts = line_content.split('：')
                if len(parts) > 2:
                    info['disk_size'] = parts[1].strip()
                    info['disk_free'] = parts[2].strip()
            
            # 在磁盘信息区域内处理磁盘
            if in_disk_section:
                # 更全面地匹配磁盘设备，包括sd、nvme、sr等
                if (line.startswith('sd') or line.startswith('nvme') or 
                    line.startswith('sr') or line.startswith('mmcblk') or
                    line.startswith('hd')):
                    parts = line.split()
                    if len(parts) >= 2:
                        disk_name = parts[0]
                        disk_size = parts[1]
                        disk_sn = parts[2] if len(parts) > 2 else 'Unknown'
                        info['disks'].append({'name': disk_name, 'size': disk_size, 'sn': disk_sn})
            
            if '网卡(' in line:
                # 使用正则表达式提取网卡名称和MAC地址
                import re
                match = re.search(r'网卡\(([^)]+)\):\s*([0-9a-fA-F:]+)', line)
                if match:
                    name = match.group(1).strip()
                    mac = match.group(2).strip()
                    info['network'].append({'name': name, 'mac': mac})
                else:
                    # 备用解析方法
                    parts = line.split(':')
                    if len(parts) > 1:
                        name = parts[0].replace('网卡(', '').replace(')', '').strip()
                        # 合并剩余部分作为MAC地址
                        mac = ':'.join(parts[1:]).strip()
                        info['network'].append({'name': name, 'mac': mac})
            
            if '系统服务序列号' in line:
                parts = line.split('：')
                if len(parts) > 1:
                    serial_part = parts[1].strip()
                    if ' ' in serial_part:
                        serial_part = serial_part.split(' ')[0].strip()
                    info['kylin_serial'] = serial_part
            
            if '技术服务期' in line or '系统未激活' in line:
                info['service_status'] = line.split('：')[-1].strip()
            
            if '当前系统版本' in line:
                parts = line.split('：')
                if len(parts) > 1:
                    info['system_id'] = parts[1].strip()
            
            if '当前内核版本' in line:
                parts = line.split('：')
                if len(parts) > 1:
                    info['kernel'] = parts[1].strip()
            
            if '系统安装时间' in line:
                parts = line.split('：')
                if len(parts) > 1:
                    info['install_time'] = parts[1].strip()
            
            if '系统build-id' in line:
                parts = line.split('：')
                if len(parts) > 1:
                    build_id_str = parts[1].strip()
                    if 'buildid:' in build_id_str:
                        build_id_str = build_id_str.split('buildid:')[-1].strip()
                    info['build_id'] = build_id_str
            
            if '操作系统硬件码' in line:
                parts = line.split('：')
                if len(parts) > 1:
                    info['hwid'] = parts[1].strip()
                    if not info['hwid']:
                        info['hwid'] = 'Unknown'
            
            if '操作系统注册码' in line:
                parts = line.split('：')
                if len(parts) > 1:
                    info['register_code'] = parts[1].strip()
            
            if '操作系统激活码' in line:
                parts = line.split('：')
                if len(parts) > 1:
                    info['activation'] = parts[1].strip()
        
        return info

    def load_system_info(self):
        def fetch():
            return self.client.get_detailed_system_info()

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                output = result.get('data', {}).get('output', '')
                self.raw_output = output
                
                info = self.parse_system_info(output)
                
                for i in reversed(range(self.hardware_card.content_layout.count())):
                    self.hardware_card.content_layout.itemAt(i).widget().setParent(None)
                
                for i in reversed(range(self.software_card.content_layout.count())):
                    self.software_card.content_layout.itemAt(i).widget().setParent(None)
                
                for i in reversed(range(self.storage_card.content_layout.count())):
                    self.storage_card.content_layout.itemAt(i).widget().setParent(None)
                
                for i in reversed(range(self.network_card.content_layout.count())):
                    self.network_card.content_layout.itemAt(i).widget().setParent(None)
                
                self.hardware_card.add_info_row("主机型号", info['system_model'])
                self.hardware_card.add_info_row("序列号", info['serial_number'])
                self.hardware_card.add_info_row("CPU型号", info['cpu_model'])
                self.hardware_card.add_info_row("CPU核心数", f"{info['cpu_cores']} 核")
                self.hardware_card.add_info_row("CPU使用率", info['cpu_usage'])
                self.hardware_card.add_info_row("总内存", info['memory_total'])
                self.hardware_card.add_info_row("空闲内存", info['memory_free'])
                self.hardware_card.add_info_row("显卡", info['gpu'])
                
                activated = "已激活" if "已激活" in info['activation'] or "激活" in info['activation'] else "未激活"
                highlighted = "已激活" in info['activation']
                
                self.software_card.add_info_row("系统版本", info['system_id'])
                self.software_card.add_info_row("内核版本", info['kernel'])
                self.software_card.add_info_row("服务序列号", info['kylin_serial'])
                self.software_card.add_info_row("服务状态", info['service_status'])
                self.software_card.add_info_row("安装时间", info['install_time'])
                self.software_card.add_info_row("Build ID", info['build_id'])
                self.software_card.add_info_row("硬件码", info['hwid'])
                self.software_card.add_info_row("注册码", info['register_code'])
                self.software_card.add_info_row("激活状态", activated, highlighted)
                
                self.storage_card.add_info_row("根目录大小", info['disk_size'])
                self.storage_card.add_info_row("根目录可用", info['disk_free'])
                for disk in info['disks']:
                    disk_name = disk['name']
                    if disk_name.startswith('sr'):
                        continue
                    if disk_name.startswith('sd') or disk_name.startswith('nvme'):
                        disk_label = f"磁盘 ({disk_name})"
                    else:
                        disk_label = f"{disk_name}"
                    disk_size = disk['size']
                    disk_sn = disk.get('sn', 'Unknown')
                    self.storage_card.add_info_row(f"{disk_label}", f"{disk_size} / SN: {disk_sn}")
                
                for net in info['network'][:3]:
                    self.network_card.add_info_row(net['name'], net['mac'])
                
                self.refresh_btn.setEnabled(True)
            else:
                self.refresh_btn.setEnabled(True)
                QMessageBox.error(self, "错误", result.get('message', '获取系统信息失败'))

        self.refresh_btn.setEnabled(False)
        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def copy_info(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.raw_output)
        QMessageBox.information(self, "成功", "系统信息已复制到剪贴板")

    def closeEvent(self, event):
        self._is_destroyed = True
        event.accept()


class PrinterRepairDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修复打印机服务")
        self.setFixedSize(600, 400)
        self.setStyleSheet(f"background-color: {BACKGROUND_MAIN};")
        self.client = LocalClient()
        self.init_ui()
        self._is_destroyed = False

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header_icon = QLabel()
        header_icon.setPixmap(QIcon.fromTheme("printer").pixmap(32, 32))
        header_layout.addWidget(header_icon)
        
        header = QLabel("修复打印机服务")
        header.setFont(create_font(FONT_SIZE_LARGE, "semibold"))
        header.setStyleSheet(f"color: {TEXT_PRIMARY};")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        main_layout.addWidget(header_widget)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(180)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BACKGROUND_SECONDARY};
                border-radius: 12px;
                padding: 16px;
                color: {TEXT_PRIMARY};
                font-family: 'Consolas', monospace;
                font-size: 13px;
            }}
        """)
        self.log_text.setPlaceholderText("点击下方按钮开始修复打印机服务...")
        main_layout.addWidget(self.log_text)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.repair_btn = QPushButton("开始修复")
        self.repair_btn.setIcon(QIcon.fromTheme("dialog-ok-apply"))
        self.repair_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.repair_btn.clicked.connect(self.start_repair)
        btn_layout.addWidget(self.repair_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def start_repair(self):
        self.repair_btn.setEnabled(False)
        self.log_text.append("正在执行打印机修复...")

        def fetch():
            return self.client.fix_printer()

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                self.log_text.append("✅ 修复成功！")
                if result.get('output'):
                    self.log_text.append(result['output'])
                if result.get('error'):
                    self.log_text.append(f"警: {result['error']}")
                QMessageBox.information(self, "成功", "打印机服务已修复并重启。")
            else:
                self.log_text.append(f"❌ 修复失败: {result.get('message', '未知错误')}")
                if result.get('error'):
                    self.log_text.append(f"错误详情: {result['error']}")
                QMessageBox.error(self, "错误", result.get('message', '修复打印机失败'))
            self.repair_btn.setEnabled(True)

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def closeEvent(self, event):
        self._is_destroyed = True
        event.accept()


class CleanupPage(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self._is_destroyed = False
        self.config = {}
        self._threads = []
        self.init_ui()
        self.load_config()
        self.load_status()
        self.load_disk_info()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        status_bar = QFrame()
        status_bar.setStyleSheet(f"background-color: {BACKGROUND_SECONDARY};")
        status_bar_layout = QHBoxLayout(status_bar)
        status_bar_layout.setContentsMargins(12, 10, 12, 10)
        status_bar_layout.setSpacing(12)

        status_group = QWidget()
        status_group_layout = QHBoxLayout(status_group)
        status_group_layout.setContentsMargins(0, 0, 0, 0)
        status_group_layout.setSpacing(8)
        
        status_label = QLabel("服务状态:")
        status_label.setFont(create_font(FONT_SIZE_NORMAL))
        status_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        status_group_layout.addWidget(status_label)
        
        self.status_value = QLabel("运行中")
        self.status_value.setFont(create_font(FONT_SIZE_NORMAL, "semibold"))
        self.status_value.setStyleSheet(f"color: {MAC_GREEN};")
        status_group_layout.addWidget(self.status_value)
        
        status_icon = QLabel()
        status_icon.setPixmap(QIcon.fromTheme("emblem-ok").pixmap(16, 16))
        status_group_layout.addWidget(status_icon)
        
        status_bar_layout.addWidget(status_group)
        
        status_bar_layout.addStretch()

        self.auto_start_check = QCheckBox("开机自启动")
        self.auto_start_check.setStyleSheet(f"""
            QCheckBox {{
                color: {TEXT_PRIMARY};
                font-size: {FONT_SIZE_NORMAL}px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
        """)
        self.auto_start_check.stateChanged.connect(self.update_auto_start)
        status_bar_layout.addWidget(self.auto_start_check)

        main_layout.addWidget(status_bar)

        disk_bar = QFrame()
        disk_bar.setStyleSheet(f"background-color: {BACKGROUND_MAIN};")
        disk_bar_layout = QVBoxLayout(disk_bar)
        disk_bar_layout.setContentsMargins(12, 10, 12, 10)
        disk_bar_layout.setSpacing(8)

        disk_label = QLabel("磁盘容量 (/home):")
        disk_label.setFont(create_font(FONT_SIZE_SMALL))
        disk_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        disk_bar_layout.addWidget(disk_label)

        disk_info_layout = QHBoxLayout()
        self.disk_info_label = QLabel("已用 0.0 GB / 总共 0.0 GB")
        self.disk_info_label.setFont(create_font(FONT_SIZE_SMALL))
        self.disk_info_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.disk_info_label.setWordWrap(False)
        disk_info_layout.addWidget(self.disk_info_label)
        disk_info_layout.addStretch()
        
        self.disk_percent_label = QLabel("0%")
        self.disk_percent_label.setFont(create_font(FONT_SIZE_SMALL))
        self.disk_percent_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        disk_info_layout.addWidget(self.disk_percent_label)
        disk_bar_layout.addLayout(disk_info_layout)

        self.disk_progress = QProgressBar()
        self.disk_progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {BACKGROUND_SECONDARY};
                border-radius: {CORNER_BUTTON}px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background-color: {MAC_BLUE};
                border-radius: {CORNER_BUTTON}px;
            }}
        """)
        self.disk_progress.setValue(0)
        disk_bar_layout.addWidget(self.disk_progress)
        
        main_layout.addWidget(disk_bar)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_WIDGET_STYLE)

        self.init_schedule_tab()
        self.init_cleanup_settings_tab()
        self.init_quick_actions_tab()

        main_layout.addWidget(self.tabs, stretch=1)

        bottom_bar = QFrame()
        bottom_bar.setStyleSheet(f"background-color: {BACKGROUND_SECONDARY};")
        bottom_bar_layout = QHBoxLayout(bottom_bar)
        bottom_bar_layout.setContentsMargins(12, 10, 12, 10)
        bottom_bar_layout.setSpacing(10)

        bottom_bar_layout.addStretch()

        restore_btn = QPushButton("恢复默认")
        restore_btn.setIcon(QIcon.fromTheme("edit-undo"))
        restore_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        restore_btn.clicked.connect(self.restore_default)
        bottom_bar_layout.addWidget(restore_btn)

        save_btn = QPushButton("保存设置")
        save_btn.setIcon(QIcon.fromTheme("document-save"))
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #34C759;
                color: white;
                border: none;
                border-radius: {CORNER_BUTTON}px;
                padding: 8px 24px;
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_NORMAL}px;
                font-weight: 500;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: #2EAF4F;
            }}
            QPushButton:pressed {{
                background-color: #269641;
            }}
            QPushButton:disabled {{
                background-color: {TEXT_DISABLED};
            }}
        """)
        save_btn.clicked.connect(self.save_config)
        bottom_bar_layout.addWidget(save_btn)
        
        main_layout.addWidget(bottom_bar)

        self.setLayout(main_layout)

    def init_schedule_tab(self):
        schedule_tab = QWidget()
        schedule_layout = QVBoxLayout(schedule_tab)
        schedule_layout.setContentsMargins(12, 12, 12, 12)
        schedule_layout.setSpacing(12)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {BACKGROUND_MAIN};
            }}
            QScrollBar:vertical {{
                width: 12px;
                background-color: {BACKGROUND_SECONDARY};
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {TEXT_DISABLED};
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {TEXT_SECONDARY};
            }}
        """)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)

        schedule_group = QGroupBox("定时清理")
        schedule_group_layout = QVBoxLayout(schedule_group)
        schedule_group_layout.setContentsMargins(12, 12, 12, 12)
        schedule_group_layout.setSpacing(12)

        row_layout = QHBoxLayout()
        row_layout.setSpacing(12)
        label = QLabel("每日定时清理准点:")
        label.setFont(create_font(FONT_SIZE_NORMAL))
        label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        row_layout.addWidget(label)
        
        self.daily_time_edit = QLineEdit("18:00")
        self.daily_time_edit.setStyleSheet(LINE_EDIT_STYLE)
        self.daily_time_edit.setMinimumWidth(80)
        self.daily_time_edit.setMaximumWidth(100)
        row_layout.addWidget(self.daily_time_edit)
        row_layout.addStretch()
        schedule_group_layout.addLayout(row_layout)

        row_layout = QHBoxLayout()
        row_layout.setSpacing(12)
        label = QLabel("执行频率:")
        label.setFont(create_font(FONT_SIZE_NORMAL))
        label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        row_layout.addWidget(label)
        
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["每天 (Daily)", "每周 (Weekly)", "每月 (Monthly)"])
        self.frequency_combo.setStyleSheet(COMBO_BOX_STYLE)
        self.frequency_combo.setMinimumWidth(150)
        self.frequency_combo.setMaximumWidth(180)
        row_layout.addWidget(self.frequency_combo)
        row_layout.addStretch()
        schedule_group_layout.addLayout(row_layout)

        row_layout = QHBoxLayout()
        row_layout.setSpacing(12)
        label = QLabel("高频后台巡逻:")
        label.setFont(create_font(FONT_SIZE_NORMAL))
        label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        row_layout.addWidget(label)
        
        self.patrol_combo = QComboBox()
        self.patrol_combo.addItems(["关闭 (按计划执行)", "每小时", "每6小时", "每12小时"])
        self.patrol_combo.setStyleSheet(COMBO_BOX_STYLE)
        self.patrol_combo.setMinimumWidth(180)
        self.patrol_combo.setMaximumWidth(220)
        row_layout.addWidget(self.patrol_combo)
        row_layout.addStretch()
        schedule_group_layout.addLayout(row_layout)

        self.broot_clean_check = QCheckBox("每次开机时自动执行一次后台系统清理")
        self.broot_clean_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        schedule_group_layout.addWidget(self.broot_clean_check)

        row_layout = QHBoxLayout()
        row_layout.setSpacing(12)
        label = QLabel("提前提醒:")
        label.setFont(create_font(FONT_SIZE_NORMAL))
        label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        row_layout.addWidget(label)
        
        self.reminder_spin = QSpinBox()
        self.reminder_spin.setRange(1, 60)
        self.reminder_spin.setValue(5)
        self.reminder_spin.setMinimumWidth(60)
        self.reminder_spin.setMaximumWidth(80)
        row_layout.addWidget(self.reminder_spin)
        
        label = QLabel("分钟")
        label.setFont(create_font(FONT_SIZE_NORMAL))
        label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        row_layout.addWidget(label)
        row_layout.addStretch()
        schedule_group_layout.addLayout(row_layout)

        scroll_layout.addWidget(schedule_group)

        shutdown_group = QGroupBox("定时关机")
        shutdown_group_layout = QVBoxLayout(shutdown_group)
        shutdown_group_layout.setContentsMargins(12, 12, 12, 12)
        shutdown_group_layout.setSpacing(12)

        self.shutdown_enable_check = QCheckBox("启用定时关机")
        self.shutdown_enable_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.shutdown_enable_check.stateChanged.connect(self.toggle_shutdown_settings)
        shutdown_group_layout.addWidget(self.shutdown_enable_check)

        row_layout = QHBoxLayout()
        row_layout.setSpacing(12)
        label = QLabel("每日关机时间:")
        label.setFont(create_font(FONT_SIZE_NORMAL))
        label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        row_layout.addWidget(label)
        
        self.shutdown_time_edit = QLineEdit("20:00")
        self.shutdown_time_edit.setStyleSheet(LINE_EDIT_STYLE)
        self.shutdown_time_edit.setMinimumWidth(80)
        self.shutdown_time_edit.setMaximumWidth(100)
        self.shutdown_time_edit.setEnabled(False)
        row_layout.addWidget(self.shutdown_time_edit)
        row_layout.addStretch()
        shutdown_group_layout.addLayout(row_layout)

        warning_label = QLabel("⚠️ 关机前10分钟会收到系统通知提醒")
        warning_label.setFont(create_font(FONT_SIZE_SMALL))
        warning_label.setStyleSheet("color: #FF9500;")
        warning_label.setWordWrap(True)
        shutdown_group_layout.addWidget(warning_label)

        scroll_layout.addWidget(shutdown_group)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        schedule_layout.addWidget(scroll_area, stretch=1)

        self.tabs.addTab(schedule_tab, "定时任务")

    def init_cleanup_settings_tab(self):
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(12, 12, 12, 12)
        settings_layout.setSpacing(12)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {BACKGROUND_MAIN};
            }}
            QScrollBar:vertical {{
                width: 12px;
                background-color: {BACKGROUND_SECONDARY};
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {TEXT_DISABLED};
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {TEXT_SECONDARY};
            }}
        """)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)

        dirs_group = QGroupBox("清理目录")
        dirs_group_layout = QGridLayout(dirs_group)
        dirs_group_layout.setContentsMargins(12, 12, 12, 12)
        dirs_group_layout.setSpacing(10)
        dirs_group_layout.setColumnStretch(0, 1)
        dirs_group_layout.setColumnStretch(1, 1)

        self.desktop_check = QCheckBox("桌面")
        self.desktop_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        dirs_group_layout.addWidget(self.desktop_check, 0, 0)

        self.download_check = QCheckBox("下载")
        self.download_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        dirs_group_layout.addWidget(self.download_check, 0, 1)

        self.documents_check = QCheckBox("文档")
        self.documents_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        dirs_group_layout.addWidget(self.documents_check, 1, 0)

        self.pictures_check = QCheckBox("图片")
        self.pictures_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        dirs_group_layout.addWidget(self.pictures_check, 1, 1)

        self.videos_check = QCheckBox("视频")
        self.videos_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        dirs_group_layout.addWidget(self.videos_check, 2, 0)

        self.trash_check = QCheckBox("回收站")
        self.trash_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        dirs_group_layout.addWidget(self.trash_check, 2, 1)

        scroll_layout.addWidget(dirs_group)

        browser_check = QCheckBox("深度清理常用浏览器缓直 (Firefox, Chrome, Edge, 360等)")
        browser_check.setStyleSheet(f"color: {MAC_BLUE};")
        browser_check.setChecked(True)
        scroll_layout.addWidget(browser_check)

        system_group = QGroupBox("高级系统清理")
        system_group_layout = QVBoxLayout(system_group)
        system_group_layout.setContentsMargins(12, 12, 12, 12)
        system_group_layout.setSpacing(10)

        self.apt_check = QCheckBox("清理陈旧的APT安装包缓直 (释放大量系统盘空间)")
        self.apt_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        system_group_layout.addWidget(self.apt_check)

        self.journal_check = QCheckBox("清理Systemd历史运行日志 (仅保留最近7天)")
        self.journal_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        system_group_layout.addWidget(self.journal_check)

        self.thumbnails_check = QCheckBox("清理陈旧的图片与视频缩略图缓直")
        self.thumbnails_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        system_group_layout.addWidget(self.thumbnails_check)

        scroll_layout.addWidget(system_group)

        mode_group = QGroupBox("清理模式")
        mode_group_layout = QVBoxLayout(mode_group)
        mode_group_layout.setContentsMargins(12, 12, 12, 12)
        mode_group_layout.setSpacing(10)

        self.mode_all_radio = QRadioButton("清理全部文件 (保留排除扩展名)")
        self.mode_all_radio.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.mode_all_radio.setChecked(True)
        mode_group_layout.addWidget(self.mode_all_radio)

        self.mode_ext_radio = QRadioButton("仅清理指定扩展名的文件")
        self.mode_ext_radio.setStyleSheet(f"color: {TEXT_PRIMARY};")
        mode_group_layout.addWidget(self.mode_ext_radio)

        scroll_layout.addWidget(mode_group)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        settings_layout.addWidget(scroll_area, stretch=1)

        self.tabs.addTab(settings_tab, "清理设置")

    def init_quick_actions_tab(self):
        actions_tab = QWidget()
        actions_layout = QVBoxLayout(actions_tab)
        actions_layout.setContentsMargins(12, 12, 12, 12)
        actions_layout.setSpacing(12)

        service_group = QGroupBox("服务控制")
        service_group_layout = QHBoxLayout(service_group)
        service_group_layout.setContentsMargins(12, 12, 12, 12)
        service_group_layout.setSpacing(10)

        start_btn = QPushButton("启动服务")
        start_btn.setIcon(QIcon.fromTheme("media-playback-start"))
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #34C759;
                color: white;
                border: none;
                border-radius: {CORNER_BUTTON}px;
                padding: 10px 16px;
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_NORMAL}px;
                font-weight: 500;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: #2EAF4F;
            }}
        """)
        start_btn.clicked.connect(lambda: self.control_service("start"))
        service_group_layout.addWidget(start_btn, stretch=1)

        stop_btn = QPushButton("停止服务")
        stop_btn.setIcon(QIcon.fromTheme("media-playback-stop"))
        stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FF3B30;
                color: white;
                border: none;
                border-radius: {CORNER_BUTTON}px;
                padding: 10px 16px;
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_NORMAL}px;
                font-weight: 500;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: #FF453A;
            }}
        """)
        stop_btn.clicked.connect(lambda: self.control_service("stop"))
        service_group_layout.addWidget(stop_btn, stretch=1)

        restart_btn = QPushButton("重启服务")
        restart_btn.setIcon(QIcon.fromTheme("system-restart"))
        restart_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MAC_BLUE};
                color: white;
                border: none;
                border-radius: {CORNER_BUTTON}px;
                padding: 10px 16px;
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_NORMAL}px;
                font-weight: 500;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: #0066CC;
            }}
        """)
        restart_btn.clicked.connect(lambda: self.control_service("restart"))
        service_group_layout.addWidget(restart_btn, stretch=1)

        actions_layout.addWidget(service_group)

        cleanup_group = QGroupBox("清理操作")
        cleanup_group_layout = QVBoxLayout(cleanup_group)
        cleanup_group_layout.setContentsMargins(12, 12, 12, 12)
        cleanup_group_layout.setSpacing(10)

        self.run_cleanup_btn = QPushButton("立即执行清理")
        self.run_cleanup_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.run_cleanup_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MAC_BLUE};
                color: white;
                border: none;
                border-radius: {CORNER_BUTTON}px;
                padding: 12px 24px;
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_NORMAL}px;
                font-weight: 600;
                min-height: 44px;
            }}
            QPushButton:hover {{
                background-color: #0066CC;
            }}
            QPushButton:disabled {{
                background-color: {TEXT_DISABLED};
            }}
        """)
        self.run_cleanup_btn.clicked.connect(self.run_cleanup)
        cleanup_group_layout.addWidget(self.run_cleanup_btn)

        hint_label = QLabel("将根据当前的「清理设置」立即执行一次任务")
        hint_label.setFont(create_font(FONT_SIZE_SMALL))
        hint_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setWordWrap(True)
        cleanup_group_layout.addWidget(hint_label)

        actions_layout.addWidget(cleanup_group)

        log_group = QGroupBox("运行日志 (最后100行)")
        log_group_layout = QVBoxLayout(log_group)
        log_group_layout.setContentsMargins(12, 12, 12, 12)
        log_group_layout.setSpacing(10)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 11))
        self.log_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.log_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.log_text.setMinimumHeight(200)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BACKGROUND_SECONDARY};
                border: 1px solid {DIVIDER};
                border-radius: {CORNER_BUTTON}px;
                padding: 12px;
                color: {TEXT_PRIMARY};
            }}
            QScrollBar:vertical {{
                width: 12px;
                background-color: {BACKGROUND_MAIN};
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {TEXT_DISABLED};
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {TEXT_SECONDARY};
            }}
        """)
        self.log_text.setPlaceholderText("运行日志将显示在这里...")
        log_group_layout.addWidget(self.log_text, stretch=1)

        refresh_log_btn = QPushButton("刷新日志")
        refresh_log_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        refresh_log_btn.clicked.connect(self.load_log)
        log_group_layout.addWidget(refresh_log_btn)

        actions_layout.addWidget(log_group, stretch=1)

        self.tabs.addTab(actions_tab, "快捷操作")

    def toggle_shutdown_settings(self, state):
        enabled = state == Qt.Checked
        self.shutdown_time_edit.setEnabled(enabled)

    def load_disk_info(self):
        try:
            import shutil
            total, used, free = shutil.disk_usage('/home')
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            percent = int((used / total) * 100)
            
            self.disk_info_label.setText(f"已用 {used_gb:.1f} GB / 总共 {total_gb:.1f} GB")
            self.disk_percent_label.setText(f"{percent}%")
            self.disk_progress.setValue(percent)
        except Exception as e:
            pass

    def load_config(self):
        def fetch():
            return self.client.get_cleanup_config()

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                self.config = result.get('data', {})
                
                self.daily_time_edit.setText(self.config.get('CLEANUP_TIME', '18:00'))
                freq = self.config.get('CLEANUP_FREQUENCY', 'daily')
                freq_map = {'daily': 0, 'weekly': 1, 'monthly': 2}
                self.frequency_combo.setCurrentIndex(freq_map.get(freq, 0))
                
                self.shutdown_time_edit.setText(self.config.get('SHUTDOWN_TIME', '20:00'))
                self.shutdown_enable_check.setChecked(self.config.get('SHUTDOWN_ENABLED', 'no') == 'yes')
                
                dirs = self.config.get('CLEANUP_DIRS', '').split(',')
                self.desktop_check.setChecked('Desktop' in dirs)
                self.download_check.setChecked('Downloads' in dirs)
                self.documents_check.setChecked('Documents' in dirs)
                self.pictures_check.setChecked('Pictures' in dirs)
                self.videos_check.setChecked('Videos' in dirs)
                self.trash_check.setChecked('Trash' in dirs)
                
                self.apt_check.setChecked(self.config.get('CLEANUP_SYS_APT', 'no') == 'yes')
                self.journal_check.setChecked(self.config.get('CLEANUP_SYS_JOURNAL', 'no') == 'yes')
                self.thumbnails_check.setChecked(self.config.get('CLEANUP_SYS_THUMBNAILS', 'no') == 'yes')
                
                mode = self.config.get('CLEANUP_MODE', 'all')
                self.mode_all_radio.setChecked(mode == 'all')
                self.mode_ext_radio.setChecked(mode == 'ext_only')
                
                self.broot_clean_check.setChecked(self.config.get('CLEANUP_ON_BOOT', 'no') == 'yes')
                self.auto_start_check.setChecked(self.config.get('SHUTDOWN_ENABLED', 'no') == 'yes')

        thread = WorkerThread(fetch)
        thread.finished.connect(on_result)
        thread.finished.connect(lambda: self._threads.remove(thread) if thread in self._threads else None)
        self._threads.append(thread)
        thread.start()

    def save_config(self):
        dirs = []
        if self.desktop_check.isChecked():
            dirs.append('Desktop')
        if self.download_check.isChecked():
            dirs.append('Downloads')
        if self.documents_check.isChecked():
            dirs.append('Documents')
        if self.pictures_check.isChecked():
            dirs.append('Pictures')
        if self.videos_check.isChecked():
            dirs.append('Videos')
        if self.trash_check.isChecked():
            dirs.append('Trash')

        freq_map = {0: 'daily', 1: 'weekly', 2: 'monthly'}
        freq = freq_map.get(self.frequency_combo.currentIndex(), 'daily')

        config = {
            'CLEANUP_TIME': self.daily_time_edit.text(),
            'SHUTDOWN_TIME': self.shutdown_time_edit.text(),
            'SHUTDOWN_ENABLED': 'yes' if self.shutdown_enable_check.isChecked() else 'no',
            'NOTIFICATION_MINUTES': str(self.reminder_spin.value()),
            'CLEANUP_MODE': 'all' if self.mode_all_radio.isChecked() else 'ext_only',
            'CLEANUP_DIRS': ','.join(dirs),
            'CLEANUP_FREQUENCY': freq,
            'CLEANUP_ON_BOOT': 'yes' if self.broot_clean_check.isChecked() else 'no',
            'CLEANUP_BROWSERS': 'yes',
            'CLEANUP_SYS_APT': 'yes' if self.apt_check.isChecked() else 'no',
            'CLEANUP_SYS_JOURNAL': 'yes' if self.journal_check.isChecked() else 'no',
            'CLEANUP_SYS_THUMBNAILS': 'yes' if self.thumbnails_check.isChecked() else 'no',
            'CLEANUP_EXTENSIONS': '.tmp,.log,.bak,.cache,.swp,.xlsx,.xls,.doc,.docx,.jpg,.jpeg,.rar,.zip,.ppt,.pdf,.pptx,.png,.txt,.wps,.wpt,.et,.ett,.dps,.dpt,.ofd',
            'EXCLUDE_EXTENSIONS': '.ico,.desktop',
            'CLEANUP_INTERVAL': '0'
        }

        def fetch():
            return self.client.update_cleanup_config(config)

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                QMessageBox.information(self, "成功", "配置已保存")
                self.config = config
            else:
                QMessageBox.warning(self, "失败", result.get('message', '保存失败'))

        thread = WorkerThread(fetch)
        thread.finished.connect(on_result)
        thread.finished.connect(lambda: self._threads.remove(thread) if thread in self._threads else None)
        self._threads.append(thread)
        thread.start()

    def restore_default(self):
        self.daily_time_edit.setText('18:00')
        self.frequency_combo.setCurrentIndex(0)
        self.patrol_combo.setCurrentIndex(0)
        self.broot_clean_check.setChecked(False)
        self.reminder_spin.setValue(5)
        self.shutdown_enable_check.setChecked(False)
        self.shutdown_time_edit.setText('20:00')
        
        self.desktop_check.setChecked(True)
        self.download_check.setChecked(True)
        self.documents_check.setChecked(True)
        self.pictures_check.setChecked(True)
        self.videos_check.setChecked(True)
        self.trash_check.setChecked(True)
        
        self.apt_check.setChecked(False)
        self.journal_check.setChecked(False)
        self.thumbnails_check.setChecked(False)
        
        self.mode_all_radio.setChecked(True)
        self.auto_start_check.setChecked(False)

        QMessageBox.information(self, "提示", "已恢复默认设置")

    def update_auto_start(self, state):
        enabled = state == Qt.Checked
        action = 'enable' if enabled else 'disable'
        
        def fetch():
            return self.client.control_cleanup_service(action)

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') != 'success':
                self.auto_start_check.setChecked(not enabled)

        thread = WorkerThread(fetch)
        thread.finished.connect(on_result)
        thread.finished.connect(lambda: self._threads.remove(thread) if thread in self._threads else None)
        self._threads.append(thread)
        thread.start()

    def run_cleanup(self):
        self.run_cleanup_btn.setEnabled(False)
        self.log_text.clear()
        self.log_text.append("正在执行系统清理...")

        def fetch():
            return self.client.run_cleanup()

        def on_result(result):
            if self._is_destroyed:
                return
            self.run_cleanup_btn.setEnabled(True)
            if result.get('status') == 'success':
                self.log_text.append("✅ 清理完成！")
                log = result.get('data', {}).get('log', '')
                if log:
                    self.log_text.append(log)
                QMessageBox.information(self, "成功", "系统清理完成")
                self.load_disk_info()
            else:
                self.log_text.append(f"❌ 清理失败: {result.get('message', '未知错误')}")
                QMessageBox.warning(self, "失败", result.get('message', '清理失败'))

        thread = WorkerThread(fetch)
        thread.finished.connect(on_result)
        thread.finished.connect(lambda: self._threads.remove(thread) if thread in self._threads else None)
        self._threads.append(thread)
        thread.start()

    def load_status(self):
        def fetch():
            return self.client.get_cleanup_status()

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                data = result.get('data', {})
                active = data.get('active', False)
                enabled = data.get('enabled', False)
                
                if active:
                    self.status_value.setText("运行中")
                    self.status_value.setStyleSheet(f"color: {MAC_GREEN};")
                else:
                    self.status_value.setText("已停止")
                    self.status_value.setStyleSheet(f"color: {MAC_RED};")
                
                self.auto_start_check.setChecked(enabled)

        thread = WorkerThread(fetch)
        thread.finished.connect(on_result)
        thread.finished.connect(lambda: self._threads.remove(thread) if thread in self._threads else None)
        self._threads.append(thread)
        thread.start()

    def load_log(self):
        self.log_text.clear()
        self.log_text.append("正在加载日志...")

        def fetch():
            return self.client.get_cleanup_status()

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                logs = result.get('data', {}).get('logs', '')
                if logs:
                    self.log_text.setPlainText(logs)
                else:
                    self.log_text.setPlainText("暂无日志")

        thread = WorkerThread(fetch)
        thread.finished.connect(on_result)
        thread.finished.connect(lambda: self._threads.remove(thread) if thread in self._threads else None)
        self._threads.append(thread)
        thread.start()

    def control_service(self, action):
        def fetch():
            return self.client.control_cleanup_service(action)

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                QMessageBox.information(self, "成功", f"服务已{action}")
                self.load_status()
            else:
                QMessageBox.warning(self, "失败", result.get('message', f"服务{action}失败"))

        thread = WorkerThread(fetch)
        thread.finished.connect(on_result)
        thread.finished.connect(lambda: self._threads.remove(thread) if thread in self._threads else None)
        self._threads.append(thread)
        thread.start()

    def closeEvent(self, event):
        self._is_destroyed = True
        for thread in list(self._threads):
            if thread.isRunning():
                thread.wait(5000)
        event.accept()


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

        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(QFont("Consolas", 10))

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("输入命令...")
        self.command_input.returnPressed.connect(self.execute_command)

        btn_layout = QHBoxLayout()
        execute_btn = QPushButton("执行")
        execute_btn.clicked.connect(self.execute_command)
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(lambda: self.terminal_output.clear())
        btn_layout.addWidget(self.command_input)
        btn_layout.addWidget(execute_btn)
        btn_layout.addWidget(clear_btn)

        main_layout.addWidget(self.terminal_output)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def execute_command(self):
        command = self.command_input.text()
        if not command.strip():
            return

        self.terminal_output.append(f"> {command}")
        
        def run_cmd():
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                return result.stdout + result.stderr
            except Exception as e:
                return str(e)

        def on_result(output):
            self.terminal_output.append(output)
            self.command_input.clear()

        self.thread = WorkerThread(run_cmd)
        self.thread.finished.connect(on_result)
        self.thread.start()


class ToolCard(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, icon_name, title, description, color=MAC_BLUE, parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.icon_name = icon_name
        self.color = color
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        self.setStyleSheet(TOOL_CARD_STYLE)
        self.setCursor(Qt.PointingHandCursor)

        icon_label = QLabel()
        icon_label.setPixmap(QIcon.fromTheme(self.icon_name).pixmap(48, 48))
        icon_label.setStyleSheet(f"color: {self.color};")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        title_label = QLabel(self.title)
        title_label.setFont(create_font(FONT_SIZE_NORMAL, "semibold"))
        title_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        desc_label = QLabel(self.description)
        desc_label.setFont(create_font(FONT_SIZE_SMALL))
        desc_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class FeatureToolsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        header_label = QLabel("特色工具")
        header_label.setFont(create_font(FONT_SIZE_LARGE, "semibold"))
        header_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        main_layout.addWidget(header_label)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)

        hosts_card = ToolCard("network", "自定义本地域名解析文件", "编辑 hosts 文件配置域名解析", "#FF2D55")
        hosts_card.clicked.connect(self.open_hosts_editor)
        grid_layout.addWidget(hosts_card, 0, 0)

        sysinfo_card = ToolCard("computer", "系统信息查看", "查看详细的系统硬件和软件信息", "#34C759")
        sysinfo_card.clicked.connect(self.open_system_info)
        grid_layout.addWidget(sysinfo_card, 0, 1)

        printer_card = ToolCard("printer", "修复打印机服务", "恢复CUPS默认配置并重启打印服务", "#007AFF")
        printer_card.clicked.connect(self.open_printer_repair)
        grid_layout.addWidget(printer_card, 1, 0)

        kms_card = ToolCard("security-high", "KMS脚本生成器", "可视化定制KMS激活脚本，支持克隆机修复", "#FF9500")
        kms_card.clicked.connect(self.open_kms_generator)
        grid_layout.addWidget(kms_card, 1, 1)

        cleanup_card = ToolCard("edit-delete", "系统清理", "清理系统垃圾文件、浏览器缓直、回收站等", "#FF3B30")
        cleanup_card.clicked.connect(self.open_cleanup)
        grid_layout.addWidget(cleanup_card, 2, 0)

        usb_card = ToolCard("usb-fix-tool", "U盘工具箱", "检测修复只读U盘，支持格式化、安全擦除和启动盘制作", "#5AC8FA")
        usb_card.clicked.connect(self.open_usb_fix_tool)
        grid_layout.addWidget(usb_card, 2, 1)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        scroll_content = QWidget()
        scroll_content.setLayout(grid_layout)
        scroll_area.setWidget(scroll_content)

        main_layout.addWidget(scroll_area, stretch=1)
        self.setLayout(main_layout)

    def open_hosts_editor(self):
        dialog = HostsEditorDialog(self)
        dialog.exec_()

    def open_system_info(self):
        dialog = SystemInfoDialog(self)
        dialog.exec_()

    def open_printer_repair(self):
        dialog = PrinterRepairDialog(self)
        dialog.exec_()

    def open_kms_generator(self):
        dialog = KmsScriptGeneratorDialog(self)
        dialog.exec_()

    def open_cleanup(self):
        from core.local_client import LocalClient
        dialog = QDialog(self)
        dialog.setWindowTitle("系统清理")
        dialog.setMinimumSize(800, 600)
        dialog.resize(800, 600)
        dialog.setStyleSheet(f"background-color: {BACKGROUND_MAIN};")
        
        layout = QVBoxLayout(dialog)
        cleanup_page = CleanupPage(LocalClient())
        layout.addWidget(cleanup_page)
        
        dialog.exec_()

    def open_usb_fix_tool(self):
        candidates = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "usb_fix_tool", "usb_tool.py"),
            "/usr/share/kylin-system-tools/tools/usb_fix_tool/usb_tool.py",
        ]
        script_path = next((path for path in candidates if os.path.exists(path)), None)

        try:
            if script_path:
                subprocess.Popen([sys.executable or "python3", script_path])
            else:
                subprocess.Popen(["kylin-usb-tool"])
        except Exception as e:
            QMessageBox.warning(self, "启动失败", f"无法启动U盘工具箱: {str(e)}")


class KmsScriptGeneratorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KMS脚本生成器")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        self.setStyleSheet(f"background-color: {BACKGROUND_MAIN};")
        
        self.kms_server = "10.0.0.10"
        self.options = {
            'clone_fix': True,
            'deploy_license': True,
            'network_diagnosis': True,
            'version_compatible': True
        }
        self.license_files = []
        self.license_base64 = {}
        
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)
        left_panel.setMinimumWidth(320)
        left_panel.setMaximumWidth(380)

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        
        header_icon = QLabel()
        header_icon.setPixmap(QIcon.fromTheme("key").pixmap(32, 32))
        header_layout.addWidget(header_icon)
        
        header_label = QLabel("KMS脚本生成器")
        header_label.setFont(create_font(FONT_SIZE_LARGE, "semibold"))
        header_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        header_layout.addWidget(header_label)
        
        left_layout.addWidget(header_widget)

        desc_label = QLabel("可视化定制多功能KMS激活脚本，支持克隆机修复与全版本适配")
        desc_label.setFont(create_font(FONT_SIZE_SMALL))
        desc_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        desc_label.setWordWrap(True)
        left_layout.addWidget(desc_label)

        kms_group = QGroupBox("KMS服务器配置")
        kms_layout = QVBoxLayout(kms_group)
        kms_layout.setContentsMargins(16, 16, 16, 16)
        
        self.kms_input = QLineEdit(self.kms_server)
        self.kms_input.setStyleSheet(LINE_EDIT_STYLE)
        kms_layout.addWidget(self.kms_input)
        
        preset_layout = QHBoxLayout()
        preset_btn1 = QPushButton("内网A")
        preset_btn1.setStyleSheet(SECONDARY_BUTTON_STYLE)
        preset_btn1.clicked.connect(lambda: self.kms_input.setText("10.0.0.10"))
        preset_layout.addWidget(preset_btn1)
        
        preset_btn2 = QPushButton("云KMS")
        preset_btn2.setStyleSheet(SECONDARY_BUTTON_STYLE)
        preset_btn2.clicked.connect(lambda: self.kms_input.setText("kms.example.com"))
        preset_layout.addWidget(preset_btn2)
        
        preset_btn3 = QPushButton("本地回路")
        preset_btn3.setStyleSheet(SECONDARY_BUTTON_STYLE)
        preset_btn3.clicked.connect(lambda: self.kms_input.setText("127.0.0.1"))
        preset_layout.addWidget(preset_btn3)
        
        kms_layout.addLayout(preset_layout)
        left_layout.addWidget(kms_group)

        options_group = QGroupBox("高级功能选项")
        options_layout = QVBoxLayout(options_group)
        options_layout.setContentsMargins(16, 16, 16, 16)
        
        self.clone_check = QCheckBox("克隆机硬件标识清理")
        self.clone_check.setChecked(self.options['clone_fix'])
        self.clone_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.clone_check.toggled.connect(lambda checked: self.update_option('clone_fix', checked))
        options_layout.addWidget(self.clone_check)
        
        self.license_check = QCheckBox("自动探测并部署授权文件")
        self.license_check.setChecked(self.options['deploy_license'])
        self.license_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.license_check.toggled.connect(lambda checked: self.update_option('deploy_license', checked))
        options_layout.addWidget(self.license_check)
        
        self.diagnosis_check = QCheckBox("连接性前置诊断")
        self.diagnosis_check.setChecked(self.options['network_diagnosis'])
        self.diagnosis_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.diagnosis_check.toggled.connect(lambda checked: self.update_option('network_diagnosis', checked))
        options_layout.addWidget(self.diagnosis_check)
        
        self.compatible_check = QCheckBox("全版本兼容适配")
        self.compatible_check.setChecked(self.options['version_compatible'])
        self.compatible_check.setStyleSheet(f"color: {TEXT_PRIMARY};")
        self.compatible_check.toggled.connect(lambda checked: self.update_option('version_compatible', checked))
        options_layout.addWidget(self.compatible_check)
        
        left_layout.addWidget(options_group)

        license_group = QGroupBox("授权文件上传")
        license_layout = QVBoxLayout(license_group)
        license_layout.setContentsMargins(16, 16, 16, 16)
        license_layout.setSpacing(12)
        
        upload_btn = QPushButton("上传授权文件")
        upload_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        upload_btn.clicked.connect(self.upload_license_file)
        license_layout.addWidget(upload_btn)
        
        self.license_list = QListWidget()
        self.license_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {BACKGROUND_SECONDARY};
                border-radius: {CORNER_BUTTON}px;
                border: 1px solid {DIVIDER};
                padding: 4px;
                color: {TEXT_PRIMARY};
                font-size: {FONT_SIZE_SMALL}px;
            }}
            QListWidget::item {{
                padding: 4px;
            }}
        """)
        self.license_list.setMaximumHeight(80)
        license_layout.addWidget(self.license_list)
        
        hint_label = QLabel("支持 .kyinfo、.zip、LICENSE 等文件\n已上传的文件将嵌入到脚本中")
        hint_label.setFont(create_font(FONT_SIZE_SMALL))
        hint_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        hint_label.setWordWrap(True)
        license_layout.addWidget(hint_label)
        
        left_layout.addWidget(license_group)

        btn_layout = QHBoxLayout()
        
        download_btn = QPushButton("下载脚本")
        download_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        download_btn.clicked.connect(self.download_script)
        btn_layout.addWidget(download_btn)
        
        copy_btn = QPushButton("复制代码")
        copy_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        copy_btn.clicked.connect(self.copy_script)
        btn_layout.addWidget(copy_btn)
        
        run_btn = QPushButton("运行脚本")
        run_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FF3B30;
                color: white;
                border: none;
                border-radius: {CORNER_BUTTON}px;
                padding: 8px 24px;
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_NORMAL}px;
                font-weight: 500;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: #FF453A;
            }}
            QPushButton:pressed {{
                background-color: #CC2D24;
            }}
            QPushButton:disabled {{
                background-color: {TEXT_DISABLED};
            }}
        """)
        run_btn.clicked.connect(self.run_script)
        btn_layout.addWidget(run_btn)
        
        left_layout.addLayout(btn_layout)
        left_layout.addStretch()

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        header_right = QWidget()
        header_right_layout = QHBoxLayout(header_right)
        header_right_layout.setContentsMargins(0, 0, 0, 0)
        
        title_right = QLabel("实时预览")
        title_right.setFont(create_font(FONT_SIZE_NORMAL, "medium"))
        title_right.setStyleSheet(f"color: {TEXT_PRIMARY};")
        header_right_layout.addWidget(title_right)
        
        header_right_layout.addStretch()
        
        file_label = QLabel("kms_activate.sh")
        file_label.setFont(create_font(FONT_SIZE_SMALL))
        file_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        header_right_layout.addWidget(file_label)
        
        lang_label = QLabel("Bash Script")
        lang_label.setFont(create_font(FONT_SIZE_SMALL))
        lang_label.setStyleSheet(f"color: {MAC_BLUE};")
        header_right_layout.addWidget(lang_label)
        
        right_layout.addWidget(header_right)

        self.script_text = QTextEdit()
        self.script_text.setReadOnly(True)
        self.script_text.setFont(QFont("Consolas", 11))
        self.script_text.setLineWrapMode(QTextEdit.NoWrap)
        self.script_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.script_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.script_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BACKGROUND_SECONDARY};
                border-radius: {CORNER_BUTTON}px;
                padding: 12px;
                color: {TEXT_PRIMARY};
                border: 1px solid {DIVIDER};
            }}
            QTextEdit QScrollBar {{
                width: 12px;
                height: 12px;
            }}
            QTextEdit QScrollBar::handle {{
                background-color: {TEXT_DISABLED};
                border-radius: 6px;
            }}
            QTextEdit QScrollBar::handle:hover {{
                background-color: {TEXT_SECONDARY};
            }}
        """)
        right_layout.addWidget(self.script_text, stretch=1)

        help_group = QGroupBox("使用说明")
        help_layout = QVBoxLayout(help_group)
        help_layout.setContentsMargins(12, 12, 12, 12)
        help_layout.setSpacing(4)
        
        title_label = QLabel("使用说明")
        title_label.setFont(create_font(FONT_SIZE_NORMAL, weight="bold"))
        title_label.setStyleSheet("color: #BF5AF2;")
        help_layout.addWidget(title_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"color: {DIVIDER};")
        help_layout.addWidget(line)
        
        instructions = [
            ("• 赋予执行权限:", "chmod +x kms_activate.sh"),
            ("• 以管理员身份运行:", "sudo ./kms_activate.sh"),
            ("• 注意事项:", "脚本执行后请重启系统或手动执行 kylin-activation -auto 以刷新状态。")
        ]
        
        for label_text, code_text in instructions:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)
            
            label = QLabel(label_text)
            label.setFont(create_font(FONT_SIZE_SMALL))
            label.setStyleSheet(f"color: {TEXT_SECONDARY};")
            label.setWordWrap(False)
            row_layout.addWidget(label, stretch=0)
            
            code_label = QLabel(code_text)
            code_label.setFont(QFont("Consolas", 11))
            code_label.setStyleSheet(f"background-color: {BACKGROUND_SECONDARY}; color: #34C759; padding: 2px 6px; border-radius: 4px;")
            code_label.setWordWrap(True)
            row_layout.addWidget(code_label, stretch=1)
            
            help_layout.addLayout(row_layout)
        
        right_layout.addWidget(help_group)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, stretch=1)
        self.setLayout(main_layout)
        
        self.update_script()

    def update_option(self, key, value):
        self.options[key] = value
        self.update_script()

    def upload_license_file(self):
        file_path = QFileDialog.getOpenFileName(
            self, 
            "选择授权文件", 
            "", 
            "授权文件 (*.kyinfo *.zip LICENSE *LICENSE*);;所有文件 (*)"
        )
        
        if file_path[0]:
            try:
                import os
                import base64
                
                abs_path = os.path.abspath(file_path[0])
                
                if abs_path in self.license_files:
                    QMessageBox.warning(self, "警", "该文件已添加！")
                    return
                
                with open(abs_path, 'rb') as f:
                    base64_data = base64.b64encode(f.read()).decode('ascii')
                
                self.license_files.append(abs_path)
                self.license_base64[abs_path] = base64_data
                
                file_name = os.path.basename(abs_path)
                self.license_list.addItem(file_name)
                
                self.update_script()
                
                QMessageBox.information(self, "成功", f"已添加授权文件: {file_name}")
            
            except Exception as e:
                QMessageBox.error(self, "错误", f"读取文件失败: {str(e)}")

    def update_script(self):
        self.kms_server = self.kms_input.text().strip()
        self.script_text.setText(self.generate_script())

    def generate_script(self):
        from datetime import datetime
        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        
        script = f"""#!/bin/bash
# ============================================================
# 银河麒麟 KMS 全自动激活脚本 (可视化生成版)
# 生成时间: {now}
# ============================================================

# 关境检查
if [ "$(id -u)" -ne 0 ]; then
    echo ">>> 请以 rroot 权限运行，正在尝试 sudo..."
    exec sudo "$0" "$@"
fi

KMS_SERVER="{self.kms_server}"

"""
        
        if self.options['network_diagnosis']:
            script += """
echo ">>> 正在执行关境诊断..."
if ! ping -c 1 -W 2 "$KMS_SERVER" &>/dev/null; then
    echo "警: 无法连通 KMS 服务器 ($KMS_SERVER)，请检查网络"
fi

"""
        
        if self.options['clone_fix']:
            script += """
echo ">>> 正在清理旧硬件标识 (克隆机修修复)..."
[ -f "/etc/.kyhwid" ] && rm -vf /etc/.kyhwid

"""
        
        if self.license_files:
            script += "\n"
            for file_path, base64_data in self.license_base64.items():
                file_basename = os.path.basename(file_path)
                script += f'''
echo ">>> 正在释放内嵌授权文件: {file_basename}..."
TMP_FILE="/tmp/{file_basename}"
echo "{base64_data}" | base64 -d > "$TMP_FILE"
if [[ "$TMP_FILE" == *.zip ]]; then
    echo "  正在解压部署..."
    unzip -q -o "$TMP_FILE" -d /tmp/kms_inner_deploy
    cp -ar -f /tmp/kms_inner_deploy/* /etc/
    rm -rf /tmp/kms_inner_deploy
else
    echo "  正在部署文件..."
    cp -vf "$TMP_FILE" /etc/
fi
rm -f "$TMP_FILE"

'''
        
        if self.options['deploy_license']:
            script += """
echo ">>> 正在探测并部署本地授权许可文件..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LICENSE_FILES=($(find "$SCRIPT_DIR" -maxdepth 1 \\( -name "*.kyinfo" -o -name "LICENSE" -o -name "*-*.zip" \\) 2>/dev/null))

if [ ${#LICENSE_FILES[@]} -gt 0 ]; then
    for file in "${{LICENSE_FILES[@]}}"; do
        if [[ "$file" == *.zip ]]; then
            echo "  正在解压部署: $(basename "$file")"
            unzip -q -o "$file" -d /tmp/kms_deploy
            cp -ar -f /tmp/kms_deploy/* /etc/
            rm -rf /tmp/kms_deploy
        else
            echo "  正在拷贝文件: $(basename "$file")"
            cp -vf "$file" /etc/
        fi
    done
else
    echo "  [跳过] 未在当前目录发现额外授权文件"
fi

"""
        
        script += f"""
echo ">>> 正在配置 KMS 服务器为: $KMS_SERVER"

"""
        
        if self.options['version_compatible']:
            script += """
# 兼容旧路径
KMS_CONF="/usr/share/kylin-activation/kms.conf"
[ -f "$KMS_CONF" ] && sed -i "s/server=.*/server=$KMS_SERVER/" "$KMS_CONF"

# 兼容新路径
INI_CONF="/usr/share/kylin-activation/activation_conf.ini"
[ -f "$INI_CONF" ] && sed -i "s/ServerIp *=.*/ServerIp = $KMS_SERVER/" "$INI_CONF"

"""
        
        script += """
echo ">>> 正在触发激活服务..."
if command -v kylin-activation &>/dev/null; then
    kylin-activation -auto
    echo ">>> 激活请求已发送，请在系统属性界面查看结果。"
else
    echo "错误: 未找到系统激活工具，请手动检查关境。"
fi

echo -e "\\n脚本执行完成！"
"""
        
        return script

    def download_script(self):
        script = self.generate_script()
        file_path = QFileDialog.getSaveFileName(self, "保直脚本", "kms_activate.sh", "Shell Script (*.sh)")
        if file_path[0]:
            try:
                with open(file_path[0], 'w') as f:
                    f.write(script)
                QMessageBox.information(self, "成功", "脚本已保直！")
            except Exception as e:
                QMessageBox.error(self, "错误", f"保直失败: {str(e)}")

    def copy_script(self):
        script = self.generate_script()
        clipboard = QApplication.clipboard()
        clipboard.setText(script)
        QMessageBox.information(self, "成功", "脚本代码已复制到剪贴板！")

    def validate_script(self, script):
        if not script or not script.strip():
            return False, "脚本内容为空"
        
        if not script.startswith('#!/bin/bash'):
            return False, "脚本不是有效的Bash脚本"
        
        if 'KMS_SERVER' not in script:
            return False, "脚本缺少KMS服务器配置"
        
        return True, "脚本验证通过"

    def run_script(self):
        script = self.generate_script()
        
        valid, message = self.validate_script(script)
        if not valid:
            QMessageBox.warning(self, "警", f"脚本验证失败: {message}")
            return
        
        reply = QMessageBox.question(
            self, 
            "确认运行", 
            "即将执行KMS激活脚本，此操作将修改系统配置。\n\n"
            "注意：\n"
            "- 脚本需要管理员权限运行\n"
            "- 请确保已备份重要数据\n"
            "- 建议在虚拟机或测试关境中先测试\n\n"
            "确定要继续执行吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        run_dialog = QDialog(self)
        run_dialog.setWindowTitle("运行脚本")
        run_dialog.setMinimumSize(600, 400)
        run_dialog.setStyleSheet(f"background-color: {BACKGROUND_MAIN};")
        
        layout = QVBoxLayout(run_dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        status_label = QLabel("脚本运行中...")
        status_label.setFont(create_font(FONT_SIZE_NORMAL, "semibold"))
        status_label.setStyleSheet(f"color: {MAC_BLUE};")
        layout.addWidget(status_label)
        
        output_text = QTextEdit()
        output_text.setReadOnly(True)
        output_text.setFont(QFont("Consolas", 10))
        output_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BACKGROUND_SECONDARY};
                border-radius: {CORNER_BUTTON}px;
                padding: 12px;
                color: {TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(output_text, stretch=1)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #E5E5EA;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #007AFF;
                border-radius: 4px;
            }
        """)
        layout.addWidget(progress_bar)
        
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        close_btn.clicked.connect(run_dialog.close)
        close_btn.setEnabled(False)
        layout.addWidget(close_btn)
        
        run_dialog.show()
        
        import subprocess
        import tempfile
        import os
        
        def execute_script():
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                    f.write(script)
                    temp_script = f.name
                
                os.chmod(temp_script, 0o755)
                
                process = subprocess.Popen(
                    ['pkexec', 'bash', temp_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                output_lines = []
                for line in iter(process.stdout.readline, ''):
                    output_lines.append(line)
                    output_text.append(line)
                
                process.wait()
                
                os.unlink(temp_script)
                
                return process.returncode, ''.join(output_lines)
            
            except Exception as e:
                return -1, f"执行错误: {str(e)}"
        
        def on_finish(result):
            return_code, output = result
            
            if return_code == 0:
                status_label.setText("运行成功")
                status_label.setStyleSheet(f"color: {MAC_GREEN};")
            else:
                status_label.setText("运行失败")
                status_label.setStyleSheet(f"color: #FF3B30;")
            
            progress_bar.setRange(0, 1)
            progress_bar.setValue(1)
            close_btn.setEnabled(True)
            
            if output:
                output_text.append("\n" + "="*50)
                if return_code == 0:
                    output_text.append("脚本执行成功！")
                else:
                    output_text.append(f"脚本执行失败，退出码: {return_code}")
        
        thread = WorkerThread(execute_script)
        thread.finished.connect(on_finish)
        thread.start()
        
        run_dialog.exec_()


class MainWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.setWindowTitle("麒麟运维百宝箱")
        try:
            self.setWindowIcon(QIcon.fromTheme("kylin-system-tools"))
        except:
            pass
        self.setGeometry(100, 100, 1200, 800)
        self.init_ui()

    def closeEvent(self, event):
        if hasattr(self, 'system_info_page') and hasattr(self.system_info_page, 'cleanup'):
            self.system_info_page.cleanup()
        if hasattr(self, 'system_status_page') and hasattr(self.system_status_page, 'cleanup'):
            self.system_status_page.cleanup()
        if hasattr(self, 'user_management_page') and hasattr(self.user_management_page, 'cleanup'):
            self.user_management_page.cleanup()
        if hasattr(self, 'log_page') and hasattr(self.log_page, 'cleanup'):
            self.log_page.cleanup()
        event.accept()

    def init_ui(self):
        self.statusBar().showMessage("就绪")
        self.setStyleSheet(WINDOW_STYLE)

        self.create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.create_sidebar(main_layout)

        self.content_area = QFrame()
        self.content_area.setStyleSheet(f"background-color: {BACKGROUND_SECONDARY};")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        main_layout.addWidget(self.content_area, stretch=1)

        self.current_main_page = None
        self.show_feature_tools()

    def create_sidebar(self, main_layout):
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: #1C1C1E;
                border-right: 1px solid {DIVIDER};
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        logo_frame = QFrame()
        logo_frame.setStyleSheet("background-color: #1C1C1E;")
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(20, 20, 20, 20)

        logo_label = QLabel("Kylin-Tools")
        logo_label.setFont(create_font(FONT_SIZE_LARGE, "bold"))
        logo_label.setStyleSheet("color: #FFFFFF;")
        logo_layout.addWidget(logo_label)

        sidebar_layout.addWidget(logo_frame)

        nav_items = [
            ("系统监视器", "server"),
            ("百宝箱", "applications"),
        ]

        self.nav_buttons = {}
        for name, icon_name in nav_items:
            btn = QPushButton()
            btn.setIcon(QIcon.fromTheme(icon_name))
            btn.setText(name)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: #B3B3B3;
                    border: none;
                    text-align: left;
                    padding: 14px 20px;
                    font-family: {FONT_FAMILY};
                    font-size: {FONT_SIZE_NORMAL}px;
                    border-left: 3px solid transparent;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.1);
                    color: #FFFFFF;
                }}
                QPushButton:checked {{
                    background-color: rgba(0, 122, 255, 0.15);
                    color: {MAC_BLUE};
                    border-left: 3px solid {MAC_BLUE};
                }}
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, n=name: self.on_nav_click(n))
            self.nav_buttons[name] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        about_btn = QPushButton()
        about_btn.setIcon(QIcon.fromTheme("help-about"))
        about_btn.setText("关于")
        about_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #B3B3B3;
                border: none;
                text-align: left;
                padding: 14px 20px;
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_NORMAL}px;
            }}
            QPushButton:hover {{
                color: #FFFFFF;
            }}
        """)
        about_btn.clicked.connect(self.show_about)
        sidebar_layout.addWidget(about_btn)

        main_layout.addWidget(sidebar)

    def create_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {BACKGROUND_MAIN};
                border-bottom: 1px solid {DIVIDER};
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_NORMAL}px;
            }}
            QMenuBar::item {{
                color: {TEXT_PRIMARY};
                padding: 8px 16px;
            }}
            QMenuBar::item:hover {{
                background-color: {BACKGROUND_HOVER};
            }}
        """)

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

    def on_nav_click(self, name):
        for btn_name, btn in self.nav_buttons.items():
            btn.setChecked(btn_name == name)

        if name == "百宝箱":
            self.show_feature_tools()
        elif name == "系统监视器":
            self.show_system_status()
        
        

    def clear_content(self):
        if self.current_main_page:
            self.content_layout.removeWidget(self.current_main_page)
            self.current_main_page.deleteLater()
            self.current_main_page = None
        if hasattr(self, 'current_top_bar') and self.current_top_bar:
            self.content_layout.removeWidget(self.current_top_bar)
            self.current_top_bar.deleteLater()
            self.current_top_bar = None

    def show_feature_tools(self):
        self.clear_content()
        self.nav_buttons["百宝箱"].setChecked(True)

        self.feature_tabs = QTabWidget()
        self.feature_tabs.setStyleSheet(TAB_WIDGET_STYLE)

        self.feature_tools_page = FeatureToolsPage()
        self.feature_tabs.addTab(self.feature_tools_page, "特色工具")

        self.current_top_bar = QFrame()
        self.current_top_bar.setStyleSheet(f"background-color: {BACKGROUND_MAIN};")
        top_bar_layout = QHBoxLayout(self.current_top_bar)
        top_bar_layout.setContentsMargins(20, 15, 20, 15)
        top_bar_layout.setSpacing(15)

        top_bar_layout.addStretch()

        self.content_layout.addWidget(self.current_top_bar)
        self.content_layout.addWidget(self.feature_tabs, stretch=1)
        self.current_main_page = self.feature_tabs

    

    def show_system_status(self):
        self.clear_content()
        self.nav_buttons["系统监视器"].setChecked(True)

        self.system_status_page = SystemStatusPage(self.client)
        self.content_layout.addWidget(self.system_status_page, stretch=1)
        self.current_main_page = self.system_status_page



    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec_()


def main():
    import os
    os.environ['QT_XCB_GL_INTEGRATION'] = 'none'
    
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    try:
        from PyQt5.QtGui import QTextCursor
        from PyQt5.QtCore import QMetaType
        QMetaType.registerType(QTextCursor, "QTextCursor")
    except:
        pass
    
    app = QApplication(sys.argv)
    
    app.setStyle("Fusion")
    
    app.setPalette(create_macos_palette())
    
    app.setFont(create_font())
    
    app.setStyleSheet("""
        QWidget {
            font-family: SF Pro Display, PingFang SC, Microsoft YaHei, Arial;
        }
        QToolTip {
            background-color: #333;
            color: white;
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 12px;
        }
    """)

    client = LocalClient()

    window = MainWindow(client)
    window.show()

    ret = app.exec_()
    return ret


if __name__ == '__main__':
    sys.exit(main())
