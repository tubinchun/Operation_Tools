#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
银河麒麟运维管理工具 - 整合版主入口
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import main


if __name__ == '__main__':
    sys.exit(main())