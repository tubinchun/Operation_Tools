#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麒麟运维百宝箱 - 整合版主入口
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import main


if __name__ == '__main__':
    sys.exit(main())