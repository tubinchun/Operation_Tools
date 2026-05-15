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
    QGridLayout, QFrame, QSizePolicy
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
        self._is_destroyed = False
        self.init_ui()
        self.load_system_info()

    def cleanup(self):
        """清理资源，停止线程"""
        self._is_destroyed = True
        for thread in self._threads:
            if thread.isRunning():
                thread.stop()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header_icon = QLabel()
        header_icon.setPixmap(QIcon.fromTheme("computer").pixmap(32, 32))
        header_layout.addWidget(header_icon)
        
        header = QLabel("系统信息")
        header.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        header.setStyleSheet("color: #333;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        main_layout.addWidget(header_widget)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)

        basic_card, basic_layout = self.create_info_card("基本信息", "system")
        
        self.hostname_val = self.create_info_label()
        self.os_name_val = self.create_info_label()
        self.os_version_val = self.create_info_label()
        self.kernel_val = self.create_info_label()
        self.kernel_arch_val = self.create_info_label()
        self.system_bits_val = self.create_info_label()

        basic_layout.addRow(self.create_label("主机名"), self.hostname_val)
        basic_layout.addRow(self.create_label("操作系统"), self.os_name_val)
        basic_layout.addRow(self.create_label("系统版本"), self.os_version_val)
        basic_layout.addRow(self.create_label("内核版本"), self.kernel_val)
        basic_layout.addRow(self.create_label("内核架构"), self.kernel_arch_val)
        basic_layout.addRow(self.create_label("系统位数"), self.system_bits_val)
        grid_layout.addWidget(basic_card, 0, 0)

        hardware_card, hardware_layout = self.create_info_card("硬件信息", "hardware")

        self.manufacturer_val = self.create_info_label()
        self.product_version_val = self.create_info_label()
        self.product_name_val = self.create_info_label()
        self.serial_number_val = self.create_info_label()
        self.cpu_model_val = self.create_info_label()

        hardware_layout.addRow(self.create_label("制造商"), self.manufacturer_val)
        hardware_layout.addRow(self.create_label("版本"), self.product_version_val)
        hardware_layout.addRow(self.create_label("型号"), self.product_name_val)
        hardware_layout.addRow(self.create_label("序列号"), self.serial_number_val)
        hardware_layout.addRow(self.create_label("CPU型号"), self.cpu_model_val)
        grid_layout.addWidget(hardware_card, 0, 1)

        gpu_card, gpu_layout = self.create_info_card("显卡信息", "display")

        self.gpu_name_val = self.create_info_label()
        self.gpu_manufacturer_val = self.create_info_label()
        self.gpu_model_val = self.create_info_label()
        self.gpu_memory_val = self.create_info_label()
        self.gpu_driver_val = self.create_info_label()

        gpu_layout.addRow(self.create_label("显卡名称"), self.gpu_name_val)
        gpu_layout.addRow(self.create_label("制造商"), self.gpu_manufacturer_val)
        gpu_layout.addRow(self.create_label("型号"), self.gpu_model_val)
        gpu_layout.addRow(self.create_label("显存"), self.gpu_memory_val)
        gpu_layout.addRow(self.create_label("驱动"), self.gpu_driver_val)
        grid_layout.addWidget(gpu_card, 1, 0, 1, 2)

        main_layout.addLayout(grid_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        refresh_btn = QPushButton()
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.setText("刷新信息")
        refresh_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        refresh_btn.clicked.connect(self.load_system_info)
        btn_layout.addWidget(refresh_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def create_info_card(self, title, icon_name):
        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM)
        layout.setSpacing(SPACING_MEDIUM)
        
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(SPACING_SMALL)
        
        icon = QLabel()
        icon.setPixmap(QIcon.fromTheme(icon_name).pixmap(20, 20))
        icon.setStyleSheet(f"color: {TEXT_SECONDARY};")
        header_layout.addWidget(icon)
        
        title_label = QLabel(title)
        title_label.setFont(create_font(FONT_SIZE_MEDIUM, "semibold"))
        title_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        content_layout = QFormLayout()
        content_layout.setSpacing(12)
        layout.addLayout(content_layout)
        
        return card, content_layout

    def create_label(self, text):
        label = QLabel(text + ":")
        label.setFont(create_font(FONT_SIZE_NORMAL))
        label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        return label

    def create_info_label(self):
        label = QLabel("加载中...")
        label.setFont(create_font(FONT_SIZE_NORMAL, "medium"))
        label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        return label

    def load_system_info(self):
        def fetch():
            sys_info = self.client.get_system_info()
            hardware_info = self.client.get_hardware_info()
            gpu_info = self.client.get_gpu_info()
            return {'sys': sys_info, 'hardware': hardware_info, 'gpu': gpu_info}

        def on_result(result):
            if self._is_destroyed:
                return
            sys_result = result.get('sys', {})
            if sys_result.get('status') == 'success':
                data = sys_result.get('data', {})
                self.hostname_val.setText(data.get('hostname', '未知'))
                self.os_name_val.setText(data.get('os_name', '银河麒麟桌面操作系统V10 SP1'))
                self.os_version_val.setText(data.get('os_version', '未知'))
                self.kernel_val.setText(data.get('kernel', '未知'))
                self.kernel_arch_val.setText(data.get('architecture', '未知'))
                self.system_bits_val.setText(data.get('bits', '64bit'))

            hardware_result = result.get('hardware', {})
            if hardware_result.get('status') == 'success':
                hardware_data = hardware_result.get('data', {})
                self.manufacturer_val.setText(hardware_data.get('manufacturer', '未知'))
                self.product_version_val.setText(str(hardware_data.get('version', 'None')))
                self.product_name_val.setText(hardware_data.get('product_name', '未知'))
                self.serial_number_val.setText(hardware_data.get('serial_number', '未知'))
                self.cpu_model_val.setText(hardware_data.get('cpu_model', '未知'))

            gpu_result = result.get('gpu', {})
            if gpu_result.get('status') == 'success':
                gpu_data = gpu_result.get('data', {})
                self.gpu_name_val.setText(gpu_data.get('name', '未知'))
                self.gpu_manufacturer_val.setText(gpu_data.get('manufacturer', '未知'))
                self.gpu_model_val.setText(gpu_data.get('model', '未知'))
                self.gpu_memory_val.setText(gpu_data.get('memory', '未知'))
                self.gpu_driver_val.setText(gpu_data.get('driver', '未知'))

        def on_error(error_msg):
            print(f"系统信息加载错误: {error_msg}")

        thread = WorkerThread(fetch)
        thread.finished.connect(on_result)
        thread.error.connect(on_error)
        thread.start()
        self._threads.append(thread)


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
                smooth_path = QPainterPath()
                smooth_path.moveTo(points[0])
                for i in range(1, len(points)):
                    if i < len(points) - 1:
                        prev_point = points[i-1]
                        curr_point = points[i]
                        next_point = points[i+1]
                        
                        cpx1 = curr_point.x() - (next_point.x() - prev_point.x()) / 6
                        cpy1 = curr_point.y() - (next_point.y() - prev_point.y()) / 6
                        cpx2 = curr_point.x() + (next_point.x() - prev_point.x()) / 6
                        cpy2 = curr_point.y() + (next_point.y() - prev_point.y()) / 6
                        
                        smooth_path.cubicTo(QPointF(cpx1, cpy1), QPointF(cpx2, cpy2), next_point)
                    else:
                        smooth_path.lineTo(points[i])
                painter.drawPath(smooth_path)
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

        refresh_btn = QPushButton("刷新")
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        refresh_btn.clicked.connect(self.load_status)
        right_header.addWidget(refresh_btn)
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
            return 'root'

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
            QMessageBox.warning(self, "警告", "请先选择一个用户")
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
            QMessageBox.warning(self, "警告", "请输入密码")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "警告", "两次输入的密码不一致")
            return
        
        def fetch():
            return self.client.reset_user_password(username, password)
        
        def on_result(result):
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
        self._is_destroyed = False
        self.init_ui()
        self.load_kysec_status()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM)
        main_layout.setSpacing(SPACING_MEDIUM)

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header_icon = QLabel()
        header_icon.setPixmap(QIcon.fromTheme("security-high").pixmap(24, 24))
        header_layout.addWidget(header_icon)
        
        header = QLabel("KySec安全管理")
        header.setFont(create_font(FONT_SIZE_LARGE, "semibold"))
        header.setStyleSheet(f"color: {TEXT_PRIMARY};")
        header_layout.addWidget(header)
        header_layout.addStretch()
        main_layout.addWidget(header_widget)

        kysec_card = QFrame()
        kysec_card.setStyleSheet(CARD_STYLE)
        kysec_layout = QVBoxLayout(kysec_card)
        kysec_layout.setContentsMargins(SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM)
        kysec_layout.setSpacing(SPACING_MEDIUM)

        kysec_header = QLabel("KySec 安全状态")
        kysec_header.setFont(create_font(FONT_SIZE_LARGE, "medium"))
        kysec_header.setStyleSheet(f"color: {TEXT_PRIMARY};")
        kysec_layout.addWidget(kysec_header)

        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(SPACING_MEDIUM)

        status_label = QLabel("当前状态:")
        status_label.setFont(create_font(FONT_SIZE_NORMAL))
        status_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        status_layout.addWidget(status_label)

        self.kysec_status_label = QLabel("加载中...")
        self.kysec_status_label.setFont(create_font(FONT_SIZE_LARGE, "bold"))
        status_layout.addWidget(self.kysec_status_label)
        status_layout.addStretch()
        kysec_layout.addWidget(status_frame)

        status_detail = QFrame()
        status_detail_layout = QFormLayout(status_detail)
        status_detail_layout.setContentsMargins(0, 0, 0, 0)
        status_detail_layout.setSpacing(SPACING_SMALL)

        raw_label = QLabel("原始输出:")
        raw_label.setFont(create_font(FONT_SIZE_NORMAL))
        raw_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        status_detail_layout.addRow(raw_label)

        self.kysec_raw = QTextEdit()
        self.kysec_raw.setReadOnly(True)
        self.kysec_raw.setMaximumHeight(100)
        self.kysec_raw.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BACKGROUND_SECONDARY};
                border-radius: {CORNER_BUTTON}px;
                border: 1px solid {DIVIDER};
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: {FONT_SIZE_SMALL}px;
                color: {TEXT_PRIMARY};
            }}
        """)
        self.kysec_raw.setPlaceholderText("命令原始输出将显示在这里")
        status_detail_layout.addRow(self.kysec_raw)
        kysec_layout.addWidget(status_detail)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        refresh_btn = QPushButton()
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.setText("刷新状态")
        refresh_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        refresh_btn.clicked.connect(self.load_kysec_status)
        btn_layout.addWidget(refresh_btn)

        self.enable_btn = QPushButton()
        self.enable_btn.setIcon(QIcon.fromTheme("check"))
        self.enable_btn.setText("开启")
        self.enable_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.enable_btn.clicked.connect(lambda: self.set_kysec('enable'))
        btn_layout.addWidget(self.enable_btn)

        self.disable_btn = QPushButton()
        self.disable_btn.setIcon(QIcon.fromTheme("x"))
        self.disable_btn.setText("关闭")
        self.disable_btn.setStyleSheet(DANGER_BUTTON_STYLE)
        self.disable_btn.clicked.connect(lambda: self.set_kysec('disable'))
        btn_layout.addWidget(self.disable_btn)

        kysec_layout.addLayout(btn_layout)

        main_layout.addWidget(kysec_card)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def load_kysec_status(self):
        def fetch():
            return self.client.get_kysec_status()

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                data = result.get('data', {})
                status = data.get('kysec', '未知').strip()
                raw_output = data.get('raw', '')
                
                if status.lower() == 'disabled':
                    self.kysec_status_label.setText("disabled")
                    self.kysec_status_label.setStyleSheet(f"color: {MAC_RED}; font-weight: bold; font-size: 16px; padding: 4px 12px; background-color: {BACKGROUND_SECONDARY}; border-radius: 8px;")
                    self.enable_btn.setEnabled(True)
                    self.disable_btn.setEnabled(False)
                elif status.lower() == 'enabled':
                    self.kysec_status_label.setText("enabled")
                    self.kysec_status_label.setStyleSheet(f"color: {MAC_GREEN}; font-weight: bold; font-size: 16px; padding: 4px 12px; background-color: {BACKGROUND_SECONDARY}; border-radius: 8px;")
                    self.enable_btn.setEnabled(False)
                    self.disable_btn.setEnabled(True)
                else:
                    self.kysec_status_label.setText(status)
                    self.kysec_status_label.setStyleSheet(f"color: {MAC_ORANGE}; font-weight: bold; font-size: 16px; padding: 4px 12px; background-color: {BACKGROUND_SECONDARY}; border-radius: 8px;")
                    self.enable_btn.setEnabled(True)
                    self.disable_btn.setEnabled(True)
                
                self.kysec_raw.setPlainText(raw_output if raw_output else "无原始输出")

        self.thread = WorkerThread(fetch)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def set_kysec(self, action):
        def do_set():
            return self.client.set_kysec(action)

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                message = f"KySec 已{action}"
                if result.get('need_reboot'):
                    message += "\n\n注意：设置需要重启系统后才生效"
                QMessageBox.information(self, "成功", message)
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
        self.current_logs = []
        self.current_log_type = 'system'
        self._threads = []
        self._is_destroyed = False
        self.init_ui()
        self.load_and_analyze_logs()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {BACKGROUND_SECONDARY};
                border-right: 1px solid {DIVIDER};
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        sidebar_header = QFrame()
        sidebar_header.setStyleSheet(f"background-color: {MAC_BLUE};")
        header_layout = QVBoxLayout(sidebar_header)
        header_layout.setContentsMargins(20, 20, 20, 20)
        
        header_title = QLabel("日志查看器")
        header_title.setFont(create_font(FONT_SIZE_MEDIUM, "semibold"))
        header_title.setStyleSheet("color: white;")
        header_layout.addWidget(header_title)
        
        count_label = QLabel("12076 条日志")
        count_label.setFont(create_font(FONT_SIZE_SMALL))
        count_label.setStyleSheet("color: rgba(255,255,255,0.8);")
        header_layout.addWidget(count_label)
        sidebar_layout.addWidget(sidebar_header)

        self.nav_buttons = {}
        nav_items = [
            ("系统日志", "system-log", True),
            ("启动日志", "system-boot"),
            ("登录日志", "system-users"),
            ("应用日志", "application-x-executable"),
            ("麒麟安全", "security-high"),
            ("溯源日志", "history"),
            ("审计日志", "file-text"),
        ]
        
        for name, icon_name, default_active in [(item[0], item[1], item[2] if len(item) > 2 else False) for item in nav_items]:
            btn = QPushButton()
            btn.setIcon(QIcon.fromTheme(icon_name))
            btn.setText(name)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {TEXT_SECONDARY};
                    border: none;
                    text-align: left;
                    padding: 12px 20px;
                    font-family: {FONT_FAMILY};
                    font-size: {FONT_SIZE_NORMAL}px;
                    border-left: 3px solid transparent;
                }}
                QPushButton:hover {{
                    background-color: {BACKGROUND_HOVER};
                    color: {TEXT_PRIMARY};
                }}
                QPushButton:checked {{
                    background-color: {BACKGROUND_MAIN};
                    color: {MAC_BLUE};
                    border-left: 3px solid {MAC_BLUE};
                }}
            """)
            btn.setCheckable(True)
            btn.setChecked(default_active)
            btn.clicked.connect(lambda checked, n=name: self.on_nav_click(n))
            self.nav_buttons[name] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar)

        content = QFrame()
        content.setStyleSheet(f"background-color: {BACKGROUND_MAIN};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QFrame()
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(20, 15, 20, 15)
        top_bar_layout.setSpacing(15)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索")
        self.search_input.setStyleSheet(LINE_EDIT_STYLE)
        self.search_input.setFixedWidth(300)
        search_action = QAction(QIcon.fromTheme("search"), "", self.search_input)
        self.search_input.addAction(search_action, QLineEdit.LeadingPosition)
        top_bar_layout.addWidget(self.search_input)

        self.level_tags = []
        level_items = [("全部", "all"), ("正常", "INFO"), ("错误", "ERROR"), ("注意", "WARNING")]
        for label, level in level_items:
            tag = QPushButton(label)
            tag.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BACKGROUND_SECONDARY};
                    color: {TEXT_SECONDARY};
                    border: none;
                    border-radius: 16px;
                    padding: 6px 16px;
                    font-family: {FONT_FAMILY};
                    font-size: {FONT_SIZE_SMALL}px;
                }}
                QPushButton:hover {{
                    background-color: {BACKGROUND_HOVER};
                }}
                QPushButton:checked {{
                    background-color: {MAC_BLUE};
                    color: white;
                }}
            """)
            tag.setCheckable(True)
            tag.setChecked(level == "all")
            tag.clicked.connect(lambda checked, l=level: self.on_level_filter(l))
            self.level_tags.append((tag, level))
            top_bar_layout.addWidget(tag)

        top_bar_layout.addStretch()

        self.date_from = QLineEdit()
        self.date_from.setPlaceholderText("2026/05/14 00:00:00")
        self.date_from.setStyleSheet(LINE_EDIT_STYLE)
        self.date_from.setFixedWidth(150)
        top_bar_layout.addWidget(self.date_from)

        top_bar_layout.addWidget(QLabel("-"))

        self.date_to = QLineEdit()
        self.date_to.setPlaceholderText("2026/05/14 23:59:59")
        self.date_to.setStyleSheet(LINE_EDIT_STYLE)
        self.date_to.setFixedWidth(150)
        top_bar_layout.addWidget(self.date_to)

        refresh_btn = QPushButton()
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {BACKGROUND_HOVER};
                border-radius: {CORNER_BUTTON}px;
            }}
        """)
        refresh_btn.clicked.connect(self.load_and_analyze_logs)
        top_bar_layout.addWidget(refresh_btn)
        content_layout.addWidget(top_bar)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["级别", "时间", "进程", "信息"])
        self.log_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BACKGROUND_MAIN};
                border: none;
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_SMALL}px;
            }}
            QHeaderView::section {{
                background-color: {BACKGROUND_SECONDARY};
                padding: 10px;
                border: none;
                border-bottom: 1px solid {DIVIDER};
                font-weight: 500;
                color: {TEXT_SECONDARY};
                text-align: left;
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {DIVIDER};
            }}
            QTableWidget::item:hover {{
                background-color: {BACKGROUND_HOVER};
            }}
        """)
        self.log_table.horizontalHeader().setStretchLastSection(True)
        self.log_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.log_table.setShowGrid(False)
        content_layout.addWidget(self.log_table, stretch=1)

        main_layout.addWidget(content, stretch=1)
        self.setLayout(main_layout)

    def on_nav_click(self, name):
        for btn_name, btn in self.nav_buttons.items():
            btn.setChecked(btn_name == name)
        
        type_mapping = {
            '系统日志': 'system',
            '启动日志': 'boot',
            '登录日志': 'login',
            '应用日志': 'application',
            '麒麟安全': 'security',
            '溯源日志': 'trace',
            '审计日志': 'audit',
        }
        self.current_log_type = type_mapping.get(name, 'system')
        self.load_and_analyze_logs()

    def on_level_filter(self, level):
        for tag, lvl in self.level_tags:
            tag.setChecked(lvl == level)
        self.apply_filters()

    def create_stat_widget(self, label, icon_name, color):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        icon = QLabel()
        icon.setPixmap(QIcon.fromTheme(icon_name).pixmap(20, 20))
        icon.setStyleSheet(f"color: {color};")
        layout.addWidget(icon, alignment=Qt.AlignCenter)

        count = QLabel("0")
        count.setFont(create_font(FONT_SIZE_LARGE, "bold"))
        count.setStyleSheet(f"color: {color};")
        layout.addWidget(count, alignment=Qt.AlignCenter)

        label_lbl = QLabel(label)
        label_lbl.setFont(create_font(FONT_SIZE_SMALL))
        label_lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(label_lbl, alignment=Qt.AlignCenter)

        return widget

    def load_and_analyze_logs(self):
        def fetch():
            return self.client.get_log_by_type(self.current_log_type, 500)

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                logs = result.get('data', {}).get('logs', '')
                self.analyze_and_display(logs)

        self.thread = WorkerThread(fetch)
        self._threads.append(self.thread)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def analyze_and_display(self, logs):
        if self._is_destroyed:
            return
        filters = self.get_current_filters()
        result = self.client.analyze_logs(logs, filters)
        
        if result.get('status') == 'success':
            data = result.get('data', {})
            self.current_logs = data.get('error_logs', []) + data.get('warning_logs', []) + data.get('info_logs', []) + data.get('other_logs', [])
            self.update_log_table(data)

    def get_current_filters(self):
        if self._is_destroyed:
            return {}
        level_filter = "all"
        for tag, level in self.level_tags:
            try:
                if tag.isChecked():
                    level_filter = level
                    break
            except RuntimeError:
                break
        
        keyword = ""
        try:
            keyword = self.search_input.text().strip()
        except RuntimeError:
            pass
        
        filters = {}
        if level_filter != 'all':
            filters['level'] = level_filter
        
        if keyword:
            filters['keywords'] = [keyword]
        
        return filters

    def apply_filters(self):
        def fetch():
            return self.client.get_system_logs(500)

        def on_result(result):
            if self._is_destroyed:
                return
            if result.get('status') == 'success':
                logs = result.get('data', {}).get('logs', '')
                self.analyze_and_display(logs)

        self.thread = WorkerThread(fetch)
        self._threads.append(self.thread)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def reset_filters(self):
        self.search_input.clear()
        for tag, level in self.level_tags:
            tag.setChecked(level == "all")
        self.apply_filters()

    def update_log_table(self, data):
        self.log_table.setRowCount(0)
        
        all_logs = []
        all_logs.extend(data.get('info_logs', []))
        all_logs.extend(data.get('warning_logs', []))
        all_logs.extend(data.get('error_logs', []))
        all_logs.extend(data.get('other_logs', []))
        
        for log in all_logs:
            row = self.log_table.rowCount()
            self.log_table.insertRow(row)
            
            level = 'ERROR' if log.get('is_error') else 'WARNING' if log.get('is_warning') else 'INFO'
            
            level_item = QTableWidgetItem()
            icon_label = QLabel()
            if level == 'ERROR':
                icon_label.setPixmap(QIcon.fromTheme("dialog-error").pixmap(16, 16))
                icon_label.setStyleSheet(f"color: {MAC_RED};")
            elif level == 'WARNING':
                icon_label.setPixmap(QIcon.fromTheme("dialog-warning").pixmap(16, 16))
                icon_label.setStyleSheet(f"color: {MAC_ORANGE};")
            else:
                icon_label.setPixmap(QIcon.fromTheme("dialog-information").pixmap(16, 16))
                icon_label.setStyleSheet(f"color: {MAC_GREEN};")
            self.log_table.setCellWidget(row, 0, icon_label)
            
            timestamp = log.get('timestamp', '')
            self.log_table.setItem(row, 1, QTableWidgetItem(timestamp))
            
            process = log.get('process', '')
            self.log_table.setItem(row, 2, QTableWidgetItem(process))
            
            message = log.get('message', '')[:150] + '...' if len(log.get('message', '')) > 150 else log.get('message', '')
            self.log_table.setItem(row, 3, QTableWidgetItem(message))
        
        self.log_table.resizeColumnsToContents()
        self.log_table.setColumnWidth(0, 40)
        self.log_table.setColumnWidth(1, 160)
        self.log_table.setColumnWidth(2, 120)

    def show_export_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("导出日志")
        dialog.setFixedSize(350, 180)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM)
        layout.setSpacing(SPACING_MEDIUM)
        
        format_label = QLabel("导出格式:")
        format_label.setFont(create_font(FONT_SIZE_NORMAL))
        format_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(format_label)
        
        format_combo = QComboBox()
        format_combo.addItems(['TXT', 'JSON', 'CSV'])
        format_combo.setStyleSheet(LINE_EDIT_STYLE)
        layout.addWidget(format_combo)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("导出")
        ok_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        ok_btn.clicked.connect(lambda: self.export_logs(format_combo.currentText().lower(), dialog))
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        dialog.exec_()

    def export_logs(self, format_type, dialog):
        if not self.current_logs:
            QMessageBox.warning(self, "警告", "没有可导出的日志")
            return
        
        result = self.client.export_logs(self.current_logs, format_type)
        
        if result.get('status') == 'success':
            path = result.get('data', {}).get('path', '')
            QMessageBox.information(self, "成功", f"日志已导出到:\n{path}")
            dialog.accept()
        else:
            QMessageBox.error(self, "错误", result.get('message', '导出失败'))

    def cleanup_logs(self):
        if QMessageBox.question(self, "确认清理", "确定要清理系统日志吗？", 
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
            return
        
        def do_cleanup():
            return self.client.cleanup_logs()

        def on_result(result):
            if result.get('status') == 'success':
                QMessageBox.information(self, "成功", "日志清理完成")
                self.load_and_analyze_logs()
            else:
                QMessageBox.error(self, "错误", result.get('message', '清理失败'))

        self.thread = WorkerThread(fetch=do_cleanup)
        self._threads.append(self.thread)
        self.thread.finished.connect(on_result)
        self.thread.start()

    def cleanup(self):
        self._is_destroyed = True
        for t in self._threads:
            t.stop()
        self._threads = []


class HostsEditorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("自定义本地域名解析文件")
        self.setFixedSize(700, 500)
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
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BACKGROUND_SECONDARY};
                border: 1px solid {DIVIDER};
                border-radius: {CORNER_BUTTON}px;
                padding: 12px;
                color: {TEXT_PRIMARY};
            }}
        """)
        main_layout.addWidget(self.text_edit)

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
            QMessageBox.warning(self, "警告", f"无法读取 hosts 文件: {str(e)}")
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
        self.status_label.setText("已恢复到默认内容（可点击保存）")

    def save_hosts(self):
        new_content = self.text_edit.toPlainText()
        
        if new_content == self.backup_content and not self.force_restore:
            QMessageBox.information(self, "提示", "内容未发生变化")
            return

        try:
            import subprocess
            result = subprocess.run(
                ['sudo', 'cp', self.hosts_path, f'{self.hosts_path}.bak'],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                QMessageBox.warning(self, "警告", "无法创建备份文件")
            
            result = subprocess.run(
                ['sudo', 'bash', '-c', f'cat > {self.hosts_path} << "EOF"\n{new_content}\nEOF'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                self.history.append(self.backup_content)
                self.backup_content = new_content
                self.force_restore = False
                self.status_label.setText("保存成功")
                QMessageBox.information(self, "成功", "hosts 文件已更新")
                self.accept()
            else:
                error_msg = result.stderr if result.stderr else "保存失败"
                QMessageBox.error(self, "错误", f"保存失败: {error_msg}")
                
        except Exception as e:
            QMessageBox.error(self, "错误", f"保存失败: {str(e)}")


class PrinterRepairDialog(QDialog):
    status_signal = pyqtSignal(str, str)
    finished_signal = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修复打印机无法启动")
        self.setFixedSize(600, 450)
        self.setStyleSheet(f"background-color: {BACKGROUND_MAIN};")
        self.is_repairing = False
        self.init_ui()
        self.status_signal.connect(self.append_status)
        self.finished_signal.connect(self.on_repair_finished)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        header_icon = QLabel()
        header_icon.setPixmap(QIcon.fromTheme("printer").pixmap(48, 48))
        header_icon.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_icon)

        title_label = QLabel("修复打印机无法启动")
        title_label.setFont(create_font(FONT_SIZE_LARGE, "semibold"))
        title_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        desc_label = QLabel("本工具将修复 CUPS 打印机服务配置问题。\n执行修复前请确保已连接网络。")
        desc_label.setFont(create_font(FONT_SIZE_NORMAL))
        desc_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setFont(QFont("Consolas", 10))
        self.status_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BACKGROUND_SECONDARY};
                border: 1px solid {DIVIDER};
                border-radius: {CORNER_BUTTON}px;
                padding: 12px;
                color: {TEXT_PRIMARY};
            }}
        """)
        main_layout.addWidget(self.status_text, stretch=1)

        self.result_label = QLabel("")
        self.result_label.setFont(create_font(FONT_SIZE_NORMAL, "medium"))
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet(f"color: {MAC_GREEN}; padding: 8px;")
        main_layout.addWidget(self.result_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.repair_btn = QPushButton("开始修复")
        self.repair_btn.setIcon(QIcon.fromTheme("system-run"))
        self.repair_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.repair_btn.setMinimumWidth(120)
        self.repair_btn.clicked.connect(self.start_repair)
        btn_layout.addWidget(self.repair_btn)

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        close_btn.setMinimumWidth(80)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    @pyqtSlot(str, str)
    def append_status(self, text, color=None):
        if color:
            self.status_text.append(f'<span style="color: {color}">{text}</span>')
        else:
            self.status_text.append(text)
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )

    def start_repair(self):
        if self.is_repairing:
            return

        self.is_repairing = True
        self.repair_btn.setEnabled(False)
        self.result_label.setText("")
        self.result_label.setStyleSheet(f"color: {MAC_ORANGE}; padding: 8px;")
        self.result_label.setText("正在修复中，请稍候...")
        self.status_text.clear()
        self.status_signal.emit("开始修复打印机服务...", None)
        self.status_signal.emit("-" * 50, TEXT_SECONDARY)

        def do_repair():
            results = []
            
            self.status_signal.emit("步骤 1: 备份并恢复 CUPS 配置文件...", None)
            result1 = subprocess.run(
                ['sudo', 'cp', '/usr/share/cups/cupsd.conf.default', '/etc/cups/cupsd.conf'],
                capture_output=True, text=True
            )
            if result1.returncode == 0:
                self.status_signal.emit("✓ CUPS 配置文件已恢复", MAC_GREEN)
                results.append(True)
            else:
                self.status_signal.emit("✗ CUPS 配置文件恢复失败: " + (result1.stderr or "未知错误"), MAC_RED)
                results.append(False)

            self.status_signal.emit("", None)
            self.status_signal.emit("步骤 2: 重启 CUPS 服务...", None)
            result2 = subprocess.run(
                ['sudo', 'systemctl', 'restart', 'cups'],
                capture_output=True, text=True
            )
            if result2.returncode == 0:
                self.status_signal.emit("✓ CUPS 服务已重启", MAC_GREEN)
                results.append(True)
            else:
                self.status_signal.emit("✗ CUPS 服务重启失败: " + (result2.stderr or "未知错误"), MAC_RED)
                results.append(False)

            self.status_signal.emit("", None)
            self.status_signal.emit("-" * 50, TEXT_SECONDARY)
            
            if all(results):
                self.status_signal.emit("✓ 打印机服务修复完成！", MAC_GREEN)
                self.finished_signal.emit({'status': 'success', 'message': '打印机服务修复成功'})
            else:
                self.status_signal.emit("✗ 修复过程中出现错误，请检查上述信息", MAC_RED)
                self.finished_signal.emit({'status': 'error', 'message': '修复过程中出现错误'})

        self.thread = WorkerThread(do_repair)
        self.thread.finished.connect(lambda r: None)
        self.thread.start()

    def on_repair_finished(self, result):
        self.is_repairing = False
        self.repair_btn.setEnabled(True)
        
        if result.get('status') == 'success':
            self.result_label.setText("✓ 修复成功！")
            self.result_label.setStyleSheet(f"color: {MAC_GREEN}; padding: 8px; font-weight: bold;")
            QMessageBox.information(self, "成功", "打印机服务修复成功！\n请尝试重新连接打印机。")
        else:
            self.result_label.setText("✗ 修复失败")
            self.result_label.setStyleSheet(f"color: {MAC_RED}; padding: 8px;")
            QMessageBox.warning(self, "警告", result.get('message', '修复失败，请检查错误信息'))


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

        printer_card = ToolCard("printer", "修复打印机无法启动", "修复 CUPS 打印机服务配置问题", "#5AC8FA")
        printer_card.clicked.connect(self.open_printer_repair)
        grid_layout.addWidget(printer_card, 0, 1)

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

    def open_printer_repair(self):
        dialog = PrinterRepairDialog(self)
        dialog.exec_()


class MainWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.setWindowTitle("Kylinos-Desktop-Tools")
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

        logo_label = QLabel("Kylinos-Desktop-Tools")
        logo_label.setFont(create_font(FONT_SIZE_LARGE, "bold"))
        logo_label.setStyleSheet("color: #FFFFFF;")
        logo_layout.addWidget(logo_label)

        sidebar_layout.addWidget(logo_frame)

        nav_items = [
            ("系统监视器", "server"),
            ("日志查看器", "wrench"),
            ("KySec安全管理", "security-high"),
            ("设备管理", "computer"),
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
        elif name == "日志查看器":
            self.show_log_page()
        elif name == "KySec安全管理":
            self.show_security_page()
        elif name == "设备管理":
            self.show_system_info()

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

        search_input = QLineEdit()
        search_input.setPlaceholderText("搜索")
        search_input.setStyleSheet(LINE_EDIT_STYLE)
        search_input.setFixedWidth(250)
        search_action = QAction(QIcon.fromTheme("search"), "", search_input)
        search_input.addAction(search_action, QLineEdit.LeadingPosition)
        top_bar_layout.addWidget(search_input)
        top_bar_layout.addStretch()

        self.content_layout.addWidget(self.current_top_bar)
        self.content_layout.addWidget(self.feature_tabs, stretch=1)
        self.current_main_page = self.feature_tabs

    def show_system_info(self):
        self.clear_content()
        self.nav_buttons["设备管理"].setChecked(True)

        self.system_info_page = SystemInfoPage(self.client)
        self.content_layout.addWidget(self.system_info_page, stretch=1)
        self.current_main_page = self.system_info_page

    def show_system_status(self):
        self.clear_content()
        self.nav_buttons["系统监视器"].setChecked(True)

        self.system_status_page = SystemStatusPage(self.client)
        self.content_layout.addWidget(self.system_status_page, stretch=1)
        self.current_main_page = self.system_status_page

    def show_log_page(self):
        self.clear_content()
        self.nav_buttons["日志查看器"].setChecked(True)

        self.log_page = LogPage(self.client)
        self.content_layout.addWidget(self.log_page, stretch=1)
        self.current_main_page = self.log_page

    def show_security_page(self):
        self.clear_content()
        self.nav_buttons["KySec安全管理"].setChecked(True)

        self.security_page = SecurityPage(self.client)
        self.content_layout.addWidget(self.security_page, stretch=1)
        self.current_main_page = self.security_page

    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec_()


def main():
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