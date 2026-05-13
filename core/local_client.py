#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.commands import SystemCommands


class LocalClient:
    def __init__(self):
        self.connected = True

    def connect(self):
        return True

    def disconnect(self):
        pass

    def get_system_info(self):
        return SystemCommands.get_system_info()

    def get_cpu_info(self):
        return SystemCommands.get_cpu_info()

    def get_memory_info(self):
        return SystemCommands.get_memory_info()

    def get_disk_info(self):
        return SystemCommands.get_disk_info()

    def get_network_info(self):
        return SystemCommands.get_network_info()

    def get_process_list(self, limit=20):
        return SystemCommands.get_process_list(limit)

    def get_service_list(self):
        return SystemCommands.get_service_list()

    def restart_network(self):
        return SystemCommands.restart_network()

    def execute_command(self, command):
        return SystemCommands.execute_command(command)

    def get_kysec_status(self):
        return SystemCommands.get_kysec_status()

    def set_kysec(self, action):
        return SystemCommands.set_kysec(action)

    def get_users(self):
        return SystemCommands.get_users()

    def get_login_history(self):
        return SystemCommands.get_login_history()

    def get_apt_sources(self):
        return SystemCommands.get_apt_sources()

    def get_installed_packages(self):
        return SystemCommands.get_installed_packages()

    def cleanup_logs(self):
        return SystemCommands.cleanup_logs()

    def get_system_logs(self, lines=100):
        return SystemCommands.get_system_logs(lines)