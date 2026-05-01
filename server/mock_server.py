#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import socket
import threading
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('MockServer')


class MockKylinServer:
    def __init__(self, host='0.0.0.0', port=29876):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = {}

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
                threading.Thread(target=self._handle_client, args=(client_socket, address), daemon=True).start()
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

    def _handle_client(self, client_socket, address):
        try:
            stream = client_socket.makefile('rwb')
            while self.running:
                header = stream.read(8)
                if not header or len(header) < 8:
                    break
                length = int.from_bytes(header, 'big')
                json_bytes = b''
                while len(json_bytes) < length:
                    chunk = stream.read(length - len(json_bytes))
                    if not chunk:
                        break
                    json_bytes += chunk

                request = json.loads(json_bytes.decode('utf-8'))
                command = request.get('command', '')
                params = request.get('params', {})

                result = self._execute_command(command, params)

                response = json.dumps(result, ensure_ascii=False).encode('utf-8')
                resp_header = len(response).to_bytes(8, 'big')
                stream.write(resp_header + response)
                stream.flush()
        except Exception as e:
            logger.error(f"Handle client error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

    def _execute_command(self, command, params):
        if command == 'get_system_info':
            return {'status': 'success', 'data': {
                'hostname': socket.gethostname(),
                'os_version': '银河麒麟桌面V10 SP1',
                'kernel': '5.4.0-generic-ARM64',
                'architecture': 'aarch64'
            }}
        elif command == 'get_cpu_info':
            return {'status': 'success', 'data': {'cpuinfo': 'processor\t: 0\nModel name\t: FT-2000/4\ncpu MHz\t\t: 2.0GHz\n'}}
        elif command == 'get_memory_info':
            return {'status': 'success', 'data': {'meminfo': 'MemTotal:       16384000 kB\nMemAvailable:    8192000 kB\nMemFree:         4096000 kB\n'}}
        elif command == 'get_disk_info':
            return {'status': 'success', 'data': {'disk': 'Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       100G   50G   50G  50% /\n'}}
        elif command == 'get_network_info':
            return {'status': 'success', 'data': {'network': 'eth0: inet 192.168.1.100/24\nlink/ether 00:11:22:33:44:55\n'}}
        elif command == 'get_process_list':
            limit = params.get('limit', 20)
            return {'status': 'success', 'data': {'processes': 'USER       PID %CPU %MEM   RSS COMMAND\nroot         1  0.0  0.1  1024 init\nroot       123  0.1  0.2  2048 systemd\n'}}
        elif command == 'get_service_list':
            return {'status': 'success', 'data': {'services': 'UNIT          STATE\nssh.service   active\ncron.service  active\n'}}
        elif command == 'restart_network':
            return {'status': 'success', 'message': '网络服务已重启'}
        elif command == 'execute_command':
            cmd = params.get('command', '')
            return {'status': 'success', 'data': {'output': f'$ {cmd}\n模拟命令输出\n'}}
        elif command == 'get_kysec_status':
            return {'status': 'success', 'data': {'kysec': 'Kysec is enabled\nsecurity level: 2'}}
        elif command == 'set_kysec':
            action = params.get('action', '')
            return {'status': 'success', 'message': f'Kysec {action}d'}
        elif command == 'get_users':
            return {'status': 'success', 'data': {'users': 'root:x:0:0::/root:/bin/bash\nuser:x:1000:1000::/home/user:/bin/bash\n'}}
        elif command == 'get_login_history':
            return {'status': 'success', 'data': {'login_history': 'user     pts/0    192.168.1.1    Mon May  1 10:00\n'}}
        elif command == 'get_apt_sources':
            return {'status': 'success', 'data': {'sources': 'deb http://repo.kylin.com/kylin V10SP1 main\n'}}
        elif command == 'get_installed_packages':
            return {'status': 'success', 'data': {'packages': 'ii  bash       5.0-6      amd64\nii  systemd    245-4      amd64\n'}}
        elif command == 'cleanup_logs':
            return {'status': 'success', 'message': '日志清理完成'}
        elif command == 'get_system_logs':
            lines = params.get('lines', 100)
            return {'status': 'success', 'data': {'logs': f'May  1 10:00:01 hostname systemd[1]: Started some service\n' * min(lines//5, 20)}}
        return {'status': 'error', 'message': f'Unknown command: {command}'}


if __name__ == '__main__':
    server = MockKylinServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
