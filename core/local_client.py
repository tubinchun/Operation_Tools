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

    def get_process_list_by_user(self, username, limit=50):
        return SystemCommands.get_process_list_by_user(username, limit)

    def kill_process(self, pid):
        return SystemCommands.kill_process(pid)
    
    def kill_process_by_name(self, name):
        return SystemCommands.kill_process_by_name(name)

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

    def reset_user_password(self, username, new_password):
        return SystemCommands.reset_user_password(username, new_password)

    def get_user_info(self, username):
        return SystemCommands.get_user_info(username)

    def get_apt_sources(self):
        return SystemCommands.get_apt_sources()

    def get_installed_packages(self):
        return SystemCommands.get_installed_packages()

    def get_system_logs(self, lines=100):
        return SystemCommands.get_system_logs(lines)

    def get_log_by_type(self, log_type, lines=200):
        return SystemCommands.get_log_by_type(log_type, lines)

    def analyze_logs(self, logs, filters=None):
        return SystemCommands.analyze_logs(logs, filters)

    def export_logs(self, log_entries, format_type='txt', filename=None):
        return SystemCommands.export_logs(log_entries, format_type, filename)

    def cleanup_logs(self):
        return SystemCommands.cleanup_logs()

    def get_hardware_info(self):
        return SystemCommands.get_hardware_info()

    def get_gpu_info(self):
        return SystemCommands.get_gpu_info()