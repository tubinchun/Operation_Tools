#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
import platform
import datetime
import psutil


def run_cmd(cmd, shell=True):
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=True,
            text=True, timeout=30
        )
        return result.stdout.strip(), result.returncode == 0
    except subprocess.TimeoutExpired:
        return "Command timeout", False
    except Exception as e:
        return str(e), False


class SystemCommands:
    @staticmethod
    def get_system_info():
        hostname = platform.node()
        os_version = run_cmd('cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2')[0] or "Kylin V10 SP1"
        kernel = run_cmd('uname -r')[0]
        architecture = run_cmd('uname -m')[0]
        uptime = run_cmd('uptime -p')[0] or run_cmd('cat /proc/uptime')[0][:10]

        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        info = {
            'hostname': hostname,
            'os_version': os_version.strip('"'),
            'kernel': kernel,
            'architecture': architecture,
            'uptime': uptime,
            'boot_time': boot_time,
            'current_time': current_time,
            'platform': platform.system(),
        }
        return {'status': 'success', 'data': info}

    @staticmethod
    def get_cpu_info():
        try:
            cpu_count = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_freq = psutil.cpu_freq()
            cpu_stats = psutil.cpu_stats()

            cpu_data = {
                'physical_cores': cpu_count,
                'logical_cores': cpu_count_logical,
                'usage_percent': cpu_percent,
                'frequency_current': cpu_freq.current if cpu_freq else 0,
                'frequency_max': cpu_freq.max if cpu_freq else 0,
                'context_switches': cpu_stats.ctx_switches,
                'interrupts': cpu_stats.interrupts,
            }

            proc_cpuinfo, _ = run_cmd('cat /proc/cpuinfo')
            cpu_data['cpuinfo'] = proc_cpuinfo

            return {'status': 'success', 'data': cpu_data}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_memory_info():
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            mem_data = {
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'percent': mem.percent,
                'total_gb': round(mem.total / (1024**3), 2),
                'available_gb': round(mem.available / (1024**3), 2),
                'used_gb': round(mem.used / (1024**3), 2),
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_percent': swap.percent,
            }

            proc_meminfo, _ = run_cmd('cat /proc/meminfo')
            mem_data['meminfo'] = proc_meminfo

            return {'status': 'success', 'data': mem_data}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_disk_info():
        try:
            partitions = []
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions.append({
                        'device': part.device,
                        'mountpoint': part.mountpoint,
                        'fstype': part.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                    })
                except:
                    pass

            df_output, _ = run_cmd('df -h')
            disk_data = {
                'partitions': partitions,
                'disk': df_output,
            }
            return {'status': 'success', 'data': disk_data}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_network_info():
        try:
            net_io = psutil.net_io_counters()
            net_connections = len(psutil.net_connections())

            addrs = {}
            for iface, addr_list in psutil.net_if_addrs().items():
                addrs[iface] = []
                for addr in addr_list:
                    addrs[iface].append({
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask,
                    })

            ip_output, _ = run_cmd('ip addr')
            route_output, _ = run_cmd('ip route')

            network_data = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'connections': net_connections,
                'interfaces': addrs,
                'network': ip_output,
                'route_output': route_output,
            }
            return {'status': 'success', 'data': network_data}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_process_list(limit=20):
        try:
            processes = []

            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'memory_info']):
                try:
                    pinfo = proc.info
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'username': pinfo['username'],
                        'cpu_percent': pinfo['cpu_percent'],
                        'memory_percent': pinfo['memory_percent'],
                        'memory_rss': pinfo['memory_info'].rss if pinfo.get('memory_info') else 0,
                        'memory_rss_mb': round(pinfo['memory_info'].rss / (1024**2), 2) if pinfo.get('memory_info') else 0,
                    })
                except:
                    pass

            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            top_processes = processes[:limit]

            ps_output, _ = run_cmd(f'ps aux --sort=-%cpu | head -{limit + 1}')

            return {'status': 'success', 'data': {
                'processes': top_processes,
                'processes_raw': ps_output,
                'total_processes': len(processes),
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_service_list():
        try:
            services = []
            for service in psutil.service_iter():
                try:
                    name = service.name()
                    status = service.status()
                    services.append({
                        'name': name,
                        'status': status,
                    })
                except:
                    pass

            systemctl_output, _ = run_cmd('systemctl list-units --type=service --all')

            return {'status': 'success', 'data': {
                'services': services,
                'services_raw': systemctl_output,
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def restart_network():
        try:
            output, success = run_cmd('systemctl restart NetworkManager')
            if success:
                return {'status': 'success', 'message': '网络服务已重启'}
            return {'status': 'error', 'message': output}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def execute_command(command):
        try:
            if not command:
                return {'status': 'error', 'message': 'No command provided'}

            dangerous_cmds = ['rm -rf', 'mkfs', 'dd if=', ':(){:|:&};:']
            for dangerous in dangerous_cmds:
                if dangerous in command:
                    return {'status': 'error', 'message': 'Command not allowed for security reasons'}

            output, success = run_cmd(command)
            return {'status': 'success', 'data': {'output': output, 'success': success}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_kysec_status():
        try:
            output, success = run_cmd('kysec status')
            return {'status': 'success', 'data': {'kysec': output}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def set_kysec(action):
        try:
            if action == 'disable':
                output, success = run_cmd('kysec set -k disabled')
            elif action == 'enable':
                output, success = run_cmd('kysec set -k enabled')
            else:
                return {'status': 'error', 'message': 'Invalid action'}

            if success or 'disabled' in output.lower() or 'enabled' in output.lower():
                return {'status': 'success', 'message': f'Kysec {action}d'}
            return {'status': 'error', 'message': output}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_users():
        try:
            passwd_output, _ = run_cmd('cat /etc/passwd')

            users = []
            for line in passwd_output.split('\n'):
                if ':' in line:
                    parts = line.split(':')
                    if int(parts[2]) >= 1000 if len(parts) > 2 else False:
                        users.append({
                            'username': parts[0],
                            'uid': parts[2],
                            'gid': parts[3],
                            'home': parts[5],
                            'shell': parts[6] if len(parts) > 6 else '/bin/bash',
                        })

            return {'status': 'success', 'data': {
                'users': users,
                'users_raw': passwd_output,
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_login_history():
        try:
            last_output, _ = run_cmd('last -20')
            who_output, _ = run_cmd('who')
            return {'status': 'success', 'data': {
                'login_history': last_output,
                'who': who_output,
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_apt_sources():
        try:
            sources_list, _ = run_cmd('cat /etc/apt/sources.list')
            sources_d, _ = run_cmd('ls /etc/apt/sources.list.d/')
            return {'status': 'success', 'data': {
                'sources': sources_list,
                'sources_d': sources_d,
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_installed_packages():
        try:
            packages, _ = run_cmd('dpkg -l')
            return {'status': 'success', 'data': {'packages': packages}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def cleanup_logs():
        try:
            run_cmd('journalctl --vacuum-time=7d')
            run_cmd('rm -rf /var/log/*.gz')
            run_cmd('rm -rf /var/log/syslog.*')
            return {'status': 'success', 'message': '日志清理完成'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_system_logs(lines=100):
        try:
            logs, _ = run_cmd(f'journalctl -n {lines}')
            dmesg, _ = run_cmd('dmesg | tail -50')
            return {'status': 'success', 'data': {
                'logs': logs,
                'dmesg': dmesg,
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_system_stats():
        try:
            load_avg, _ = run_cmd('cat /proc/loadavg')
            mem_info, _ = run_cmd('free -h')
            disk_usage, _ = run_cmd('df -h')

            stats = {
                'load_average': load_avg,
                'memory': mem_info,
                'disk': disk_usage,
            }
            return {'status': 'success', 'data': stats}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}