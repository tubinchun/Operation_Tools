#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能验证脚本 - 测试整合后的核心模块
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.commands import SystemCommands


def test_command(name, func, *args, **kwargs):
    """测试单个命令"""
    try:
        result = func(*args, **kwargs)
        if result.get('status') == 'success':
            print(f"✓ {name}")
            return True
        else:
            print(f"✗ {name} - {result.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"✗ {name} - Exception: {e}")
        return False


def main():
    print("=" * 60)
    print("银河麒麟运维管理工具 - 功能验证")
    print("=" * 60)
    print()

    tests = [
        ("系统信息", SystemCommands.get_system_info),
        ("CPU信息", SystemCommands.get_cpu_info),
        ("内存信息", SystemCommands.get_memory_info),
        ("磁盘信息", SystemCommands.get_disk_info),
        ("网络信息", SystemCommands.get_network_info),
        ("进程列表", SystemCommands.get_process_list, 10),
        ("服务列表", SystemCommands.get_service_list),
        ("用户列表", SystemCommands.get_users),
        ("登录历史", SystemCommands.get_login_history),
        ("APT源", SystemCommands.get_apt_sources),
        ("系统日志", SystemCommands.get_system_logs, 50),
        ("系统统计", SystemCommands.get_system_stats),
    ]

    passed = 0
    failed = 0

    print("测试核心命令模块:")
    print("-" * 40)

    for test in tests:
        name = test[0]
        func = test[1]
        args = test[2:] if len(test) > 2 else ()
        
        if test_command(name, func, *args):
            passed += 1
        else:
            failed += 1

    print("-" * 40)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print()

    if failed == 0:
        print("✓ 所有核心功能验证通过！")
        return 0
    else:
        print("✗ 部分功能验证失败，请检查相关模块")
        return 1


if __name__ == '__main__':
    sys.exit(main())