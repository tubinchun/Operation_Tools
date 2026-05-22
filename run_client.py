#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == '__main__':
    from client.gui import MainWindow, KylinClient
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import Qt

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    client = KylinClient('localhost', 29876)

    if not client.connect():
        QMessageBox.critical(None, "连接失败", "无法连接到本地服务器，请确保服务已启动")
        sys.exit(1)

    window = MainWindow(client)
    window.show()

    ret = app.exec_()
    client.disconnect()
    sys.exit(ret)
