#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
苹果风格UI样式定义 - 遵循 Human Interface Guidelines
"""

from PyQt5.QtGui import QColor, QPalette, QFont

# ==================== 颜色常量 ====================

# 主色调
MAC_BLUE = "#007AFF"
MAC_GREEN = "#34C759"
MAC_RED = "#FF3B30"
MAC_ORANGE = "#FF9500"
MAC_PURPLE = "#AF52DE"

# 中性色
TEXT_PRIMARY = "#1C1C1E"
TEXT_SECONDARY = "#8E8E93"
TEXT_DISABLED = "#C7C7CC"
DIVIDER = "#EFEFF4"
BACKGROUND_MAIN = "#FFFFFF"
BACKGROUND_SECONDARY = "#F5F5F7"
BACKGROUND_HOVER = "#F0F0F2"

# ==================== 字体常量 ====================

FONT_FAMILY = "SF Pro Display, PingFang SC, Microsoft YaHei, Arial"
FONT_SIZE_SMALL = 12
FONT_SIZE_NORMAL = 13
FONT_SIZE_MEDIUM = 14
FONT_SIZE_LARGE = 16
FONT_SIZE_XLARGE = 18

# ==================== 间距常量 ====================

SPACING_TINY = 4
SPACING_SMALL = 8
SPACING_MEDIUM = 16
SPACING_LARGE = 24
SPACING_XLARGE = 32

# ==================== 圆角常量 ====================

CORNER_BUTTON = 8
CORNER_CARD = 12
CORNER_DIALOG = 16

# ==================== 样式表 ====================

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

# 输入框样式
LINE_EDIT_STYLE = f"""
QLineEdit {{
    background-color: {BACKGROUND_SECONDARY};
    border: none;
    border-radius: {CORNER_BUTTON}px;
    padding: 10px 12px;
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_NORMAL}px;
    min-height: 36px;
}}
QLineEdit:focus {{
    border: 2px solid {MAC_BLUE};
    background-color: {BACKGROUND_MAIN};
}}
QLineEdit::placeholder {{
    color: {TEXT_DISABLED};
}}
"""

# 标签页样式
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

# 文本编辑样式
TEXT_EDIT_STYLE = f"""
QTextEdit {{
    background-color: {BACKGROUND_MAIN};
    border: 1px solid {DIVIDER};
    border-radius: {CORNER_BUTTON}px;
    padding: 12px;
    font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
    font-size: {FONT_SIZE_SMALL}px;
    color: {TEXT_PRIMARY};
}}
QTextEdit:focus {{
    border-color: {MAC_BLUE};
}}
"""

# 列表视图样式
LIST_WIDGET_STYLE = f"""
QListWidget {{
    background-color: {BACKGROUND_MAIN};
    border: 1px solid {DIVIDER};
    border-radius: {CORNER_BUTTON}px;
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_NORMAL}px;
}}
QListWidget::item {{
    padding: 12px;
    border-bottom: 1px solid {DIVIDER};
}}
QListWidget::item:last-child {{
    border-bottom: none;
}}
QListWidget::item:hover {{
    background-color: {BACKGROUND_HOVER};
}}
QListWidget::item:selected {{
    background-color: rgba(0, 122, 255, 0.1);
    color: {MAC_BLUE};
}}
"""

# 表格视图样式
TABLE_WIDGET_STYLE = f"""
QTableWidget {{
    background-color: {BACKGROUND_MAIN};
    border: 1px solid {DIVIDER};
    border-radius: {CORNER_BUTTON}px;
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_SMALL}px;
    gridline-color: {DIVIDER};
}}
QTableWidget::item {{
    padding: 8px 12px;
    border: none;
}}
QTableWidget::item:hover {{
    background-color: {BACKGROUND_HOVER};
}}
QTableWidget::item:selected {{
    background-color: rgba(0, 122, 255, 0.1);
    color: {MAC_BLUE};
}}
QHeaderView::section {{
    background-color: {BACKGROUND_SECONDARY};
    color: {TEXT_SECONDARY};
    padding: 10px 12px;
    font-weight: 500;
    border: none;
    border-bottom: 1px solid {DIVIDER};
}}
"""

# 进度条样式
PROGRESS_BAR_STYLE = f"""
QProgressBar {{
    background-color: {BACKGROUND_SECONDARY};
    border: none;
    border-radius: 4px;
    height: 6px;
}}
QProgressBar::chunk {{
    background-color: {MAC_GREEN};
    border-radius: 4px;
}}
"""

# 窗口背景样式
WINDOW_STYLE = f"""
QMainWindow {{
    background-color: {BACKGROUND_SECONDARY};
}}
"""

# ==================== 字体工厂函数 ====================

def create_font(size=FONT_SIZE_NORMAL, weight="normal"):
    """创建指定大小和字重的字体"""
    font = QFont(FONT_FAMILY, size)
    if weight == "bold":
        font.setWeight(QFont.Bold)
    elif weight == "medium":
        font.setWeight(QFont.Medium)
    elif weight == "semibold":
        font.setWeight(QFont.DemiBold)
    return font

# ==================== 调色板工厂函数 ====================

def create_macos_palette():
    """创建苹果风格调色板"""
    palette = QPalette()
    
    # 窗口背景
    palette.setColor(QPalette.Window, QColor(BACKGROUND_SECONDARY))
    palette.setColor(QPalette.WindowText, QColor(TEXT_PRIMARY))
    
    # 按钮
    palette.setColor(QPalette.Button, QColor(BACKGROUND_MAIN))
    palette.setColor(QPalette.ButtonText, QColor(TEXT_PRIMARY))
    
    # 高亮
    palette.setColor(QPalette.Highlight, QColor(MAC_BLUE))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    
    # 文本
    palette.setColor(QPalette.Text, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Foreground, QColor(TEXT_PRIMARY))
    
    # 提示文本
    palette.setColor(QPalette.PlaceholderText, QColor(TEXT_DISABLED))
    
    return palette
