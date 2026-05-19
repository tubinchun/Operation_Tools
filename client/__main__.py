#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from PyQt5.QtWidgets import QApplication, QMessageBox
from client.gui import MainWindow
from client.client import KylinClient


def main():
    parser = argparse.ArgumentParser(description='银河麒麟运维管理工具 - 客户端')
    parser.add_argument('--host', default='localhost', help='服务器地址 (默认: localhost)')
    parser.add_argument('--port', type=int, default=29876, help='服务器端口 (默认: 29876)')
    args = parser.parse_args()

    from PyQt5.QtCore import Qt
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    client = KylinClient(args.host, args.port)

    if not client.connect():
        QMessageBox.critical(None, "连接失败", f"无法连接到服务器 {args.host}:{args.port}")
        return 1

    window = MainWindow(client)
    window.show()

    ret = app.exec_()
    client.disconnect()
    return ret


if __name__ == '__main__':
    sys.exit(main())
