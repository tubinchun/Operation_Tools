#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json
import threading
import io
import os
import sys
import socket
import logging
import logging.handlers
import signal
import glob
import time
import struct
import shutil
import datetime
import tempfile
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor, as_completed
import ctypes
import queue

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services import tftp
from services import dhcp
from services import helpers

class PXECommands:
    SETTINGS = {
        'NETBOOT_DIR': 'netboot',
        'NETBOOT_FILE': '',
        'DHCP_SERVER_IP': '192.168.2.2',
        'DHCP_SERVER_PORT': 67,
        'DHCP_SERVER_NIC': '',
        'DHCP_OFFER_BEGIN': '192.168.2.100',
        'DHCP_OFFER_END': '192.168.2.150',
        'DHCP_SUBNET': '255.255.255.0',
        'DHCP_DNS': '8.8.8.8',
        'DHCP_ROUTER': '192.168.2.1',
        'DHCP_BROADCAST': '',
        'DHCP_FILESERVER': '192.168.2.2',
        'DHCP_WHITELIST': [],
        'DHCP_BLACKLIST': [],
        'HTTP_PORT': 80,
        'TFTP_PORT': 69,
        'DHCP_MODE_PROXY': False,
        'LOG_LEVEL': 'INFO',
        'MODE_VERBOSE': '',
        'USE_DHCP': True,
        'USE_HTTP': True,
        'USE_IPXE': True,
        'MENU_DEFAULT': '',
        'MENU_TIMEOUT': '1200'
    }

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PXECommands, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.monitor = None
        self.tftp_server = None
        self.dhcp_server = None
        self.http_server = None
        self.tftp_logger = None
        self.dhcp_logger = None
        self.http_logger = None
        self.sys_logger = logging.getLogger('PXE-Service')
        self.running = False
        self.msg_queue = queue.Queue()
        self._init_directories()

    def _init_directories(self):
        self._config_dir = os.environ.get('KYLIN_CONFIG_DIR', '/etc/kylin-system-tools/pxe')
        self._iso_dir = '/var/lib/kylin-system-tools/pxe/iso'
        self._log_dir = os.environ.get('KYLIN_LOG_DIR', '/var/log/kylin-system-tools')
        self._image_config_dir = os.path.join(self._config_dir, 'images')
        
        if not os.path.exists(self._config_dir):
            try:
                os.makedirs(self._config_dir, exist_ok=True)
            except PermissionError:
                self._config_dir = os.path.join(os.path.dirname(__file__), 'config')
                os.makedirs(self._config_dir, exist_ok=True)
        
        if not os.path.exists(self._iso_dir):
            try:
                os.makedirs(self._iso_dir, exist_ok=True)
                os.chmod(self._iso_dir, 0o775)
            except PermissionError:
                self._iso_dir = os.path.join(os.path.dirname(__file__), 'iso')
                os.makedirs(self._iso_dir, exist_ok=True)
        
        if not os.path.exists(self._image_config_dir):
            try:
                os.makedirs(self._image_config_dir, exist_ok=True)
                os.chmod(self._image_config_dir, 0o775)
            except PermissionError:
                self._image_config_dir = os.path.join(os.path.dirname(__file__), 'config', 'images')
                os.makedirs(self._image_config_dir, exist_ok=True)
        
        if not os.path.exists(self._log_dir):
            try:
                os.makedirs(self._log_dir, exist_ok=True)
            except PermissionError:
                self._log_dir = os.path.join(os.path.dirname(__file__), 'logs')
                os.makedirs(self._log_dir, exist_ok=True)
        
        self._pxe_mount_dir = os.path.join(os.path.dirname(__file__), 'netboot', 'pxenfsroot')
        if not os.path.exists(self._pxe_mount_dir):
            try:
                os.makedirs(self._pxe_mount_dir, exist_ok=True)
            except:
                pass
    
    def _mount_iso(self, iso_path, mount_point):
        try:
            subprocess.run(['umount', '-q', '-l', mount_point], 
                         capture_output=True, timeout=10)
            result = subprocess.run(
                ['mount', '-o', 'ro', iso_path, mount_point],
                capture_output=True, timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            self.sys_logger.error(f"挂载ISO失败: {e}")
            return False
    
    def _unmount_iso(self, mount_point):
        try:
            subprocess.run(['umount', '-q', '-l', mount_point], 
                         capture_output=True, timeout=10)
            return True
        except Exception as e:
            self.sys_logger.error(f"卸载ISO失败: {e}")
            return False
    
    def _read_iso_file(self, iso_path, file_path_in_iso):
        iso_mount_point = os.path.join(self._pxe_mount_dir, 'temp_iso_mount')
        try:
            os.makedirs(iso_mount_point, exist_ok=True)
            
            if not self._mount_iso(iso_path, iso_mount_point):
                return None
            
            full_path = os.path.join(iso_mount_point, file_path_in_iso)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                self._unmount_iso(iso_mount_point)
                return content
            
            self._unmount_iso(iso_mount_point)
            return None
        except Exception as e:
            self.sys_logger.error(f"读取ISO内文件失败: {e}")
            self._unmount_iso(iso_mount_point)
            return None
    
    def _find_ks_file(self, iso_path):
        ks_files = [
            'ky-installer.cfg',
            'anaconda-ks.cfg',
            'ks.cfg',
            'kickstart.cfg'
        ]
        
        iso_mount_point = os.path.join(self._pxe_mount_dir, 'temp_iso_mount')
        try:
            os.makedirs(iso_mount_point, exist_ok=True)
            
            if not self._mount_iso(iso_path, iso_mount_point):
                return None, None
            
            found_path = None
            found_content = None
            
            for ks_file in ks_files:
                full_path = os.path.join(iso_mount_point, ks_file)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            found_content = f.read()
                        found_path = ks_file
                        break
                    except:
                        continue
            
            for root, dirs, files in os.walk(iso_mount_point):
                for file in files:
                    if file in ks_files and file != found_path:
                        full_path = os.path.join(root, file)
                        try:
                            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            rel_path = os.path.relpath(full_path, iso_mount_point)
                            found_content = content
                            found_path = rel_path
                            break
                        except:
                            continue
                if found_path:
                    break
            
            self._unmount_iso(iso_mount_point)
            return found_path, found_content
        except Exception as e:
            self.sys_logger.error(f"查找KS文件失败: {e}")
            self._unmount_iso(iso_mount_point)
            return None, None
    
    def _find_grub_file(self, iso_path):
        grub_files = ['grub.cfg', 'boot/grub/grub.cfg', 'EFI/BOOT/grub.cfg']
        
        iso_mount_point = os.path.join(self._pxe_mount_dir, 'temp_iso_mount')
        try:
            os.makedirs(iso_mount_point, exist_ok=True)
            
            if not self._mount_iso(iso_path, iso_mount_point):
                return None, None
            
            found_path = None
            found_content = None
            
            for grub_file in grub_files:
                full_path = os.path.join(iso_mount_point, grub_file)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            found_content = f.read()
                        found_path = grub_file
                        break
                    except:
                        continue
            
            if not found_path:
                for root, dirs, files in os.walk(iso_mount_point):
                    for file in files:
                        if file == 'grub.cfg':
                            full_path = os.path.join(root, file)
                            try:
                                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                rel_path = os.path.relpath(full_path, iso_mount_point)
                                found_content = content
                                found_path = rel_path
                                break
                            except:
                                continue
                    if found_path:
                        break
            
            self._unmount_iso(iso_mount_point)
            return found_path, found_content
        except Exception as e:
            self.sys_logger.error(f"查找GRUB文件失败: {e}")
            self._unmount_iso(iso_mount_point)
            return None, None
    
    def extract_iso_config(self, params=None):
        try:
            iso_name = params.get('iso_name', '') if params else ''
            
            if not iso_name:
                return {'status': 'error', 'message': 'ISO名称不能为空'}
            
            iso_path = os.path.join(self._iso_dir, iso_name)
            if not os.path.exists(iso_path):
                return {'status': 'error', 'message': 'ISO文件不存在'}
            
            ks_path, ks_content = self._find_ks_file(iso_path)
            grub_path, grub_content = self._find_grub_file(iso_path)
            
            return {
                'status': 'success',
                'data': {
                    'ks_path': ks_path,
                    'ks_content': ks_content or '',
                    'grub_path': grub_path,
                    'grub_content': grub_content or ''
                }
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _parse_mac_list(self, mac_str):
        mac_list = []
        if not mac_str:
            return mac_list
        
        for line in mac_str.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            line = line.replace(',', ' ').replace(';', ' ').replace('\t', ' ')
            parts = line.split()
            for part in parts:
                part = part.strip().upper()
                if not part:
                    continue
                
                part = part.replace('-', ':').replace('.', ':')
                if len(part) == 17:
                    mac_list.append(part)
                elif len(part) == 12:
                    formatted = ':'.join([part[i:i+2] for i in range(0, 12, 2)])
                    mac_list.append(formatted)
        
        return mac_list
    
    def _get_blackwhitelist_config_path(self):
        return os.path.join(self._config_dir, 'blackwhitelist.json')
    
    def _ensure_config_files(self):
        try:
            leases_path = os.path.join(self._config_dir, 'leases.json')
            if not os.path.exists(leases_path):
                with open(leases_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f, indent=4, ensure_ascii=False)
                os.chmod(leases_path, 0o664)
                self.sys_logger.info(f"已创建leases.json文件: {leases_path}")
            
            config_path = os.path.join(self._config_dir, 'config.json')
            if not os.path.exists(config_path):
                config = {
                    'DHCP_WHITELIST': [],
                    'DHCP_BLACKLIST': [],
                    'DHCP_SERVER_NIC': '',
                    'DHCP_SERVER_IP': '',
                    'DHCP_OFFER_BEGIN': '',
                    'DHCP_OFFER_END': '',
                    'DHCP_SUBNET': '255.255.255.0',
                    'DHCP_ROUTER': '',
                    'DHCP_DNS': '',
                    'DHCP_MODE_PROXY': 'true',
                    'HTTP_PORT': '8080',
                    'TFTP_PORT': '69',
                    'USE_IPXE': 'true',
                    'USE_HTTP': 'true',
                    'LOG_LEVEL': 'INFO'
                }
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                os.chmod(config_path, 0o664)
                self.sys_logger.info(f"已创建config.json文件: {config_path}")
            
            blackwhitelist_path = self._get_blackwhitelist_config_path()
            if not os.path.exists(blackwhitelist_path):
                config = {
                    'whitelist': [],
                    'blacklist': [],
                    'updated_at': datetime.datetime.now().isoformat()
                }
                with open(blackwhitelist_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                os.chmod(blackwhitelist_path, 0o664)
                self.sys_logger.info(f"已创建blackwhitelist.json文件: {blackwhitelist_path}")
            
        except Exception as e:
            self.sys_logger.error(f"确保配置文件存在失败: {e}")
    
    def set_blackwhitelist(self, params=None):
        try:
            whitelist_str = params.get('whitelist', '') if params else ''
            blacklist_str = params.get('blacklist', '') if params else ''
            
            whitelist = self._parse_mac_list(whitelist_str)
            blacklist = self._parse_mac_list(blacklist_str)
            
            config = {
                'whitelist': whitelist,
                'blacklist': blacklist,
                'updated_at': datetime.datetime.now().isoformat()
            }
            
            config_path = self._get_blackwhitelist_config_path()
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            os.chmod(config_path, 0o644)
            
            self.sys_logger.info(f"黑白名单已更新 - 白名单: {len(whitelist)}个, 黑名单: {len(blacklist)}个")
            
            return {'status': 'success', 'message': f'黑白名单已保存 - 白名单: {len(whitelist)}个MAC地址, 黑名单: {len(blacklist)}个MAC地址'}
        except Exception as e:
            self.sys_logger.error(f"保存黑白名单失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_blackwhitelist(self, params=None):
        try:
            config_path = self._get_blackwhitelist_config_path()
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                whitelist = '\n'.join(config.get('whitelist', []))
                blacklist = '\n'.join(config.get('blacklist', []))
                
                return {
                    'status': 'success',
                    'data': {
                        'whitelist': whitelist,
                        'blacklist': blacklist
                    }
                }
            else:
                return {
                    'status': 'success',
                    'data': {
                        'whitelist': '',
                        'blacklist': ''
                    }
                }
        except Exception as e:
            self.sys_logger.error(f"读取黑白名单失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _setup_logging(self):
        log_file = os.path.join(self._log_dir, 'pxe.log')
        handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s %(message)s')
        handler.setFormatter(formatter)
        self.sys_logger.addHandler(handler)
        log_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self.sys_logger.setLevel(log_levels.get(self.SETTINGS['LOG_LEVEL'].upper(), logging.INFO))

    def load_config(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(self._config_dir, 'config.json')
        
        default_config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
        if not os.path.exists(config_path) and os.path.exists(default_config_path):
            try:
                shutil.copy(default_config_path, config_path)
            except:
                pass
        
        if os.path.exists(config_path):
            try:
                with io.open(config_path, 'r', encoding='utf-8') as config_file:
                    loaded_config = json.load(config_file)
                for key, value in loaded_config.items():
                    if key in self.SETTINGS:
                        self.SETTINGS[key] = value
            except (IOError, ValueError) as e:
                self.sys_logger.error(f"Failed to load config: {e}")
        
        return SimpleNamespace(**self.SETTINGS)

    def _check_samba_service(self):
        try:
            result = subprocess.run(
                ['systemctl', 'status', 'smbd'],
                capture_output=True, text=True
            )
            if "Unit smbd.service could not be found" in result.stderr:
                return {'status': 'error', 'message': '请先安装Samba服务: sudo apt install samba'}
            return {'status': 'success', 'message': 'Samba服务已安装'}
        except Exception as e:
            return {'status': 'error', 'message': f'检查Samba服务状态时出错: {e}'}

    def _run_privileged_command(self, cmd):
        try:
            result = subprocess.run(
                ['pkexec'] + cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result
        except subprocess.TimeoutExpired:
            return None
    
    def _configure_samba_share(self):
        samba_config = """[pxe-share]
   comment = PXE Network Boot Share
   path = {netboot_path}
   browsable = yes
   read only = yes
   guest ok = yes
   create mask = 0755
   directory mask = 0755
""".format(netboot_path=os.path.join(os.path.dirname(__file__), 'netboot'))
        
        try:
            # Check if config already exists
            result = subprocess.run(
                ['grep', '-q', '\[pxe-share\]', '/etc/samba/smb.conf'],
                capture_output=True
            )
            
            if result.returncode != 0:
                config_file = '/etc/samba/smb.conf'
                try:
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as script_file:
                        script_file.write(f'''#!/bin/bash
# Append Samba config safely
cp -f {config_file} {config_file}.bak
cat >> {config_file} << 'EOF'

{samba_config}
EOF
''')
                        script_path = script_file.name
                    
                    os.chmod(script_path, 0o755)
                    result = self._run_privileged_command(['bash', script_path])
                    
                    try:
                        os.unlink(script_path)
                    except:
                        pass
                    
                    if result is None:
                        return {'status': 'error', 'message': '操作超时'}
                    if result.returncode != 0:
                        return {'status': 'error', 'message': f'写入Samba配置失败'}
                except Exception as write_error:
                    self.sys_logger.error(f"写入Samba配置失败: {write_error}")
                    return {'status': 'error', 'message': f'写入Samba配置失败: {write_error}'}
            
            # Only restart if services are not running
            try:
                result = self._run_privileged_command(['systemctl', 'is-active', '--quiet', 'smbd'])
                if result is None or result.returncode != 0:
                    self.sys_logger.info("SMBD is not running, starting...")
                    result = self._run_privileged_command(['systemctl', 'start', 'smbd'])
                else:
                    self.sys_logger.info("SMBD is already running, restarting...")
                    result = self._run_privileged_command(['systemctl', 'restart', 'smbd'])
                
                if result is None:
                    return {'status': 'error', 'message': '操作超时'}
                if result.returncode != 0:
                    self.sys_logger.warning(f"重启smbd服务失败: {result.stderr}")
                    # Continue without failing, as Samba might not be needed for basic PXE
                
                result = self._run_privileged_command(['systemctl', 'is-active', '--quiet', 'nmbd'])
                if result is None or result.returncode != 0:
                    self.sys_logger.info("NMBD is not running, starting...")
                    result = self._run_privileged_command(['systemctl', 'start', 'nmbd'])
                else:
                    self.sys_logger.info("NMBD is already running, restarting...")
                    result = self._run_privileged_command(['systemctl', 'restart', 'nmbd'])
                
                if result is None:
                    return {'status': 'error', 'message': '操作超时'}
                if result.returncode != 0:
                    self.sys_logger.warning(f"重启nmbd服务失败: {result.stderr}")
                    # Continue without failing
            except Exception as restart_error:
                self.sys_logger.warning(f"重启Samba服务出错: {restart_error}")
                # Continue without failing
            
            return {'status': 'success', 'message': 'Samba共享配置成功'}
        except Exception as e:
            self.sys_logger.error(f'Samba配置出错: {e}')
            # Don't fail the entire PXE startup because of Samba
            return {'status': 'success', 'message': 'Samba配置可能有问题，但PXE其他功能可用'}

    def _start_samba(self):
        check_result = self._check_samba_service()
        if check_result['status'] == 'error':
            return check_result
        
        return self._configure_samba_share()

    def _stop_samba(self):
        try:
            subprocess.run(['systemctl', 'stop', 'smbd'], capture_output=True)
            subprocess.run(['systemctl', 'stop', 'nmbd'], capture_output=True)
            return {'status': 'success', 'message': 'Samba服务已停止'}
        except Exception as e:
            return {'status': 'error', 'message': f'停止Samba服务失败: {e}'}

    def start_pxe_services(self, params=None):
        if self.running:
            return {'status': 'error', 'message': 'PXE服务已在运行'}

        try:
            working_dir = os.path.dirname(__file__)
            
            args = self.load_config()
            self._setup_logging()
            
            if not os.path.exists(self._config_dir):
                if os.access(self._config_dir, os.W_OK):
                    target_dir = self._config_dir
                else:
                    target_dir = os.path.join(working_dir, 'config')
            else:
                if os.access(self._config_dir, os.W_OK):
                    target_dir = self._config_dir
                else:
                    target_dir = os.path.join(working_dir, 'config')
            
            os.makedirs(target_dir, exist_ok=True)
            
            relative_config_dir = os.path.join(working_dir, 'config')
            if not os.path.exists(relative_config_dir):
                if target_dir != relative_config_dir:
                    try:
                        os.symlink(target_dir, relative_config_dir)
                    except:
                        pass
            
            self._ensure_config_files()
            
            iso_pattern = os.path.join(self._iso_dir, '*.iso')
            if not glob.glob(iso_pattern):
                return {'status': 'error', 'message': 'iso文件夹中未发现镜像文件，请将镜像文件上传至iso文件夹后重新运行服务。'}

            samba_result = self._start_samba()
            if samba_result['status'] == 'error':
                return samba_result

            scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
            gen_script = os.path.join(scripts_dir, 'gen_boot_ipxe.sh')
            if os.path.exists(gen_script):
                subprocess.run(['bash', gen_script], capture_output=True, text=True)

            self.tftp_logger = helpers.get_child_logger(self.sys_logger, 'TFTP')
            self.tftp_server = tftp.TFTPD(
                log_level=args.LOG_LEVEL,
                logger=self.tftp_logger,
                netboot_directory=os.path.join(os.path.dirname(__file__), args.NETBOOT_DIR),
                port=args.TFTP_PORT,
                ip='0.0.0.0'
            )

            self.dhcp_logger = helpers.get_child_logger(self.sys_logger, 'DHCP')
            
            os.makedirs(self._config_dir, exist_ok=True)
            original_cwd = os.getcwd()
            os.chdir(self._config_dir)
            
            self.dhcp_server = dhcp.DHCPD(
                nic=args.DHCP_SERVER_NIC,
                ip=args.DHCP_SERVER_IP,
                port=args.DHCP_SERVER_PORT,
                offer_from=args.DHCP_OFFER_BEGIN,
                offer_to=args.DHCP_OFFER_END,
                subnet_mask=args.DHCP_SUBNET,
                router=args.DHCP_ROUTER,
                dns_server=args.DHCP_DNS,
                broadcast=args.DHCP_BROADCAST,
                file_server=args.DHCP_FILESERVER,
                file_name=args.NETBOOT_FILE,
                use_ipxe=args.USE_IPXE,
                use_http=args.USE_HTTP,
                mode_proxy=args.DHCP_MODE_PROXY,
                log_level=args.LOG_LEVEL,
                whitelist=args.DHCP_WHITELIST,
                blacklist=args.DHCP_BLACKLIST,
                logger=self.dhcp_logger,
                saveleases=''
            )
            
            os.chdir(original_cwd)

            from services import http
            self.http_logger = helpers.get_child_logger(self.sys_logger, 'HTTP')
            self.http_server = http.HTTPServer(
                "0.0.0.0", args.HTTP_PORT,
                log_level=args.LOG_LEVEL,
                logger=self.http_logger
            )

            self.tftp_thread = threading.Thread(
                target=self.tftp_server.listen,
                args=(self.msg_queue,),
                daemon=True
            )
            self.dhcp_thread = threading.Thread(
                target=self.dhcp_server.listen,
                args=(self.msg_queue,),
                daemon=True
            )
            self.http_thread = threading.Thread(
                target=self.http_server.start,
                args=(self.msg_queue,),
                daemon=True
            )

            self.tftp_thread.start()
            self.dhcp_thread.start()
            self.http_thread.start()

            self.running = True
            return {
                'status': 'success',
                'message': 'PXE服务启动成功',
                'server_ip': args.DHCP_SERVER_IP,
                'http_port': args.HTTP_PORT,
                'tftp_port': args.TFTP_PORT,
                'dhcp_port': args.DHCP_SERVER_PORT
            }
        except Exception as e:
            self.sys_logger.error(f'启动PXE服务失败: {e}', exc_info=True)
            return {'status': 'error', 'message': f'启动PXE服务失败: {e}'}

    def stop_pxe_services(self, params=None):
        if not self.running:
            return {'status': 'error', 'message': 'PXE服务未运行'}

        try:
            if self.tftp_server:
                self.tftp_server.sock.close()
            
            if self.dhcp_server:
                self.dhcp_server.sock.close()
            
            if self.http_server:
                self.http_server.stop()

            self._stop_samba()
            
            self.running = False
            return {'status': 'success', 'message': 'PXE服务已停止'}
        except Exception as e:
            self.sys_logger.error(f'停止PXE服务失败: {e}', exc_info=True)
            return {'status': 'error', 'message': f'停止PXE服务失败: {e}'}

    def get_pxe_status(self, params=None):
        try:
            args = self.load_config()
            
            service_status = {
                'pxe_running': self.running,
                'dhcp': self._check_port_available(args.DHCP_SERVER_PORT, 'udp'),
                'tftp': self._check_port_available(args.TFTP_PORT, 'udp'),
                'http': self._check_port_available(args.HTTP_PORT, 'tcp'),
                'samba': self._check_port_available(139, 'tcp')
            }

            return {
                'status': 'success',
                'data': {
                    'config': self.SETTINGS,
                    'service_status': service_status,
                    'running': self.running
                }
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def update_pxe_config(self, params):
        try:
            required_fields = ['ip_address', 'netmask', 'ip_start', 'ip_end']
            optional_fields = ['gateway', 'name']
            
            if not all(params.get(field) for field in required_fields):
                return {'status': 'error', 'message': '缺少必要参数（IP地址、子网掩码、IP范围）'}
            
            for field in optional_fields:
                if field not in params:
                    params[field] = ''

            config_path = os.path.join(self._config_dir, 'config.json')
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as file:
                    config = json.load(file)
            else:
                config = {}

            config.update({
                "DHCP_FILESERVER": params['ip_address'],
                "DHCP_OFFER_BEGIN": params['ip_start'],
                "DHCP_OFFER_END": params['ip_end'],
                "DHCP_ROUTER": params['gateway'],
                "DHCP_SERVER_IP": params['ip_address'],
                "DHCP_SERVER_NIC": params['name'],
                "DHCP_SUBNET": params['netmask'],
                "TFTP_SERVER_IP": params['ip_address']
            })

            with open(config_path, 'w', encoding='utf-8') as file:
                json.dump(config, file, indent=4)

            return {'status': 'success', 'message': '配置更新成功，请重启服务生效'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def get_client_list(self, params=None):
        try:
            leases_path = os.path.join(self._config_dir, 'leases.json')
            if os.path.exists(leases_path):
                with open(leases_path, 'r', encoding='utf-8') as file:
                    config = json.load(file)
            else:
                config = {}

            client_list = []
            for mac, entry in config.items():
                client_info = {
                    'mac': mac,
                    'ip': entry.get('ip', ''),
                    'isoname': entry.get('isoname', ''),
                    'progress': entry.get('progress', 0),
                    'status': entry.get('msg', '等待开始')
                }
                client_list.append(client_info)

            return {'status': 'success', 'data': client_list}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def get_network_info(self, params=None):
        try:
            nic_info = []
            with open("/proc/net/dev", "r") as f:
                lines = f.readlines()[2:]
                nics = [line.split(":")[0].strip() for line in lines]

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                for nic in nics:
                    try:
                        import fcntl
                        ip_req = struct.pack("256s", nic.encode("utf-8"))
                        ip_data = fcntl.ioctl(sock.fileno(), 0x8915, ip_req)
                        ip_addr = socket.inet_ntoa(ip_data[20:24])

                        mask_req = struct.pack("256s", nic.encode("utf-8"))
                        mask_data = fcntl.ioctl(sock.fileno(), 0x891b, mask_req)
                        netmask = socket.inet_ntoa(mask_data[20:24])

                        if ip_addr != "127.0.0.1":
                            nic_info.append({
                                "name": nic,
                                "ip_address": ip_addr,
                                "netmask": netmask
                            })
                    except Exception:
                        continue

            return {'status': 'success', 'data': nic_info}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _check_port_available(self, port, protocol="tcp"):
        try:
            opt = socket.SOCK_STREAM if protocol == "tcp" else socket.SOCK_DGRAM
            with socket.socket(socket.AF_INET, opt) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
                try:
                    s.bind(('', port))
                    s.close()
                    return "not running"
                except OSError:
                    return "running"
        except Exception:
            return "unknown"

    def rescan_isos(self, params=None):
        try:
            scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
            gen_script = os.path.join(scripts_dir, 'gen_boot_ipxe.sh')
            
            if os.path.exists(gen_script):
                subprocess.run(
                    ['bash', gen_script, '--rescan'],
                    capture_output=True, text=True
                )
            
            return {'status': 'success', 'message': '重新扫描完成'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def get_logs(self, params=None):
        try:
            lines = params.get('lines', 500) if params else 500
            log_type = params.get('type', 'all') if params else 'all'
            
            all_logs = []
            
            log_file = os.path.join(self._log_dir, 'pxe.log')
            if os.path.exists(log_file) and (log_type == 'all' or log_type == 'system'):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
                    log_content = ''.join(all_lines[-lines:])
                    if log_content:
                        all_logs.append(f"=== 系统日志 (pxe.log) ===\n{log_content}\n")
            
            client_log_file = os.path.join(self._log_dir, 'client.log')
            if os.path.exists(client_log_file) and (log_type == 'all' or log_type == 'client'):
                with open(client_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
                    log_content = ''.join(all_lines[-lines:])
                    if log_content:
                        all_logs.append(f"=== 客户端连接日志 (client.log) ===\n{log_content}\n")
            
            dhcp_log_file = os.path.join(self._log_dir, 'dhcp.log')
            if os.path.exists(dhcp_log_file) and (log_type == 'all' or log_type == 'dhcp'):
                with open(dhcp_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
                    log_content = ''.join(all_lines[-lines:])
                    if log_content:
                        all_logs.append(f"=== DHCP日志 (dhcp.log) ===\n{log_content}\n")
            
            if not all_logs:
                return {'status': 'success', 'data': ''}
            
            return {'status': 'success', 'data': '\n'.join(all_logs)}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def start_samba_service(self, params=None):
        try:
            result = self._run_privileged_command(['systemctl', 'enable', 'smbd.service', '--now'])
            if result is None:
                return {'status': 'error', 'message': '操作超时'}
            if result.returncode == 0:
                return {'status': 'success', 'message': 'Samba服务启动并设置开机自启成功'}
            else:
                return {'status': 'error', 'message': f'Samba服务启动失败: {result.stderr}'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def get_iso_list(self, params=None):
        try:
            if not os.path.exists(self._iso_dir):
                os.makedirs(self._iso_dir, exist_ok=True)
            
            iso_files = []
            for filename in os.listdir(self._iso_dir):
                if filename.lower().endswith('.iso'):
                    filepath = os.path.join(self._iso_dir, filename)
                    stat = os.stat(filepath)
                    size = stat.st_size
                    if size >= 1024 * 1024 * 1024:
                        size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
                    elif size >= 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.2f} MB"
                    else:
                        size_str = f"{size / 1024:.2f} KB"
                    
                    mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    
                    iso_files.append({
                        'name': filename,
                        'size': size_str,
                        'mtime': mtime,
                        'path': filepath
                    })
            
            return {
                'status': 'success',
                'data': iso_files,
                'iso_path': self._iso_dir
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def delete_iso_file(self, params):
        try:
            if isinstance(params, str):
                filename = params
            else:
                filename = params.get('filename', '') if params else ''
            
            if not filename:
                return {'status': 'error', 'message': '文件名不能为空'}
            
            if '..' in filename or '/' in filename or '\\' in filename:
                return {'status': 'error', 'message': '非法文件名'}
            
            filepath = os.path.join(self._iso_dir, filename)
            
            if not os.path.exists(filepath):
                return {'status': 'error', 'message': '文件不存在'}
            
            if not os.path.abspath(filepath).startswith(os.path.abspath(self._iso_dir)):
                return {'status': 'error', 'message': '无权访问此文件'}
            
            os.remove(filepath)
            return {'status': 'success', 'message': f'ISO文件 {filename} 删除成功'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def upload_iso_file(self, params):
        try:
            source_path = params.get('source_path', '') if params else ''
            
            if not source_path or not os.path.exists(source_path):
                return {'status': 'error', 'message': '源文件不存在'}
            
            filename = os.path.basename(source_path)
            
            if not os.path.exists(self._iso_dir):
                os.makedirs(self._iso_dir, exist_ok=True)
            
            dest_path = os.path.join(self._iso_dir, filename)
            shutil.copy2(source_path, dest_path)
            
            try:
                ks_path, ks_content = self._find_ks_file(dest_path)
                grub_path, grub_content = self._find_grub_file(dest_path)
                
                if ks_content or grub_content:
                    config = {
                        'ipxename': '',
                        'isoname': filename,
                        'autoinstall': 'true' if ks_content else 'false',
                        'CompatibleMode': 'false',
                        'autoinstallcfg': ks_content or '',
                        'grubcfg': grub_content or '',
                        'extpathname': 'mpxe_extfile',
                        'mpxe_extfile': ''
                    }
                    
                    config_path = self._get_image_config_path(filename)
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=4, ensure_ascii=False)
                    
                    os.chmod(config_path, 0o664)
                    
                    message = f'ISO文件 {filename} 上传成功，已自动提取配置'
                    if ks_path:
                        message += f'\nKS文件: {ks_path}'
                    if grub_path:
                        message += f'\nGRUB文件: {grub_path}'
                    
                    return {'status': 'success', 'message': message}
            except Exception as extract_error:
                self.sys_logger.warning(f"自动提取配置失败: {extract_error}")
            
            return {'status': 'success', 'message': f'ISO文件 {filename} 上传成功'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def open_iso_directory(self, params=None):
        try:
            if not os.path.exists(self._iso_dir):
                os.makedirs(self._iso_dir, exist_ok=True)
            
            subprocess.Popen(['xdg-open', self._iso_dir])
            
            return {'status': 'success', 'message': '已打开ISO目录'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _get_image_config_path(self, iso_name):
        safe_name = ''.join(c for c in iso_name if c.isalnum() or c in '.-_')
        return os.path.join(self._image_config_dir, f'{safe_name}.json')
    
    def get_image_config(self, params=None):
        try:
            if isinstance(params, str):
                iso_name = params
            else:
                iso_name = params.get('iso_name', '') if params else ''
            
            if not iso_name:
                return {'status': 'error', 'message': 'ISO名称不能为空'}
            
            config_path = self._get_image_config_path(iso_name)
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = self._get_default_image_config(iso_name)
            
            self._merge_mpxe_config(config)
            
            return {'status': 'success', 'data': config}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _get_default_image_config(self, iso_name):
        return {
            'ipxename': '',
            'isoname': iso_name,
            'autoinstall': 'false',
            'CompatibleMode': 'false',
            'autoinstallcfg': '',
            'grubcfg': '',
            'extpathname': 'mpxe_extfile',
            'mpxe_extfile': '',
            'class': 'Preseed',
            'kernel_params': '',
            'initrd_params': '',
            'boot_timeout': '60',
            'language': 'zh_CN',
            'keyboard': 'us',
            'timezone': 'Asia/Shanghai',
            'driver_path': '',
            'extra_drivers': '',
            'network_config': '',
            'disk_partition': '',
            'post_install': '',
            'custom_scripts': ''
        }
    
    def _merge_mpxe_config(self, config):
        default_config = self._get_default_image_config(config.get('isoname', ''))
        
        for key, default_value in default_config.items():
            if key not in config:
                config[key] = default_value
        
        if config.get('autoinstall') == 'true' and not config.get('autoinstallcfg'):
            config['autoinstallcfg'] = self._generate_default_autoinstall_config()
        
        if config.get('CompatibleMode') == 'true' and not config.get('grubcfg'):
            config['grubcfg'] = self._generate_compatible_grub_config()
    
    def _generate_default_autoinstall_config(self):
        return """# Kylin Auto Install Configuration
# 继承mpxe自动安装流程

install
cdrom
lang zh_CN.UTF-8
keyboard us
timezone Asia/Shanghai --utc
rootpw --iscrypted $6$rounds=4096$your_hash_here
firewall --disabled
network --bootproto=dhcp --device=eth0
selinux --disabled
authconfig --enableshadow --passalgo=sha512
bootloader --location=mbr --driveorder=sda
zerombr
clearpart --all --initlabel
autopart
reboot

%packages
@^minimal
@core
%end

%post
# 安装后脚本
echo "Installation completed successfully"
%end
"""
    
    def _generate_compatible_grub_config(self):
        return """set timeout=60
set default=0

menuentry 'Kylin Installer (Compatible Mode)' {
    set gfxpayload=keep
    linux /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=KYLIN quiet nomodeset acpi=off pci=noacpi
    initrd /images/pxeboot/initrd.img
}

menuentry 'Kylin Installer (Safe Mode)' {
    set gfxpayload=keep
    linux /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=KYLIN quiet nomodeset acpi=off pci=noacpi xforcevesa
    initrd /images/pxeboot/initrd.img
}

menuentry 'Kylin Installer (Text Mode)' {
    linux /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=KYLIN inst.text quiet
    initrd /images/pxeboot/initrd.img
}
"""
    
    def save_image_config(self, params):
        try:
            iso_name = params.get('iso_name', '')
            if not iso_name:
                return {'status': 'error', 'message': 'ISO名称不能为空'}
            
            config = self._validate_and_clean_config(params)
            
            config_path = self._get_image_config_path(iso_name)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            os.chmod(config_path, 0o664)
            
            self._sync_to_mpxe_format(iso_name, config)
            
            return {'status': 'success', 'message': '配置保存成功'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _validate_and_clean_config(self, params):
        config = {
            'ipxename': params.get('ipxename', '').strip(),
            'isoname': params.get('iso_name', '').strip(),
            'autoinstall': 'true' if params.get('autoinstall', 'false') == 'true' else 'false',
            'CompatibleMode': 'true' if params.get('CompatibleMode', 'false') == 'true' else 'false',
            'autoinstallcfg': params.get('autoinstallcfg', '').strip(),
            'grubcfg': params.get('grubcfg', '').strip(),
            'extpathname': params.get('extpathname', 'mpxe_extfile').strip(),
            'mpxe_extfile': params.get('mpxe_extfile', '').strip(),
            'class': params.get('class', 'Preseed').strip(),
            'kernel_params': params.get('kernel_params', '').strip(),
            'initrd_params': params.get('initrd_params', '').strip(),
            'boot_timeout': params.get('boot_timeout', '60').strip(),
            'language': params.get('language', 'zh_CN').strip(),
            'keyboard': params.get('keyboard', 'us').strip(),
            'timezone': params.get('timezone', 'Asia/Shanghai').strip(),
            'driver_path': params.get('driver_path', '').strip(),
            'extra_drivers': params.get('extra_drivers', '').strip(),
            'network_config': params.get('network_config', '').strip(),
            'disk_partition': params.get('disk_partition', '').strip(),
            'post_install': params.get('post_install', '').strip(),
            'custom_scripts': params.get('custom_scripts', '').strip()
        }
        
        if not config['ipxename']:
            config['ipxename'] = self._generate_ipxename(config['isoname'])
        
        return config
    
    def _generate_ipxename(self, isoname):
        import hashlib
        md5_hash = hashlib.md5()
        md5_hash.update(isoname.encode('utf-8'))
        return md5_hash.hexdigest()[:9]
    
    def _sync_to_mpxe_format(self, iso_name, config):
        try:
            directory = os.path.join(os.path.dirname(__file__), 'netboot', 'config')
            ipxename = config['ipxename']
            config_dir = os.path.join(directory, ipxename)
            
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            config_file = os.path.join(config_dir, 'config.ini')
            extfile_path = os.path.join(config_dir, 'extfile.ini')
            grub_path = os.path.join(config_dir, 'grub.cfg_tpl')
            autoinstall_path = os.path.join(config_dir, 'autoinstall.cfg_tpl')
            
            import configparser
            mpxe_config = configparser.ConfigParser(
                allow_no_value=True,
                delimiters=('='),
                comment_prefixes=('#', ';')
            )
            
            if not mpxe_config.has_section('config'):
                mpxe_config.add_section('config')
            
            mpxe_config.set('config', 'isoname', config['isoname'])
            mpxe_config.set('config', 'extpathname', config['extpathname'])
            mpxe_config.set('config', 'autoinstall', config['autoinstall'])
            mpxe_config.set('config', 'class', config['class'])
            
            with open(config_file, 'w') as f:
                mpxe_config.write(f)
            
            if config['mpxe_extfile']:
                with open(extfile_path, 'w', encoding='utf-8') as f:
                    f.write(config['mpxe_extfile'])
            
            if config['grubcfg']:
                with open(grub_path, 'w', encoding='utf-8') as f:
                    f.write(config['grubcfg'])
            
            if config['autoinstallcfg']:
                with open(autoinstall_path, 'w', encoding='utf-8') as f:
                    f.write(config['autoinstallcfg'])
            
            self.sys_logger.info(f"配置已同步到mpxe格式: {ipxename}")
        except Exception as e:
            self.sys_logger.error(f"同步到mpxe格式失败: {e}")
