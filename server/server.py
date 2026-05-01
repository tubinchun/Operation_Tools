#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import json
import logging
import hashlib
import base64
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('KylinServer')


class KylinServerProtocol:
    VERSION = "1.0.0"
    HEADER_SIZE = 8

    @staticmethod
    def pack_message(data: dict) -> bytes:
        json_data = json.dumps(data, ensure_ascii=False)
        json_bytes = json_data.encode('utf-8')
        length = len(json_bytes)
        header = length.to_bytes(KylinServerProtocol.HEADER_SIZE, 'big')
        return header + json_bytes

    @staticmethod
    def unpack_message(stream) -> dict:
        header = stream.read(KylinServerProtocol.HEADER_SIZE)
        if not header or len(header) < KylinServerProtocol.HEADER_SIZE:
            return None
        length = int.from_bytes(header, 'big')
        json_bytes = b''
        while len(json_bytes) < length:
            chunk = stream.read(length - len(json_bytes))
            if not chunk:
                return None
            json_bytes += chunk
        return json.loads(json_bytes.decode('utf-8'))


class KylinServer:
    def __init__(self, host='0.0.0.0', port=29876):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = {}
        self.client_id = 0
        self.handlers = {}

    def register_handler(self, command: str, handler: callable):
        self.handlers[command] = handler

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(50)
        self.running = True
        logger.info(f"Kylin Server started on {self.host}:{self.port}")

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
                    request = KylinServerProtocol.unpack_message(stream)
                    if request is None:
                        break

                    command = request.get('command', '')
                    params = request.get('params', {})

                    logger.info(f"Client {client_id} command: {command}")

                    if command in self.handlers:
                        result = self.handlers[command](params)
                    else:
                        result = {'status': 'error', 'message': f'Unknown command: {command}'}

                    KylinServerProtocol.pack_message(result)
                    stream.write(KylinServerProtocol.pack_message(result))
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


class KylinServerCommands:
    @staticmethod
    def get_system_info(params):
        info = {
            'hostname': socket.gethostname(),
            'os_version': 'Kylin V10 SP1',
            'kernel': os.popen('uname -r').read().strip(),
            'architecture': os.popen('uname -m').read().strip(),
        }
        return {'status': 'success', 'data': info}

    @staticmethod
    def get_cpu_info(params):
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpu_data = f.read()
            return {'status': 'success', 'data': {'cpuinfo': cpu_data}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_memory_info(params):
        try:
            with open('/proc/meminfo', 'r') as f:
                mem_data = f.read()
            return {'status': 'success', 'data': {'meminfo': mem_data}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_disk_info(params):
        try:
            result = os.popen('df -h').read()
            return {'status': 'success', 'data': {'disk': result}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_network_info(params):
        try:
            result = os.popen('ip addr').read()
            return {'status': 'success', 'data': {'network': result}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_process_list(params):
        try:
            limit = params.get('limit', 20)
            result = os.popen(f'ps aux --sort=-%cpu | head -{limit}').read()
            return {'status': 'success', 'data': {'processes': result}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_service_list(params):
        try:
            result = os.popen('systemctl list-units --type=service --all').read()
            return {'status': 'success', 'data': {'services': result}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def restart_network(params):
        try:
            os.system('systemctl restart NetworkManager')
            return {'status': 'success', 'message': 'Network restarted'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def execute_command(params):
        try:
            cmd = params.get('command', '')
            if not cmd:
                return {'status': 'error', 'message': 'No command provided'}
            result = os.popen(cmd).read()
            return {'status': 'success', 'data': {'output': result}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_kysec_status(params):
        try:
            result = os.popen('kysec status').read()
            return {'status': 'success', 'data': {'kysec': result}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def set_kysec(params):
        try:
            action = params.get('action', '')
            if action == 'disable':
                os.system('kysec set -k disabled')
            elif action == 'enable':
                os.system('kysec set -k enabled')
            return {'status': 'success', 'message': f'Kysec {action}d'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_users(params):
        try:
            result = os.popen('cat /etc/passwd').read()
            return {'status': 'success', 'data': {'users': result}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_login_history(params):
        try:
            result = os.popen('last').read()
            return {'status': 'success', 'data': {'login_history': result}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_apt_sources(params):
        try:
            result = os.popen('cat /etc/apt/sources.list').read()
            return {'status': 'success', 'data': {'sources': result}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_installed_packages(params):
        try:
            result = os.popen('dpkg -l').read()
            return {'status': 'success', 'data': {'packages': result}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def cleanup_logs(params):
        try:
            os.system('journalctl --vacuum-time=7d')
            os.system('rm -rf /var/log/*.gz')
            return {'status': 'success', 'message': 'Logs cleaned'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_system_logs(params):
        try:
            lines = params.get('lines', 100)
            result = os.popen(f'journalctl -n {lines}').read()
            return {'status': 'success', 'data': {'logs': result}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


def main():
    server = KylinServer()

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

    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.stop()


if __name__ == '__main__':
    main()
