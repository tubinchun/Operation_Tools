#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import json
import logging
import subprocess
import os
import platform
import datetime
import psutil
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.commands import CleanupCommands

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


class KylinServer:
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
            logger.info(f"Kylin Server started on {self.host}:{self.port}")
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
    def get_cpu_info(params):
        try:
            cpu_count = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_percent = psutil.cpu_percent(interval=1)
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
            cpu_data['cpuinfo_raw'] = proc_cpuinfo

            return {'status': 'success', 'data': cpu_data}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_memory_info(params):
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
            mem_data['meminfo_raw'] = proc_meminfo

            return {'status': 'success', 'data': mem_data}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_disk_info(params):
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
                'df_output': df_output,
            }
            return {'status': 'success', 'data': disk_data}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_network_info(params):
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
                'ip_output': ip_output,
                'route_output': route_output,
            }
            return {'status': 'success', 'data': network_data}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_process_list(params):
        try:
            limit = params.get('limit', 20)
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
                'ps_output': ps_output,
                'total_processes': len(processes),
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_service_list(params):
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
                'systemctl_output': systemctl_output,
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def restart_network(params):
        try:
            output, success = run_cmd('systemctl restart NetworkManager')
            if success:
                return {'status': 'success', 'message': '网络服务已重启'}
            return {'status': 'error', 'message': output}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def execute_command(params):
        try:
            cmd = params.get('command', '')
            if not cmd:
                return {'status': 'error', 'message': 'No command provided'}

            dangerous_cmds = ['rm -rf', 'mkfs', 'dd if=', ':(){:|:&};:']
            for dangerous in dangerous_cmds:
                if dangerous in cmd:
                    return {'status': 'error', 'message': 'Command not allowed for security reasons'}

            output, success = run_cmd(cmd)
            return {'status': 'success', 'data': {'output': output, 'success': success}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_kysec_status(params):
        try:
            output, success = run_cmd('kysec status')
            return {'status': 'success', 'data': {'kysec': output}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def set_kysec(params):
        try:
            action = params.get('action', '')
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
    def get_users(params):
        try:
            passwd_output, _ = run_cmd('cat /etc/passwd')
            shadow_output, _ = run_cmd('sudo cat /etc/shadow')

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
                'passwd_raw': passwd_output,
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_login_history(params):
        try:
            last_output, _ = run_cmd('last -20')
            who_output, _ = run_cmd('who')
            return {'status': 'success', 'data': {
                'last': last_output,
                'who': who_output,
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_apt_sources(params):
        try:
            sources_list, _ = run_cmd('cat /etc/apt/sources.list')
            sources_d, _ = run_cmd('ls /etc/apt/sources.list.d/')
            return {'status': 'success', 'data': {
                'sources_list': sources_list,
                'sources_d': sources_d,
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_installed_packages(params):
        try:
            packages, _ = run_cmd('dpkg -l')
            return {'status': 'success', 'data': {'packages': packages}}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def cleanup_logs(params):
        try:
            run_cmd('journalctl --vacuum-time=7d')
            run_cmd('rm -rf /var/log/*.gz')
            run_cmd('rm -rf /var/log/syslog.*')
            return {'status': 'success', 'message': '日志清理完成'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_system_logs(params):
        try:
            lines = params.get('lines', 100)
            logs, _ = run_cmd(f'journalctl -n {lines}')
            dmesg, _ = run_cmd('dmesg | tail -50')
            return {'status': 'success', 'data': {
                'journalctl': logs,
                'dmesg': dmesg,
            }}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_system_stats(params):
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
    def get_detailed_system_info(params):
        try:
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'core', 'kylin_desktop_system_info.sh'),
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
            else:
                return {'status': 'success', 'data': {'output': KylinServerCommands._get_system_info_python(), 'error': ''}}
        except subprocess.TimeoutExpired:
            return {'status': 'error', 'message': '执行超时'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def _get_system_info_python():
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

    @staticmethod
    def run_cleanup(params):
        try:
            return CleanupCommands.run_cleanup()
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_cleanup_config(params):
        try:
            return CleanupCommands.get_cleanup_config()
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def update_cleanup_config(params):
        try:
            config = params.get('config', {})
            return CleanupCommands.update_cleanup_config(config)
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_cleanup_status(params):
        try:
            return CleanupCommands.get_cleanup_status()
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def control_cleanup_service(params):
        try:
            action = params.get('action', '')
            return CleanupCommands.control_cleanup_service(action)
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Kylin System Tools Server')
    parser.add_argument('--host', default='0.0.0.0', help='Bind address')
    parser.add_argument('--port', type=int, default=29876, help='Bind port')
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
    server.register_handler('get_system_stats', KylinServerCommands.get_system_stats)
    server.register_handler('get_detailed_system_info', KylinServerCommands.get_detailed_system_info)
    server.register_handler('run_cleanup', KylinServerCommands.run_cleanup)
    server.register_handler('get_cleanup_config', KylinServerCommands.get_cleanup_config)
    server.register_handler('update_cleanup_config', KylinServerCommands.update_cleanup_config)
    server.register_handler('get_cleanup_status', KylinServerCommands.get_cleanup_status)
    server.register_handler('control_cleanup_service', KylinServerCommands.control_cleanup_service)

    print(f"银河麒麟运维管理工具服务端启动中...")
    print(f"监听地址: {args.host}:{args.port}")

    try:
        server.start()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        server.stop()


if __name__ == '__main__':
    main()
