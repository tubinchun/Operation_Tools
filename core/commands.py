#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
import platform
import datetime
import psutil
import re
from collections import defaultdict

try:
    from .auth_service import AuthService
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from auth_service import AuthService


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


def run_cmd_with_auth(cmd_list, input_data=None):
    """通过授权服务执行需要管理员权限的命令"""
    try:
        auth_service = AuthService()
        result = auth_service.execute(cmd_list, input_data)
        
        if result.get('success'):
            return result.get('stdout', ''), True
        else:
            error_msg = result.get('error', result.get('stderr', 'Unknown error'))
            return error_msg, False
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
            
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'memory_info', 'uids']):
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
                            'memory_percent': pinfo['memory_percent'],
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
                output, success = run_cmd_with_auth(['kill', '-9', str(pid)])
                if success:
                    return {'status': 'success', 'message': f'进程 {proc_name} (PID: {pid}) 已成功结束'}
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
            output, success = run_cmd(['killall', name])
            if success:
                return {'status': 'success', 'message': f'成功结束所有名为 {name} 的进程'}
            else:
                output, success = run_cmd_with_auth(['killall', name])
                if success:
                    return {'status': 'success', 'message': f'成功结束所有名为 {name} 的进程'}
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
            cmd = ['pkexec', 'chpasswd']
            import subprocess
            result = subprocess.run(
                cmd,
                input=f'{username}:{new_password}',
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return {'status': 'success', 'message': f"用户 {username} 的密码已成功重置"}
            return {'status': 'error', 'message': f"密码重置失败: {result.stderr}"}
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
            serial_number, _ = run_cmd('pkexec dmidecode -t system 2>/dev/null | grep Serial | sed \'s/^[[:space:]]*Serial[[:space:]]*Number[[:space:]]*:[[:space:]]*//\' || cat /sys/class/dmi/id/product_serial 2>/dev/null || echo "Unknown"')
            serial_number = serial_number.strip() if serial_number else "Unknown"
            
            cpu_model, _ = run_cmd("lscpu | sed -n 's/^型号名称：[[:blank:]]*//p'")
            if not cpu_model:
                cpu_model, _ = run_cmd("lscpu | grep 'Model name' | sed 's/Model name[[:space:]]*:[[:space:]]*//'")
            if not cpu_model:
                cpu_model = 'Unknown'
            
            cpu_cores, _ = run_cmd("lscpu | grep 'CPU(s):' | head -1 | sed 's/CPU(s)[[:space:]]*:[[:space:]]*//'")
            cpu_threads, _ = run_cmd("lscpu | grep 'Thread(s) per core' | sed 's/Thread(s) per core[[:space:]]*:[[:space:]]*//'")
            
            mem_total, _ = run_cmd("free -h | grep Mem | awk '{print $2}'")
            swap_total, _ = run_cmd("free -h | grep Swap | awk '{print $2}'")
            
            motherboard_info, _ = run_cmd('cat /sys/class/dmi/id/board_name 2>/dev/null || echo "Unknown"')
            motherboard_vendor, _ = run_cmd('cat /sys/class/dmi/id/board_vendor 2>/dev/null || echo "Unknown"')
            motherboard_version, _ = run_cmd('cat /sys/class/dmi/id/board_version 2>/dev/null || echo "Unknown"')
            
            gpu_info = SystemCommands._get_gpu_details()
            
            disks = SystemCommands._get_storage_info()
            
            hardware_info = {
                'system': {
                    'manufacturer': manufacturer.strip(),
                    'product_name': product_name.strip(),
                    'product_version': product_version.strip(),
                    'serial_number': serial_number,
                },
                'cpu': {
                    'model': cpu_model.strip(),
                    'cores': cpu_cores.strip() if cpu_cores else "Unknown",
                    'threads': cpu_threads.strip() if cpu_threads else "Unknown",
                },
                'memory': {
                    'total': mem_total.strip() if mem_total else "Unknown",
                    'swap': swap_total.strip() if swap_total else "Unknown",
                },
                'motherboard': {
                    'name': motherboard_info.strip(),
                    'vendor': motherboard_vendor.strip(),
                    'version': motherboard_version.strip(),
                },
                'gpu': gpu_info,
                'storage': disks,
            }
            return {'status': 'success', 'data': hardware_info}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_gpu_info():
        try:
            gpu_info = SystemCommands._get_gpu_details()
            return {'status': 'success', 'data': gpu_info}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def _get_gpu_details():
        gpu_info = {
            'name': 'Unknown',
            'manufacturer': 'Unknown',
            'model': 'Unknown',
            'memory': 'Unknown',
            'driver': 'Unknown',
            'bus_info': 'Unknown',
        }
        
        name, _ = run_cmd('lspci | grep -i VGA | cut -d: -f3')
        if name:
            gpu_info['name'] = name.strip()
            gpu_info['model'] = name.strip()
            
            if 'NVIDIA' in name:
                gpu_info['manufacturer'] = 'NVIDIA'
                mem_output, _ = run_cmd('nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null')
                if mem_output:
                    gpu_info['memory'] = f"{mem_output.strip()}MB"
                driver_output, _ = run_cmd('nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null')
                if driver_output:
                    gpu_info['driver'] = driver_output.strip()
            elif 'AMD' in name or 'ATI' in name:
                gpu_info['manufacturer'] = 'AMD'
            elif 'Intel' in name:
                gpu_info['manufacturer'] = 'Intel'
            elif 'VMware' in name:
                gpu_info['manufacturer'] = 'VMware'
                gpu_info['memory'] = '128MB'
                gpu_info['driver'] = 'vmwgfx'
        
        vga_device, _ = run_cmd('lspci | grep -i VGA | cut -d\' \' -f1')
        if vga_device:
            bus_info, _ = run_cmd(f'lspci -v -s {vga_device} 2>/dev/null | grep "Bus info" | sed \'s/Bus info[[:space:]]*:[[:space:]]*//\'')
            if bus_info:
                gpu_info['bus_info'] = bus_info.strip()
        
        return gpu_info

    @staticmethod
    def _get_storage_info():
        disks = []
        try:
            lsblk_output, _ = run_cmd('lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT -n')
            if lsblk_output:
                for line in lsblk_output.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 2 and parts[2] == 'disk':
                        disk_name = parts[0]
                        disk_size = parts[1]
                        disks.append({
                            'name': disk_name,
                            'size': disk_size,
                            'type': 'HDD/SSD',
                        })
        except Exception:
            pass
        
        if not disks:
            disks.append({'name': 'Unknown', 'size': 'Unknown', 'type': 'Unknown'})
        
        return disks

    @staticmethod
    def get_detailed_system_info():
        import subprocess
        import os
        
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'kylin_desktop_system_info.sh'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core', 'kylin_desktop_system_info.sh'),
            '/usr/share/kylin-system-tools/core/kylin_desktop_system_info.sh',
            '/opt/kylin-system-tools/core/kylin_desktop_system_info.sh',
            '/usr/local/share/kylin-system-tools/core/kylin_desktop_system_info.sh',
        ]
        
        script_path = None
        for path in possible_paths:
            if os.path.exists(path):
                script_path = path
                break
        
        if script_path:
            try:
                os.chmod(script_path, 0o755)
                result = subprocess.run(
                    ['bash', script_path],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                return {
                    'status': 'success',
                    'data': {
                        'output': result.stdout,
                        'error': result.stderr
                    }
                }
            except subprocess.TimeoutExpired:
                return {'status': 'error', 'message': '执行超时'}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}
        else:
            return {'status': 'success', 'data': {'output': SystemCommands._get_system_info_python(), 'error': ''}}

    @staticmethod
    def fix_printer():
        import subprocess
        import os
        
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'fix_printer.sh'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core', 'fix_printer.sh'),
            '/usr/share/kylin-system-tools/core/fix_printer.sh',
            '/opt/kylin-system-tools/core/fix_printer.sh',
            '/usr/local/share/kylin-system-tools/core/fix_printer.sh',
        ]
        
        script_path = None
        for path in possible_paths:
            if os.path.exists(path):
                script_path = path
                break
        
        if script_path:
            try:
                os.chmod(script_path, 0o755)
                result = subprocess.run(
                    ['bash', script_path],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                return {
                    'status': 'success',
                    'message': '打印机修复成功' if result.returncode == 0 else '打印机修复失败',
                    'output': result.stdout,
                    'error': result.stderr
                }
            except subprocess.TimeoutExpired:
                return {'status': 'error', 'message': '执行超时'}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}
        else:
            return SystemCommands._fix_printer_command()

    @staticmethod
    def _fix_printer_command():
        output, success = run_cmd_with_auth(['cp', '/usr/share/cups/cupsd.conf.default', '/etc/cups/cupsd.conf'])
        if not success:
            return {'status': 'error', 'message': f'恢复CUPS默认配置失败: {output}'}
        
        output, success = run_cmd_with_auth(['systemctl', 'restart', 'cups'])
        if not success:
            return {'status': 'error', 'message': f'重启CUPS服务失败: {output}'}
        
        return {'status': 'success', 'message': '打印机修复成功'}

    @staticmethod
    def _get_system_info_python():
        import subprocess
        
        def run_cmd(cmd, shell=True):
            try:
                result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=30)
                return result.stdout.strip()
            except Exception:
                return ""
        
        lines = []
        
        lines.append("=" * 78)
        lines.append("                    系统基本信息")
        lines.append("=" * 78)
        lines.append("")
        
        lines.append("硬件信息：")
        
        manufacturer = run_cmd('cat /sys/class/dmi/id/sys_vendor 2>/dev/null') or "Unknown"
        product_name = run_cmd('cat /sys/class/dmi/id/product_name 2>/dev/null') or "Unknown"
        sncode = run_cmd('dmidecode -s system-serial-number 2>/dev/null') or "Unknown"
        lines.append(f" 1、主机型号：{manufacturer}-{product_name}  主机SN码：{sncode}")
        
        cpu_model = run_cmd("awk -F: '/model name/ {print $2}' /proc/cpuinfo | uniq") or "Unknown"
        cpu_cores = run_cmd("cat /proc/cpuinfo | grep 'processor' | wc -l") or "Unknown"
        cpu_usage = run_cmd("top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'") or "Unknown"
        lines.append(f" 2、CPU型号【{cpu_cores}核】：【{cpu_usage}%】{cpu_model.strip()}")
        
        mem_total = run_cmd("free -g | awk 'NR==2{print $2}'") or "Unknown"
        mem_free = run_cmd("free -g | awk 'NR==2{print $7}'") or "Unknown"
        lines.append(f" 3、总内存/空闲内存: {mem_total} GB / {mem_free} GB")
        
        gpu_name = run_cmd("lspci | grep -i vga | awk -F ':' '{print $3}'") or "Unknown"
        lines.append(f" 4、显卡：{gpu_name.strip()}")
        
        root_size = run_cmd("df -h / | awk 'NR==2{print $2}'") or "Unknown"
        root_avail = run_cmd("df -h / | awk 'NR==2{print $4}'") or "Unknown"
        lines.append(f" 5、系统根目录空间：{root_size}  剩余可用：{root_avail}")
        
        lines.append(" -------------------------")
        disk_info = run_cmd("lsblk -d -o NAME,SIZE,SERIAL --nodeps | grep -v loop | head -6")
        lines.append("磁盘名称    磁盘大小    磁盘SN")
        lines.append(disk_info)
        lines.append(" -------------------------")
        
        net_info = run_cmd("ip -o link show | awk -F': ' '{print $2}' | grep -Ev 'lo|vmnet|docker|utun|virbr0' | head -3")
        if net_info:
            for intf in net_info.split('\n'):
                intf = intf.strip()
                if intf:
                    mac = run_cmd(f"ip link show {intf} | grep link/ether | awk '{{print $2}}'") or "Unknown"
                    lines.append(f" 网卡({intf}): {mac}")
        
        lines.append("")
        lines.append("软件信息：")
        
        systemid = run_cmd("cat /etc/.kyinfo | grep dist_id | awk -F'=| ' '{print $2}'") or "Unknown"
        kylin_serial = run_cmd("cat /etc/.kyinfo | grep key= | awk -F'=' '{print $2}'") or "Unknown"
        
        if os.path.exists("/etc/.kyactivation"):
            service_data = run_cmd("cat /etc/.kyinfo | grep term= | awk -F'=' '{print $2}'")
            service_text = f"技术服务期到：{service_data}" if service_data else "技术服务期未知"
            register = run_cmd("cat /etc/.kyactivation") or "Unknown"
        else:
            service_text = "【系统未激活无技术服务】"
            register = "系统未激活"
        
        lines.append(f" 1、系统服务序列号：{kylin_serial}  {service_text}")
        lines.append(f" 2、当前系统版本是：{systemid}")
        
        kernel = run_cmd("uname -r") or "Unknown"
        lines.append(f" 3、当前内核版本是：{kernel}")
        
        systemtime = run_cmd("date -r /var/log/installer 2>/dev/null") or "Unknown"
        lines.append(f" 4、系统安装时间是：{systemtime}")
        
        buildid = run_cmd("cat /etc/kylin-build | grep buildid 2>/dev/null") or "Unknown"
        lines.append(f" 5、系统build-id是：{buildid}")
        
        kyhwid = run_cmd("cat /etc/.kyhwid 2>/dev/null") or "Unknown"
        lines.append(f" 6、操作系统硬件码：{kyhwid}")
        
        reg_code = run_cmd("kylin_gen_register 2>/dev/null") or "Unknown"
        lines.append(f" 7、操作系统注册码：{reg_code}")
        
        lines.append(f" 8、操作系统激活码：{register}")
        lines.append("")
        
        return "\n".join(lines)


# ==================== Kylin Cleanup 清理功能集成 ====================

class CleanupCommands:
    DEFAULT_CONFIG = {
        'CLEANUP_TIME': '18:00',
        'NOTIFICATION_MINUTES': '5',
        'SHUTDOWN_TIME': '20:00',
        'SHUTDOWN_ENABLED': 'yes',
        'SHUTDOWN_NOTIFICATION_MINUTES': '10',
        'CLEANUP_EXTENSIONS': '.tmp,.log,.bak,.cache,.swp,.xlsx,.xls,.doc,.docx,.jpg,.jpeg,.rar,.zip,.ppt,.pdf,.pptx,.png,.txt,.wps,.wpt,.et,.ett,.dps,.dpt,.ofd',
        'EXCLUDE_EXTENSIONS': '.ico,.desktop',
        'CLEANUP_MODE': 'all',
        'CLEANUP_DIRS': 'Desktop,Downloads,Documents,Pictures,Videos,Trash',
        'CLEANUP_BROWSERS': 'yes',
        'CLEANUP_SYS_APT': 'no',
        'CLEANUP_SYS_JOURNAL': 'no',
        'CLEANUP_SYS_THUMBNAILS': 'no',
        'CLEANUP_FREQUENCY': 'daily',
        'CLEANUP_ON_BOOT': 'no',
        'CLEANUP_INTERVAL': '0'
    }

    CONFIG_FILE = "/etc/kylin-clean/config.sh"

    @staticmethod
    def load_config():
        config = CleanupCommands.DEFAULT_CONFIG.copy()
        if os.path.exists(CleanupCommands.CONFIG_FILE):
            try:
                with open(CleanupCommands.CONFIG_FILE, 'r') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            k, v = line.strip().split('=', 1)
                            config[k.strip()] = v.strip().strip('"')
            except Exception as e:
                pass
        return config

    @staticmethod
    def save_config(config):
        config_str = f'''# Kylin / openKylin 清理工具配置文件
CLEANUP_TIME="{config.get('CLEANUP_TIME', '18:00')}"
NOTIFICATION_MINUTES="{config.get('NOTIFICATION_MINUTES', '5')}"
SHUTDOWN_TIME="{config.get('SHUTDOWN_TIME', '20:00')}"
SHUTDOWN_ENABLED="{config.get('SHUTDOWN_ENABLED', 'yes')}"
CLEANUP_EXTENSIONS="{config.get('CLEANUP_EXTENSIONS', '.tmp,.log,.bak,.cache,.swp')}"
EXCLUDE_EXTENSIONS="{config.get('EXCLUDE_EXTENSIONS', '.ico,.desktop')}"
CLEANUP_MODE="{config.get('CLEANUP_MODE', 'all')}"
CLEANUP_DIRS="{config.get('CLEANUP_DIRS', 'Desktop,Downloads,Documents,Pictures,Videos,Trash')}"
CLEANUP_BROWSERS="{config.get('CLEANUP_BROWSERS', 'yes')}"
CLEANUP_SYS_APT="{config.get('CLEANUP_SYS_APT', 'no')}"
CLEANUP_SYS_JOURNAL="{config.get('CLEANUP_SYS_JOURNAL', 'no')}"
CLEANUP_SYS_THUMBNAILS="{config.get('CLEANUP_SYS_THUMBNAILS', 'no')}"
CLEANUP_FREQUENCY="{config.get('CLEANUP_FREQUENCY', 'daily')}"
CLEANUP_ON_BOOT="{config.get('CLEANUP_ON_BOOT', 'no')}"
CLEANUP_INTERVAL="{config.get('CLEANUP_INTERVAL', '0')}"
'''
        try:
            auth_service = AuthService()
            
            cmd = ['tee', CleanupCommands.CONFIG_FILE]
            result = auth_service.execute(cmd, config_str)
            
            if result.get('success'):
                return {'status': 'success', 'message': '配置保存成功'}
            else:
                error_msg = result.get('error', result.get('stderr', 'Unknown error'))
                return {'status': 'error', 'message': f'保存配置失败: {error_msg}'}
        except Exception as e:
            return {'status': 'error', 'message': f'保存配置失败: {str(e)}'}

    @staticmethod
    def get_regular_users():
        users = set()
        try:
            import pwd
            for p in pwd.getpwall():
                if 1000 <= p.pw_uid < 65534 and os.path.isdir(p.pw_dir):
                    users.add(p.pw_name)
        except:
            pass
        
        if os.path.isdir("/home"):
            try:
                for entry in os.listdir("/home"):
                    if entry not in users and os.path.isdir(os.path.join("/home", entry)):
                        if not entry.startswith('.'):
                            users.add(entry)
            except:
                pass
        return list(users) if users else ["kylin", "openkylin"]

    @staticmethod
    def get_compiled_extension_rules(config):
        mode = config.get('CLEANUP_MODE', 'all')
        cleanups = tuple([e.strip().lower() for e in config.get('CLEANUP_EXTENSIONS', '').split(',') if e.strip()])
        excludes = tuple([e.strip().lower() for e in config.get('EXCLUDE_EXTENSIONS', '').split(',') if e.strip()])
        return mode, cleanups, excludes

    @staticmethod
    def should_delete(filename, rules):
        mode, cleanup_exts, exclude_exts = rules
        name_lower = filename.lower()
        
        if name_lower.endswith(exclude_exts):
            return False
            
        if mode == 'ext_only':
            return name_lower.endswith(cleanup_exts)
        else:
            return True

    @staticmethod
    def cleanup_directory_safe(path, rules):
        deleted_count = 0
        if not os.path.exists(path):
            return deleted_count
            
        try:
            for root, dirs, files in os.walk(path, topdown=False):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for filename in files:
                    file_path = os.path.join(root, filename)
                    if os.path.islink(file_path):
                        continue
                    
                    if CleanupCommands.should_delete(filename, rules):
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except:
                            pass
                            
                if root != path:
                    try:
                        if not os.listdir(root):
                            os.rmdir(root)
                    except:
                        pass
        except:
            pass
            
        return deleted_count

    @staticmethod
    def clear_recycle_bin(username, config):
        target_dirs = config.get('CLEANUP_DIRS', '').split(',')
        if 'Trash' not in target_dirs:
            return 0

        trash_path = f"/home/{username}/.local/share/Trash/"
        deleted_count = 0
        if os.path.exists(trash_path):
            paths = [os.path.join(trash_path, "files"), os.path.join(trash_path, "info")]
            for p in paths:
                if os.path.exists(p):
                    try:
                        import shutil
                        for item in os.listdir(p):
                            item_path = os.path.join(p, item)
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                                deleted_count += len(os.listdir(item_path)) if os.path.exists(item_path) else 0
                            else:
                                os.remove(item_path)
                                deleted_count += 1
                    except:
                        pass
        return deleted_count

    @staticmethod
    def clear_browser_caches(username):
        cache_paths = [
            f"/home/{username}/.cache/mozilla/firefox",
            f"/home/{username}/.cache/chromium/Default/Cache",
            f"/home/{username}/.cache/google-chrome/Default/Cache",
            f"/home/{username}/.cache/microsoft-edge/Default/Cache",
            f"/home/{username}/.cache/BraveSoftware/Brave-Browser/Default/Cache",
            f"/home/{username}/.cache/360se",
            f"/home/{username}/.cache/qaxbrowser"
        ]
        
        deleted_count = 0
        for base_path in cache_paths:
            if os.path.exists(base_path) and os.path.isdir(base_path):
                try:
                    import shutil
                    for item in os.listdir(base_path):
                        item_path = os.path.join(base_path, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                        deleted_count += 1
                except:
                    pass
                    
        return deleted_count

    @staticmethod
    def clear_thumbnails(username):
        thumb_path = f"/home/{username}/.cache/thumbnails"
        deleted_count = 0
        if os.path.exists(thumb_path) and os.path.isdir(thumb_path):
            try:
                import shutil
                for item in os.listdir(thumb_path):
                    item_path = os.path.join(thumb_path, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                    deleted_count += 1
            except:
                pass
        return deleted_count

    @staticmethod
    def clear_system_garbage(apt_enabled, journal_enabled):
        commands = []
        
        if apt_enabled:
            commands.extend([
                ["apt-get", "clean"],
                ["apt-get", "autoremove", "-y"]
            ])
            
        if journal_enabled:
            commands.extend([
                ["journalctl", "--vacuum-time=7d"],
                ["journalctl", "--vacuum-size=100M"]
            ])
            
        results = []
        for cmd in commands:
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                results.append(f"执行: {' '.join(cmd)} - 成功")
            except Exception as e:
                results.append(f"执行: {' '.join(cmd)} - 失败: {str(e)}")
        
        return results

    @staticmethod
    def run_cleanup(config=None):
        try:
            result = subprocess.run(
                ['pkexec', 'python3', '/opt/kylin-clean/clean_linux.py', '--once'],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                return {'status': 'success', 'data': {'log': result.stdout}}
            else:
                return {'status': 'error', 'message': f'清理失败: {result.stderr}'}
        except subprocess.TimeoutExpired:
            return {'status': 'error', 'message': '清理操作超时'}
        except Exception as e:
            return {'status': 'error', 'message': f'执行清理失败: {str(e)}'}

    @staticmethod
    def get_cleanup_config():
        try:
            config = CleanupCommands.load_config()
            return {'status': 'success', 'data': config}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def update_cleanup_config(config_updates):
        try:
            config = CleanupCommands.load_config()
            config.update(config_updates)
            return CleanupCommands.save_config(config)
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_cleanup_status():
        try:
            result = subprocess.run(["systemctl", "is-active", "kylin-clean-tools.service"],
                                   capture_output=True, text=True)
            active = result.returncode == 0
            
            result = subprocess.run(["systemctl", "is-enabled", "kylin-clean-tools.service"],
                                   capture_output=True, text=True)
            enabled = result.returncode == 0
            
            return {'status': 'success', 'data': {
                'active': active,
                'enabled': enabled,
                'status_text': '运行中' if active else '已停止',
                'enabled_text': '已启用' if enabled else '已禁用'
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e), 'data': {
                'active': False,
                'enabled': False,
                'status_text': '未知',
                'enabled_text': '未知'
            }}

    @staticmethod
    def control_cleanup_service(action):
        try:
            import shutil
            elevate_cmd = ["pkexec"]
            for cmd in ["pkexec", "kysec-polkit", "kdesu", "gksudo", "sudo"]:
                if shutil.which(cmd):
                    elevate_cmd = [cmd]
                    break
            
            cmd = elevate_cmd + ["systemctl", action, "kylin-clean-tools.service"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                action_text = {
                    'start': '启动',
                    'stop': '停止',
                    'restart': '重启',
                    'enable': '启用',
                    'disable': '禁用'
                }
                return {'status': 'success', 'message': f'服务已{action_text.get(action, action)}'}
            else:
                stderr = result.stderr.strip() if result.stderr else ''
                stdout = result.stdout.strip() if result.stdout else ''
                error_msg = stderr if stderr else stdout
                if not error_msg:
                    error_msg = '操作失败'
                return {'status': 'error', 'message': error_msg}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}