#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('KylinClient')


class KylinClientProtocol:
    HEADER_SIZE = 8

    @staticmethod
    def pack_message(data: dict) -> bytes:
        json_data = json.dumps(data, ensure_ascii=False)
        json_bytes = json_data.encode('utf-8')
        length = len(json_bytes)
        header = length.to_bytes(KylinClientProtocol.HEADER_SIZE, 'big')
        return header + json_bytes

    @staticmethod
    def unpack_message(stream) -> dict:
        header = stream.read(KylinClientProtocol.HEADER_SIZE)
        if not header or len(header) < KylinClientProtocol.HEADER_SIZE:
            return None
        length = int.from_bytes(header, 'big')
        json_bytes = b''
        while len(json_bytes) < length:
            chunk = stream.read(length - len(json_bytes))
            if not chunk:
                return None
            json_bytes += chunk
        return json.loads(json_bytes.decode('utf-8'))


class KylinClient:
    def __init__(self, host='localhost', port=29876):
        self.host = host
        self.port = port
        self.socket = None
        self.stream = None
        self.connected = False

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.stream = self.socket.makefile('rwb')
            self.connected = True
            logger.info(f"Connected to server {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connected = False
            return False

    def disconnect(self):
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        logger.info("Disconnected from server")

    def send_request(self, command: str, params: dict = None) -> dict:
        if not self.connected:
            return {'status': 'error', 'message': 'Not connected to server'}

        if params is None:
            params = {}

        request = {
            'command': command,
            'params': params
        }

        try:
            self.stream.write(KylinClientProtocol.pack_message(request))
            self.stream.flush()
            response = KylinClientProtocol.unpack_message(self.stream)
            return response
        except Exception as e:
            logger.error(f"Send request error: {e}")
            self.connected = False
            return {'status': 'error', 'message': str(e)}

    def get_system_info(self):
        return self.send_request('get_system_info')

    def get_cpu_info(self):
        return self.send_request('get_cpu_info')

    def get_memory_info(self):
        return self.send_request('get_memory_info')

    def get_disk_info(self):
        return self.send_request('get_disk_info')

    def get_network_info(self):
        return self.send_request('get_network_info')

    def get_process_list(self, limit=20):
        return self.send_request('get_process_list', {'limit': limit})

    def get_service_list(self):
        return self.send_request('get_service_list')

    def restart_network(self):
        return self.send_request('restart_network')

    def execute_command(self, command):
        return self.send_request('execute_command', {'command': command})

    def get_kysec_status(self):
        return self.send_request('get_kysec_status')

    def set_kysec(self, action):
        return self.send_request('set_kysec', {'action': action})

    def get_users(self):
        return self.send_request('get_users')

    def get_login_history(self):
        return self.send_request('get_login_history')

    def get_apt_sources(self):
        return self.send_request('get_apt_sources')

    def get_installed_packages(self):
        return self.send_request('get_installed_packages')

    def cleanup_logs(self):
        return self.send_request('cleanup_logs')

    def get_system_logs(self, lines=100):
        return self.send_request('get_system_logs', {'lines': lines})

    def run_cleanup(self):
        return self.send_request('run_cleanup')

    def get_cleanup_config(self):
        return self.send_request('get_cleanup_config')

    def update_cleanup_config(self, config):
        return self.send_request('update_cleanup_config', {'config': config})

    def get_cleanup_status(self):
        return self.send_request('get_cleanup_status')

    def control_cleanup_service(self, action):
        return self.send_request('control_cleanup_service', {'action': action})
