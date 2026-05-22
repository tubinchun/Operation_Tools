#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from server.server import KylinServer, KylinServerCommands


def main():
    parser = argparse.ArgumentParser(description='麒麟运维百宝箱 - 服务端')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=29876, help='监听端口 (默认: 29876)')
    args = parser.parse_args()

    server = KylinServer(host=args.host, port=args.port)

    server.register_handler('get_system_info', KylinServerCommands.get_system_info)
    server.register_handler('get_cpu_info', KylinServerCommands.get_cpu_info)
    server.register_handler('get_memory_info', KylinServerCommands.get_memory_info)
    server.register_handler('get_disk_info', KylinServerCommands.get_disk_info)
    server.register_handler('get_network_info', KylinServerCommands.get_network_info)
    server.register_handler('get_process_list', KylinServerCommands.get_process_list)
    server.register_handler('get_service_list', KylinServerCommands.get_service_list)
    server.register_handler('restart_network', KylinServerCommands.restart_network)
    server.register_handler('execute_command', KylinServerCommands.execute_command)
    server.register_handler('get_kysec_status', KylinServerCommands.get_kysec_status)
    server.register_handler('set_kysec', KylinServerCommands.set_kysec)
    server.register_handler('get_users', KylinServerCommands.get_users)
    server.register_handler('get_login_history', KylinServerCommands.get_login_history)
    server.register_handler('get_apt_sources', KylinServerCommands.get_apt_sources)
    server.register_handler('get_installed_packages', KylinServerCommands.get_installed_packages)
    server.register_handler('cleanup_logs', KylinServerCommands.cleanup_logs)
    server.register_handler('get_system_logs', KylinServerCommands.get_system_logs)

    print(f"麒麟运维百宝箱服务端启动中...")
    print(f"监听地址: {args.host}:{args.port}")

    try:
        server.start()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        server.stop()


if __name__ == '__main__':
    main()
