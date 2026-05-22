#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import json
import logging
import os
import platform
import random
import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MockServer')


class MockServerProtocol:
    VERSION = "1.0.3"
    HEADER_SIZE = 8

    @staticmethod
    def pack_message(data: dict) -> bytes:
        json_data = json.dumps(data, ensure_ascii=False)
        json_bytes = json_data.encode('utf-8')
        length = len(json_bytes)
        header = length.to_bytes(MockServerProtocol.HEADER_SIZE, 'big')
        return header + json_bytes

    @staticmethod
    def unpack_message(stream) -> dict:
        header = stream.read(MockServerProtocol.HEADER_SIZE)
        if not header or len(header) < MockServerProtocol.HEADER_SIZE:
            return None
        length = int.from_bytes(header, 'big')
        json_bytes = b''
        while len(json_bytes) < length:
            chunk = stream.read(length - len(json_bytes))
            if not chunk:
                return None
            json_bytes += chunk
        return json.loads(json_bytes.decode('utf-8'))


class MockServer:
    def __init__(self, host='0.0.0.0', port=29876):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.client_id = 0
        self.handlers = {}

    def register_handler(self, command: str, handler: callable):
        self.handlers[command] = handler

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(50)
            self.running = True
            logger.info(f"Mock Server started on {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Bind failed: {e}")
            return

        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                logger.info(f"Client connected: {address}")
                self.client_id += 1
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address, self.client_id)
                )
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.running:
                    logger.error(f"Accept error: {e}")
                    break

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        logger.info("Server stopped")

    def _handle_client(self, client_socket, address, client_id):
        try:
            stream = client_socket.makefile('rwb')
            while self.running:
                try:
                    request = MockServerProtocol.unpack_message(stream)
                    if request is None:
                        break

                    command = request.get('command', '')
                    params = request.get('params', {})

                    logger.info(f"Client {client_id} command: {command}")

                    if command in self.handlers:
                        result = self.handlers[command](params)
                    else:
                        result = {'status': 'error', 'message': f'Unknown command: {command}'}

                    stream.write(MockServerProtocol.pack_message(result))
                    stream.flush()

                except Exception as e:
                    logger.error(f"Handle client error: {e}")
                    break
        except Exception as e:
            logger.error(f"Client {client_id} error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            logger.info(f"Client {client_id} disconnected")


class MockServerCommands:
    @staticmethod
    def get_system_info(params):
        info = {
            'hostname': socket.gethostname(),
            'os_version': '银河麒麟桌面V10 SP1',
            'kernel': '5.4.0-generic-ARM64',
            'architecture': 'aarch64',
            'uptime': 'up 3 hours, 15 minutes',
            'boot_time': (datetime.datetime.now() - datetime.timedelta(hours=3, minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
            'current_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'platform': 'Linux',
        }
        return {'status': 'success', 'data': info}

    @staticmethod
    def get_cpu_info(params):
        cpu_data = {
            'physical_cores': 4,
            'logical_cores': 8,
            'usage_percent': random.uniform(15, 45),
            'frequency_current': 2.0,
            'frequency_max': 2.5,
            'context_switches': 12567890,
            'interrupts': 9876543,
            'cpuinfo_raw': '''processor	: 0
model name	: FT-2000/4
cpu MHz		: 2.0GHz
cache size	: 2048 KB
physical id	: 0
siblings	: 4
core id		: 0
cpu cores	: 4

processor	: 1
model name	: FT-2000/4
cpu MHz		: 2.0GHz
cache size	: 2048 KB

processor	: 2
model name	: FT-2000/4
cpu MHz		: 2.0GHz

processor	: 3
model name	: FT-2000/4
cpu MHz		: 2.0GHz
'''
        }
        return {'status': 'success', 'data': cpu_data}

    @staticmethod
    def get_memory_info(params):
        mem_data = {
            'total': 16 * 1024**3,
            'available': 8 * 1024**3,
            'used': 8 * 1024**3,
            'percent': 50.0,
            'total_gb': 16.0,
            'available_gb': 8.0,
            'used_gb': 8.0,
            'swap_total': 4 * 1024**3,
            'swap_used': 1 * 1024**3,
            'swap_percent': 25.0,
            'meminfo_raw': '''MemTotal:        16 GB
MemFree:         8 GB
MemAvailable:    8 GB
Buffers:         512 MB
Cached:          2 GB
SwapCached:      256 MB
Active:          3 GB
Inactive:        2 GB
Active(anon):    1 GB
Inactive(anon):  512 MB
Active(file):    2 GB
Inactive(file):  1.5 GB
SwapTotal:       4 GB
SwapFree:        3 GB
'''
        }
        return {'status': 'success', 'data': mem_data}

    @staticmethod
    def get_disk_info(params):
        disk_data = {
            'partitions': [
                {
                    'device': '/dev/vda1',
                    'mountpoint': '/',
                    'fstype': 'ext4',
                    'total': 500 * 1024**3,
                    'used': 200 * 1024**3,
                    'free': 300 * 1024**3,
                    'percent': 40.0,
                    'total_gb': 500.0,
                    'free_gb': 300.0,
                },
                {
                    'device': '/dev/vda2',
                    'mountpoint': '/home',
                    'fstype': 'ext4',
                    'total': 1000 * 1024**3,
                    'used': 400 * 1024**3,
                    'free': 600 * 1024**3,
                    'percent': 40.0,
                    'total_gb': 1000.0,
                    'free_gb': 600.0,
                }
            ],
            'df_output': '''Filesystem      Size  Used Avail Use% Mounted on
/dev/vda1       500G  200G  300G  40% /
/dev/vda2      1000G  400G  600G  40% /home
tmpfs            16G   64M   16G   1% /dev/shm
'''
        }
        return {'status': 'success', 'data': disk_data}

    @staticmethod
    def get_network_info(params):
        network_data = {
            'bytes_sent': 1024 * 1024 * 500,
            'bytes_recv': 1024 * 1024 * 1024 * 2,
            'packets_sent': 1234567,
            'packets_recv': 9876543,
            'connections': 128,
            'interfaces': {
                'eth0': [
                    {'family': 'AF_INET', 'address': '192.168.1.100', 'netmask': '255.255.255.0'},
                    {'family': 'AF_INET6', 'address': 'fe80::1', 'netmask': 'ffff:ffff:ffff:ffff::'},
                ],
                'lo': [
                    {'family': 'AF_INET', 'address': '127.0.0.1', 'netmask': '255.0.0.0'},
                ]
            },
            'ip_output': '''1: lo: <LOOPBACK,UP> mtu 65536 qdisc noqueue
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP> mtu 1500 qdisc pfifo_fast
    inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0''',
            'route_output': '''default via 192.168.1.1 dev eth0
192.168.1.0/24 dev eth0 proto kernel'''
        }
        return {'status': 'success', 'data': network_data}

    @staticmethod
    def get_process_list(params):
        limit = params.get('limit', 20)
        processes = [
            {'pid': 1, 'name': 'systemd', 'username': 'root', 'cpu_percent': 0.1, 'memory_percent': 0.2, 'memory_rss': 50000, 'memory_rss_mb': 50},
            {'pid': 1234, 'name': 'kylin-desktop', 'username': 'user', 'cpu_percent': 5.2, 'memory_percent': 8.5, 'memory_rss': 850000, 'memory_rss_mb': 850},
            {'pid': 2345, 'name': 'firefox', 'username': 'user', 'cpu_percent': 12.5, 'memory_percent': 15.2, 'memory_rss': 1520000, 'memory_rss_mb': 1520},
            {'pid': 3456, 'name': 'python3', 'username': 'user', 'cpu_percent': 3.8, 'memory_percent': 2.1, 'memory_rss': 210000, 'memory_rss_mb': 210},
            {'pid': 4567, 'name': 'Xorg', 'username': 'root', 'cpu_percent': 2.5, 'memory_percent': 3.5, 'memory_rss': 350000, 'memory_rss_mb': 350},
            {'pid': 5678, 'name': 'gnome-shell', 'username': 'user', 'cpu_percent': 8.5, 'memory_percent': 6.2, 'memory_rss': 620000, 'memory_rss_mb': 620},
        ]

        ps_output = '''USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.1  0.2  50000 50000 ?        Ss   10:00   0:05 systemd
user      1234  5.2  8.5 850000 850000 ?       Sl   10:01  15:30 kylin-desktop
user      2345 12.5 15.2 1520000 1520000 ?      Sl   10:05  45:20 firefox
user      3456  3.8  2.1 210000 210000 ?       Sl   10:10   8:15 python3
root      4567  2.5  3.5 350000 350000 ?        Ss   10:00   5:40 Xorg
user      5678  8.5  6.2 620000 620000 ?       Sl   10:00  20:15 gnome-shell'''

        return {'status': 'success', 'data': {
            'processes': processes,
            'ps_output': ps_output,
            'total_processes': 256,
        }}

    @staticmethod
    def get_service_list(params):
        services = [
            {'name': 'NetworkManager', 'status': 'running'},
            {'name': 'firewalld', 'status': 'running'},
            {'name': 'sshd', 'status': 'running'},
            {'name': 'docker', 'status': 'stopped'},
            {'name': 'postgresql', 'status': 'stopped'},
        ]

        systemctl_output = '''  UNIT                        LOAD   ACTIVE SUB     DESCRIPTION
  NetworkManager.service     loaded active running Network Manager
  firewalld.service          loaded active running firewalld - dynamic firewall
  sshd.service               loaded active running OpenSSH server daemon
  docker.service             loaded inactive dead   Docker Application Container
  postgresql.service         loaded inactive dead   PostgreSQL database'''

        return {'status': 'success', 'data': {
            'services': services,
            'systemctl_output': systemctl_output,
        }}

    @staticmethod
    def restart_network(params):
        return {'status': 'success', 'message': '网络服务已重启'}

    @staticmethod
    def execute_command(params):
        cmd = params.get('command', '')
        return {'status': 'success', 'data': {'output': f'模拟执行: {cmd}', 'success': True}}

    @staticmethod
    def get_kysec_status(params):
        return {'status': 'success', 'data': {'kysec': 'Kysec status: enabled\nVersion: 3.0\nPolicy: strict'}}

    @staticmethod
    def set_kysec(params):
        action = params.get('action', '')
        return {'status': 'success', 'message': f'Kysec {action}d'}

    @staticmethod
    def get_users(params):
        users = [
            {'username': 'root', 'uid': '0', 'gid': '0', 'home': '/root', 'shell': '/bin/bash'},
            {'username': 'user', 'uid': '1000', 'gid': '1000', 'home': '/home/user', 'shell': '/bin/bash'},
            {'username': 'admin', 'uid': '1001', 'gid': '1001', 'home': '/home/admin', 'shell': '/bin/zsh'},
        ]
        return {'status': 'success', 'data': {
            'users': users,
            'passwd_raw': 'root:x:0:0:root:/root:/bin/bash\nuser:x:1000:1000:user:/home/user:/bin/bash',
        }}

    @staticmethod
    def get_login_history(params):
        return {'status': 'success', 'data': {
            'last': '''user     pts/0    192.168.1.50    Mon Apr 29 10:30 still logged in
user     pts/1    192.168.1.51    Mon Apr 29 09:15 - 10:00 (00:45)
root     tty1                     Mon Apr 29 08:00 - 10:30 (02:30)''',
            'who': '''user     pts/0    2026-05-01 10:30 (192.168.1.50)''',
        }}

    @staticmethod
    def get_apt_sources(params):
        return {'status': 'success', 'data': {
            'sources_list': '''deb http://archive.kylin.com/kylin/ V10SP1 main restricted universe
deb http://archive.kylin.com/kylin/ V10SP1-security main restricted universe
deb http://archive.kylin.com/kylin/ V10SP1-updates main restricted universe''',
            'sources_d': '''archive-team-kylin.list
mozilla.list''',
        }}

    @staticmethod
    def get_installed_packages(params):
        return {'status': 'success', 'data': {'packages': '''ii  kylin-desktop          4.0      amd64    Kylin Desktop Environment
ii  kylin-login           2.0      amd64    Kylin Login Manager
ii  kylin-system-tools    1.0      arm64    Kylin System Tools'''}}

    @staticmethod
    def cleanup_logs(params):
        return {'status': 'success', 'message': '日志清理完成'}

    @staticmethod
    def get_system_logs(params):
        return {'status': 'success', 'data': {
            'journalctl': '''Apr 29 10:00:01 kylin systemd[1]: Started Session 5 of user user.
Apr 29 10:05:23 kylin NetworkManager[1234]: <info> device (eth0): state change: activated
Apr 29 10:10:45 kylin kernel: eth0: link up''',
            'dmesg': '''[    0.000000] Linux version 5.4.0-generic-ARM64
[    1.234567] CPU: ARM64 generic
[    2.345678] Memory: 16GB available''',
        }}

    @staticmethod
    def get_system_stats(params):
        return {'status': 'success', 'data': {
            'load_average': '0.52 0.48 0.45',
            'memory': '''              total        used        free      shared  buff/cache   available
Mem:         16Gi       8.0Gi       7.5Gi        64Mi       512Mi       7.5Gi
Swap:        4Gi       1.0Gi       3.0Gi''',
            'disk': '''Filesystem      Size  Used Avail Use% Mounted on
/dev/vda1       500G  200G  300G  40% /''',
        }}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Mock Server for Testing')
    parser.add_argument('--host', default='0.0.0.0', help='Bind address')
    parser.add_argument('--port', type=int, default=29876, help='Bind port')
    args = parser.parse_args()

    server = MockServer(host=args.host, port=args.port)

    server.register_handler('get_system_info', MockServerCommands.get_system_info)
    server.register_handler('get_cpu_info', MockServerCommands.get_cpu_info)
    server.register_handler('get_memory_info', MockServerCommands.get_memory_info)
    server.register_handler('get_disk_info', MockServerCommands.get_disk_info)
    server.register_handler('get_network_info', MockServerCommands.get_network_info)
    server.register_handler('get_process_list', MockServerCommands.get_process_list)
    server.register_handler('get_service_list', MockServerCommands.get_service_list)
    server.register_handler('restart_network', MockServerCommands.restart_network)
    server.register_handler('execute_command', MockServerCommands.execute_command)
    server.register_handler('get_kysec_status', MockServerCommands.get_kysec_status)
    server.register_handler('set_kysec', MockServerCommands.set_kysec)
    server.register_handler('get_users', MockServerCommands.get_users)
    server.register_handler('get_login_history', MockServerCommands.get_login_history)
    server.register_handler('get_apt_sources', MockServerCommands.get_apt_sources)
    server.register_handler('get_installed_packages', MockServerCommands.get_installed_packages)
    server.register_handler('cleanup_logs', MockServerCommands.cleanup_logs)
    server.register_handler('get_system_logs', MockServerCommands.get_system_logs)
    server.register_handler('get_system_stats', MockServerCommands.get_system_stats)

    print(f"Mock服务器启动中...")
    print(f"监听地址: {args.host}:{args.port}")
    print(f"用于Windows测试，生产环境请使用真实server.py")

    try:
        server.start()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        server.stop()


if __name__ == '__main__':
    main()
