#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
import platform
import datetime
import psutil
import re
from collections import defaultdict


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
        hostname = run_cmd('hostname')[0]
        os_name = run_cmd('grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d \'"\'')[0] or "银河麒麟桌面操作系统V10 SP1"
        os_version = run_cmd('grep VERSION_ID /etc/os-release | cut -d= -f2 | tr -d \'"\'')[0] or "2503"
        kernel = run_cmd('uname -r')[0]
        kernel_name = run_cmd('uname -s')[0]
        architecture = run_cmd('uname -m')[0]
        bits = run_cmd('getconf LONG_BIT')[0] or "64"
        bits = f"{bits}bit"
        uptime = run_cmd('uptime -p')[0] or run_cmd('cat /proc/uptime')[0][:10]

        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        info = {
            'hostname': hostname,
            'os_name': os_name,
            'os_version': os_version,
            'kernel': kernel,
            'kernel_name': kernel_name,
            'architecture': architecture,
            'bits': bits,
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

            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'memory_info', 'uids']):
                try:
                    pinfo = proc.info
                    username = pinfo.get('username')
                    
                    if username is None:
                        try:
                            import pwd
                            uids = pinfo.get('uids')
                            if uids:
                                username = pwd.getpwuid(uids.real).pw_name
                        except:
                            username = 'unknown'
                    
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'username': username,
                        'cpu_percent': pinfo['cpu_percent'],
                        'memory_percent': pinfo['memory_percent'],
                        'memory_rss': pinfo['memory_info'].rss if pinfo.get('memory_info') else 0,
                        'memory_rss_mb': round(pinfo['memory_info'].rss / (1024**2), 2) if pinfo.get('memory_info') else 0,
                    })
                except Exception as e:
                    pass

            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            top_processes = processes[:limit]

            return {'status': 'success', 'data': {
                'processes': top_processes,
                'processes_raw': '',
                'total_processes': len(processes),
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_process_list_by_user(username, max_count=50):
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info', 'uids']):
                try:
                    pinfo = proc.info
                    proc_username = pinfo.get('username')
                    
                    if proc_username is None:
                        try:
                            uids = pinfo.get('uids')
                            if uids:
                                import pwd
                                proc_username = pwd.getpwuid(uids.real).pw_name
                        except:
                            proc_username = str(pinfo.get('pid'))
                    
                    if proc_username == username or proc_username == f'{username}':
                        processes.append({
                            'pid': pinfo['pid'],
                            'name': pinfo['name'],
                            'username': proc_username,
                            'cpu_percent': pinfo['cpu_percent'],
                            'memory_rss_mb': round(pinfo['memory_info'].rss / (1024**2), 2) if pinfo.get('memory_info') else 0,
                        })
                except Exception as e:
                    pass
            
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            return {'status': 'success', 'data': {
                'processes': processes[:max_count],
                'total_processes': len(processes),
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def kill_process(pid):
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()
            
            try:
                proc.terminate()
                proc.wait(timeout=3)
                return {'status': 'success', 'message': f'进程 {proc_name} (PID: {pid}) 已成功结束'}
            except psutil.TimeoutExpired:
                try:
                    proc.kill()
                    proc.wait(timeout=3)
                    return {'status': 'success', 'message': f'进程 {proc_name} (PID: {pid}) 已强制结束'}
                except Exception as e:
                    return {'status': 'error', 'message': f'强制结束进程失败: {str(e)}'}
            except psutil.AccessDenied:
                output, success = run_cmd(f'sudo kill -9 {pid}')
                if success:
                    return {'status': 'success', 'message': f'进程 {proc_name} (PID: {pid}) 已使用 sudo 结束'}
                return {'status': 'error', 'message': f'权限不足: {output}'}
            except Exception as e:
                return {'status': 'error', 'message': f'结束进程失败: {str(e)}'}
        except psutil.NoSuchProcess:
            return {'status': 'error', 'message': f'进程不存在 (PID: {pid})'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def kill_process_by_name(name):
        try:
            output, success = run_cmd(f'killall {name}')
            if success:
                return {'status': 'success', 'message': f'成功结束所有名为 {name} 的进程'}
            else:
                output, success = run_cmd(f'sudo killall {name}')
                if success:
                    return {'status': 'success', 'message': f'使用 sudo 成功结束所有名为 {name} 的进程'}
                return {'status': 'error', 'message': f'结束进程失败: {output}'}
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
            output, success = run_cmd('getstatus')
            if not success:
                output, success = run_cmd('kysec status')
            
            # 解析状态，只保留 enabled 或 disabled
            status_value = 'unknown'
            lower_output = output.lower()
            
            if 'enabled' in lower_output:
                status_value = 'enabled'
            elif 'disabled' in lower_output:
                status_value = 'disabled'
            
            return {'status': 'success', 'data': {'kysec': status_value, 'raw': output}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def set_kysec(action):
        try:
            if action == 'disable':
                output, success = run_cmd('setstatus disable -p')
            elif action == 'enable':
                output, success = run_cmd('setstatus enable')
            else:
                return {'status': 'error', 'message': 'Invalid action'}

            lower_output = output.lower()
            
            if success or \
               'disabled' in lower_output or \
               'enabled' in lower_output or \
               'setting' in lower_output or \
               'success' in lower_output or \
               'ok' in lower_output:
                return {'status': 'success', 'message': f'KySec 已{action}', 'need_reboot': True}
            return {'status': 'error', 'message': output if output else '操作失败'}
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
    def get_login_history(username=None):
        try:
            if username:
                last_output, _ = run_cmd(f'last {username} -n 20')
            else:
                last_output, _ = run_cmd('last -20')
            who_output, _ = run_cmd('who')
            return {'status': 'success', 'data': {
                'login_history': last_output,
                'who': who_output,
                'username': username,
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def reset_user_password(username, new_password):
        try:
            cmd = f"echo '{username}:{new_password}' | sudo chpasswd"
            output, success = run_cmd(cmd)
            if success:
                return {'status': 'success', 'message': f"用户 {username} 的密码已成功重置"}
            else:
                return {'status': 'error', 'message': f"密码重置失败: {output}"}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_user_info(username):
        try:
            username_output, _ = run_cmd(f"awk -F: '/^{username}:/{{print $1}}' /etc/passwd")
            uid_output, _ = run_cmd(f"awk -F: '/^{username}:/{{print $3}}' /etc/passwd")
            gid_output, _ = run_cmd(f"awk -F: '/^{username}:/{{print $4}}' /etc/passwd")
            home_output, _ = run_cmd(f"awk -F: '/^{username}:/{{print $6}}' /etc/passwd")
            shell_output, _ = run_cmd(f"awk -F: '/^{username}:/{{print $7}}' /etc/passwd")
            
            passwd_status, _ = run_cmd(f"sudo passwd -S {username}")
            is_locked = False
            password_status = "未知"
            if passwd_status:
                status_parts = passwd_status.split()
                if len(status_parts) >= 2:
                    if status_parts[1] == 'L':
                        password_status = "已锁定"
                        is_locked = True
                    elif status_parts[1] == 'P':
                        password_status = "已设置"
                    elif status_parts[1] == 'NP':
                        password_status = "无密码"
            
            uid_num = int(uid_output) if uid_output.isdigit() else 0
            user_type = "普通用户" if uid_num >= 1000 else "系统用户"
            
            groups_output, _ = run_cmd(f"id {username}")
            groups = ""
            if groups_output:
                groups_start = groups_output.find("groups=")
                if groups_start != -1:
                    groups = groups_output[groups_start+7:].replace("(", ",").replace(")", "").rstrip(',')
            
            return {'status': 'success', 'data': {
                'username': username_output or username,
                'uid': uid_output or "未知",
                'gid': gid_output or "未知",
                'home': home_output or "未知",
                'shell': shell_output or "未知",
                'password_status': password_status,
                'is_locked': is_locked,
                'user_type': user_type,
                'groups': groups or "未知",
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
    def get_log_by_type(log_type, lines=200):
        try:
            if log_type == 'system':
                logs, _ = run_cmd(f'journalctl -n {lines}')
            elif log_type == 'boot':
                logs, _ = run_cmd('dmesg')
            elif log_type == 'login':
                logs, _ = run_cmd('last -n 50')
                failed_logins, _ = run_cmd('lastb -n 20 2>/dev/null || echo "需要 sudo 权限查看失败登录记录"')
                auth_log, _ = run_cmd(f'tail -n {lines} /var/log/auth.log 2>/dev/null || echo "无法读取 auth.log"')
                logs = f"=== 成功登录记录 ===\n{logs}\n\n=== 失败登录尝试 ===\n{failed_logins}\n\n=== 认证日志 ===\n{auth_log}"
            elif log_type == 'application':
                logs, _ = run_cmd(f'journalctl -u "*.service" -n {lines}')
            elif log_type == 'security':
                auth_log, _ = run_cmd(f'tail -n {lines} /var/log/auth.log 2>/dev/null || echo "无法读取 auth.log"')
                secure_log, _ = run_cmd(f'tail -n {lines} /var/log/secure 2>/dev/null || echo "无法读取 secure.log"')
                logs = f"=== Auth Log ===\n{auth_log}\n\n=== Secure Log ===\n{secure_log}"
            elif log_type == 'trace':
                logs, _ = run_cmd(f'journalctl -n {lines} --since "1 hour ago"')
            elif log_type == 'audit':
                audit_log, _ = run_cmd(f'tail -n {lines} /var/log/audit/audit.log 2>/dev/null || echo "无法读取 audit.log"')
                logs = audit_log if audit_log.strip() else "审计日志不可用"
            else:
                logs, _ = run_cmd(f'journalctl -n {lines}')
            
            return {'status': 'success', 'data': {'logs': logs, 'type': log_type}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    ERROR_KEYWORDS = [
        'error', 'Error', 'ERROR',
        'fail', 'Fail', 'FAIL', 'failed', 'Failed', 'FAILED',
        'exception', 'Exception', 'EXCEPTION',
        'crash', 'Crash', 'CRASH',
        'warn', 'Warn', 'WARN', 'warning', 'Warning', 'WARNING',
        'segfault', 'Segfault', 'SEGFAULT',
        'panic', 'Panic', 'PANIC',
        'fatal', 'Fatal', 'FATAL',
        'unable', 'Unable',
        'cannot', 'Cannot', 'CANNOT',
        'denied', 'Denied', 'DENIED',
        'timeout', 'Timeout', 'TIMEOUT',
        'invalid', 'Invalid', 'INVALID',
        'permission', 'Permission', 'PERMISSION',
    ]

    ERROR_CODE_PATTERNS = [
        r'code\s*=\s*(\d+)',
        r'error\s*code\s*(\d+)',
        r'errno\s*=\s*(\d+)',
        r'error\s*(\d+)',
        r'\[(\d+)\]\s*error',
    ]

    STACK_TRACE_PATTERNS = [
        r'File\s+"([^"]+)"',
        r'at\s+(\w+\.\w+)\(',
        r'Traceback \(most recent call last\):',
        r'^\s*File "',
    ]

    @staticmethod
    def analyze_logs(logs, filters=None):
        if filters is None:
            filters = {}
        
        error_logs = []
        warning_logs = []
        info_logs = []
        other_logs = []
        
        error_stats = defaultdict(int)
        error_by_module = defaultdict(int)
        error_by_time = defaultdict(int)
        
        keyword_filter = filters.get('keywords', [])
        level_filter = filters.get('level', 'all')
        time_filter = filters.get('time_range', None)
        
        for line in logs.split('\n'):
            if not line.strip():
                continue
            
            log_entry = SystemCommands.parse_log_line(line)
            
            if not log_entry:
                continue
            
            if time_filter:
                if not SystemCommands.matches_time_filter(log_entry.get('timestamp', ''), time_filter):
                    continue
            
            level = log_entry.get('level', 'INFO').upper()
            
            if keyword_filter:
                found = False
                for keyword in keyword_filter:
                    if keyword.lower() in line.lower():
                        found = True
                        break
                if not found:
                    continue
            
            is_error = SystemCommands.is_error_log(line)
            is_warning = SystemCommands.is_warning_log(line)
            
            if level_filter != 'all':
                if level != level_filter:
                    if not (level_filter == 'ERROR' and is_error):
                        continue
            
            log_entry['is_error'] = is_error
            log_entry['is_warning'] = is_warning
            log_entry['raw_line'] = line
            
            if is_error:
                error_logs.append(log_entry)
                error_type = SystemCommands.classify_error(line)
                module = SystemCommands.extract_module(line)
                time_hour = log_entry.get('timestamp', '')[:13]
                
                error_stats[error_type] += 1
                error_by_module[module] += 1
                error_by_time[time_hour] += 1
            elif is_warning:
                warning_logs.append(log_entry)
            elif level == 'INFO':
                info_logs.append(log_entry)
            else:
                other_logs.append(log_entry)
        
        return {
            'status': 'success',
            'data': {
                'error_logs': error_logs,
                'warning_logs': warning_logs,
                'info_logs': info_logs,
                'other_logs': other_logs,
                'stats': {
                    'total_errors': len(error_logs),
                    'total_warnings': len(warning_logs),
                    'total_info': len(info_logs),
                    'error_by_type': dict(error_stats),
                    'error_by_module': dict(error_by_module),
                    'error_by_time': dict(error_by_time),
                }
            }
        }

    @staticmethod
    def parse_log_line(line):
        patterns = [
            r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(\w+)\s+(\w+)\[?(\d*)\]?:?\s+(.*)$',
            r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\S*\s+(\w+)\s+(\w+)\[?(\d*)\]?:?\s+(.*)$',
            r'^\[?(\d{2}:\d{2}:\d{2})\]?\s*(\w+)\s*[:-]\s*(.*)$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                if len(groups) >= 5:
                    return {
                        'timestamp': groups[0],
                        'host': groups[1],
                        'process': groups[2],
                        'pid': groups[3] if groups[3] else None,
                        'message': groups[4],
                        'level': 'INFO',
                    }
                elif len(groups) == 3:
                    return {
                        'timestamp': groups[0],
                        'level': groups[1],
                        'message': groups[2],
                    }
        
        return {
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': line,
            'level': 'INFO',
        }

    @staticmethod
    def is_error_log(line):
        for keyword in SystemCommands.ERROR_KEYWORDS:
            if keyword.lower() in line.lower():
                if 'warning' in keyword.lower():
                    continue
                return True
        
        for pattern in SystemCommands.ERROR_CODE_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        for pattern in SystemCommands.STACK_TRACE_PATTERNS:
            if re.search(pattern, line):
                return True
        
        return False

    @staticmethod
    def is_warning_log(line):
        warning_keywords = ['warn', 'warning', 'WARNING']
        for keyword in warning_keywords:
            if keyword.lower() in line.lower():
                return True
        return False

    @staticmethod
    def classify_error(line):
        error_types = {
            'authentication': ['auth', 'login', 'password', 'permission', 'denied'],
            'network': ['network', 'connect', 'timeout', 'socket', 'http', 'tcp', 'udp'],
            'disk': ['disk', 'storage', 'mount', 'fsck', 'inode', 'block'],
            'memory': ['memory', 'oom', 'swap', 'ram'],
            'cpu': ['cpu', 'processor', 'load'],
            'system': ['system', 'kernel', 'module', 'driver'],
            'application': ['app', 'service', 'daemon', 'process'],
            'database': ['database', 'mysql', 'postgres', 'sqlite'],
            'file': ['file', 'directory', 'path', 'read', 'write'],
        }
        
        line_lower = line.lower()
        for error_type, keywords in error_types.items():
            for keyword in keywords:
                if keyword in line_lower:
                    return error_type
        
        return 'other'

    @staticmethod
    def extract_module(line):
        patterns = [
            r'(\w+)\[\d+\]:',
            r'(\w+)\.service:',
            r'(\w+)\.log:',
            r'(\w+)\.py:',
            r'(\w+)\.c:',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        
        return 'unknown'

    @staticmethod
    def matches_time_filter(timestamp, time_range):
        try:
            log_time = datetime.datetime.strptime(timestamp[:19], '%Y-%m-%d %H:%M:%S')
            now = datetime.datetime.now()
            
            if time_range == '1h':
                return log_time >= now - datetime.timedelta(hours=1)
            elif time_range == '6h':
                return log_time >= now - datetime.timedelta(hours=6)
            elif time_range == '24h':
                return log_time >= now - datetime.timedelta(hours=24)
            elif time_range == '7d':
                return log_time >= now - datetime.timedelta(days=7)
        except:
            pass
        
        return True

    @staticmethod
    def export_logs(log_entries, format_type='txt', filename=None):
        if not filename:
            filename = f"error_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format_type == 'json':
            import json
            content = json.dumps(log_entries, indent=2, ensure_ascii=False)
            ext = '.json'
        elif format_type == 'csv':
            headers = ['timestamp', 'level', 'process', 'pid', 'message']
            lines = [','.join(headers)]
            for entry in log_entries:
                row = [
                    entry.get('timestamp', ''),
                    entry.get('level', ''),
                    entry.get('process', ''),
                    str(entry.get('pid', '')),
                    entry.get('message', '').replace(',', ' '),
                ]
                lines.append(','.join(row))
            content = '\n'.join(lines)
            ext = '.csv'
        else:
            lines = []
            for entry in log_entries:
                line = f"{entry.get('timestamp', '')} [{entry.get('level', 'INFO')}] {entry.get('message', '')}"
                lines.append(line)
            content = '\n'.join(lines)
            ext = '.txt'
        
        full_path = f"/tmp/{filename}{ext}"
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {'status': 'success', 'data': {'path': full_path, 'count': len(log_entries)}}
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

    @staticmethod
    def get_hardware_info():
        try:
            manufacturer, _ = run_cmd('cat /sys/class/dmi/id/sys_vendor 2>/dev/null || echo "Unknown"')
            product_version, _ = run_cmd('cat /sys/class/dmi/id/product_version 2>/dev/null || echo "None"')
            product_name, _ = run_cmd('cat /sys/class/dmi/id/product_name 2>/dev/null || echo "Unknown"')
            serial_number, _ = run_cmd('sudo dmidecode -s system-serial-number 2>/dev/null || cat /sys/class/dmi/id/product_serial 2>/dev/null || echo "Unknown"')
            
            cpu_model, _ = run_cmd("lscpu | sed -n 's/^型号名称：[[:blank:]]*//p'")
            if not cpu_model:
                cpu_model, _ = run_cmd("lscpu | grep 'Model name' | sed 's/Model name[[:space:]]*:[[:space:]]*//'")
            if not cpu_model:
                cpu_model = 'Unknown'

            hardware_info = {
                'manufacturer': manufacturer,
                'version': product_version,
                'product_name': product_name,
                'serial_number': serial_number,
                'cpu_model': cpu_model,
            }
            return {'status': 'success', 'data': hardware_info}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_gpu_info():
        try:
            gpu_info = {
                'name': 'Unknown',
                'manufacturer': 'Unknown',
                'subsystem': 'Unknown',
                'model': 'Unknown',
                'memory': 'Unknown',
                'bus_info': 'Unknown',
                'clock': 'Unknown',
                'physical_id': 'Unknown',
                'version': 'Unknown',
                'driver': 'Unknown',
                'bus_width': 'Unknown',
            }
            
            name, _ = run_cmd('lspci | grep VGA | cut -d: -f3')
            if name:
                gpu_info['name'] = name.strip()
                gpu_info['model'] = name.strip()
            
            if 'VMware' in gpu_info['name']:
                gpu_info['manufacturer'] = 'VMware'
                gpu_info['memory'] = '128MB'
                gpu_info['driver'] = 'vmwgfx'
            
            vga_device, _ = run_cmd('lspci | grep VGA | cut -d\' \' -f1')
            if vga_device:
                subsystem, _ = run_cmd(f'lspci -nn -s {vga_device} 2>/dev/null | sed -n \'s/.*Subsystem \\([^ ]*\\):.*/\\1/p\'')
                if subsystem:
                    gpu_info['subsystem'] = subsystem.strip()
            
            return {'status': 'success', 'data': gpu_info}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}