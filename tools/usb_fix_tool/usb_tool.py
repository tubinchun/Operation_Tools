#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
银河麒麟v10 U盘只读修复工具
版本: 1.3
描述: 用于检测和修复U盘只读状态的图形化工具 (支持非Root运行 + 提权修复)
"""

import os
import sys
import argparse
import subprocess
import time
import json
import re
from datetime import datetime
import io



# ============================================
# 后端逻辑 (不依赖GUI)
# ============================================

class USBAnalyzer:
    """USB设备分析类"""
    
    @staticmethod
    def get_usb_devices():
        """获取USB存储设备列表"""
        devices = []
        try:
            # 使用lsblk命令获取块设备信息
            result = subprocess.run(['lsblk', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,RO', '-J'], 
                                   capture_output=True, text=True, check=True)
            
            data = json.loads(result.stdout)
            
            for device in data.get('blockdevices', []):
                # 检查是否为USB设备
                if device.get('type') == 'disk' and USBAnalyzer._is_usb_device(device.get('name', '')):
                    device_info = USBAnalyzer._get_device_details(device)
                    if device_info:
                        devices.append(device_info)
                        
        except Exception as e:
            print(f"DEBUG: Error getting USB devices: {e}")
            
        return devices
    
    @staticmethod
    def _is_usb_device(device_name):
        """通过sysfs判断是否为USB设备"""
        try:
            usb_path = f"/sys/block/{device_name}/device"
            if os.path.exists(usb_path):
                real_path = os.path.realpath(usb_path)
                return 'usb' in real_path
        except:
            return False
        return False
    
    @staticmethod
    def _get_device_details(device):
        """获取设备详细信息"""
        try:
            device_name = device.get('name', '')
            device_path = f"/dev/{device_name}"
            size = device.get('size', '未知')
            
            partitions = []
            if device.get('children'):
                for child in device.get('children', []):
                    partition_info = {
                        'name': child.get('name', ''),
                        'path': f"/dev/{child.get('name', '')}",
                        'fstype': child.get('fstype', '未知'),
                        'mountpoint': child.get('mountpoint', '未挂载'),
                        'size': child.get('size', '未知'),
                        'ro': child.get('ro', False)
                    }
                    partitions.append(partition_info)
            
            # ─── 多层只读检测 ───
            is_readonly = False
            ro_reason = ''
            
            # 1) lsblk RO 字段
            if device.get('ro', False):
                is_readonly = True
                ro_reason = 'lsblk RO=1'
            
            # 2) sysfs /sys/block/X/ro
            if not is_readonly and device_name:
                sys_ro_path = f"/sys/block/{device_name}/ro"
                if os.path.exists(sys_ro_path):
                    try:
                        with open(sys_ro_path, 'r') as f:
                            if f.read().strip() == '1':
                                is_readonly = True
                                ro_reason = 'sysfs ro=1'
                    except: pass
            
            # 3) blockdev --getro (内核层面的只读锁)
            if not is_readonly:
                try:
                    res = subprocess.run(['blockdev', '--getro', device_path],
                                       capture_output=True, text=True, timeout=3)
                    if res.returncode == 0 and res.stdout.strip() == '1':
                        is_readonly = True
                        ro_reason = 'blockdev --getro=1'
                except: pass
            
            # 4) 分区级挂载选项检查 (findmnt)
            if not is_readonly:
                for p in partitions:
                    mp = p.get('mountpoint')
                    if mp and mp not in ('未挂载', ''):
                        try:
                            res = subprocess.run(['findmnt', '-n', '-o', 'OPTIONS', '--target', mp],
                                               capture_output=True, text=True, timeout=3)
                            if res.returncode == 0:
                                opts = [o.strip() for o in res.stdout.strip().split(',')]
                                if 'ro' in opts:
                                    is_readonly = True
                                    ro_reason = f'分区 {p["name"]} 挂载为 ro'
                                    break
                        except: pass
                    # 子设备 lsblk RO 字段
                    if p.get('ro', False):
                        is_readonly = True
                        ro_reason = f'分区 {p["name"]} RO=1'
                        break
            
            # 5) hdparm 写保护位检测 (硬件级)
            if not is_readonly:
                try:
                    res = subprocess.run(['hdparm', '-r', device_path],
                                       capture_output=True, text=True, timeout=3)
                    if res.returncode == 0 and 'readonly' in res.stdout.lower():
                        # hdparm 输出: readonly = 1 (on)
                        if '= 1' in res.stdout or '=  1' in res.stdout:
                            is_readonly = True
                            ro_reason = 'hdparm readonly=1'
                except: pass
            
            status_text = f'只读 ({ro_reason})' if is_readonly else '正常'
            
            return {
                'name': device_name,
                'path': device_path,
                'size': size,
                'partitions': partitions,
                'readonly': is_readonly,
                'ro_reason': ro_reason,
                'status': status_text
            }
        except:
            return None
    
    @staticmethod
    def _check_readonly(device_path, device_name=''):
        """检查挂载选项是否只读 (兼容旧调用)"""
        try:
            # blockdev 检查
            res = subprocess.run(['blockdev', '--getro', device_path],
                               capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout.strip() == '1':
                return True
        except: pass
        
        try:
            mount_point = USBAnalyzer._get_mount_point(device_path)
            if mount_point != '未挂载':
                res = subprocess.run(['findmnt', '-n', '-o', 'OPTIONS', '--target', mount_point],
                                   capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    options = [o.strip() for o in res.stdout.strip().split(',')]
                    if 'ro' in options:
                        return True
        except: pass
        return False
    
    @staticmethod
    def _get_mount_point(device_path):
        """获取设备挂载点"""
        try:
            result = subprocess.run(['findmnt', '-n', '-o', 'TARGET', '-S', device_path],
                                   capture_output=True, text=True, timeout=3)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().splitlines()[0]
        except: pass
        try:
            result = subprocess.run(['mount'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if device_path in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith('/') and part != device_path:
                            return part
        except: pass
        return '未挂载'


class USBRepairman:
    """修复工具核心逻辑 (CLI模式)"""
    
    def __init__(self, device_path):
        self.device_path = device_path
        self.device_name = os.path.basename(device_path)
        
    def log(self, step, message):
        """输出标准格式日志供前端解析 [STEP:progress:message]"""
        print(f"[PROGRESS]:{step}:{message}", flush=True)

    def run_repair(self):
        """执行修复流程"""
        self.log(0, f"开始修复设备: {self.device_path}")
        
        # 1. 获取设备分区信息
        device_info = None
        devices = USBAnalyzer.get_usb_devices()
        for d in devices:
            if d['path'] == self.device_path:
                device_info = d
                break
        
        if not device_info:
            self.log(0, "错误: 无法找到设备信息")
            return False
            
        # 2. 卸载设备
        self.log(10, "正在卸载设备...")
        for partition in device_info['partitions']:
            if partition['mountpoint'] and partition['mountpoint'] != '未挂载':
                ret = subprocess.run(['umount', partition['path']], capture_output=True, text=True)
                if ret.returncode != 0:
                    self.log(10, f"卸载失败: {ret.stderr}")
                    return False
        
        # 3. 检查文件系统
        self.log(30, "正在检查文件系统...")
        for partition in device_info['partitions']:
             self._fsck(partition, check_only=True)
             
        # 4. 修复文件系统
        self.log(60, "正在修复文件系统...")
        for partition in device_info['partitions']:
             self._fsck(partition, check_only=False)
             
        # 5. 重新挂载
        self.log(80, "正在重新挂载设备...")
        # 等待系统自动挂载
        time.sleep(2)
        # 尝试触发udev事件
        subprocess.run(['udevadm', 'trigger', '--name-match', self.device_name], capture_output=True)
        time.sleep(2)
        
        # 6. 验证
        self.log(90, "验证修复结果...")
        # 刷新设备信息
        devices = USBAnalyzer.get_usb_devices()
        new_info = next((d for d in devices if d['path'] == self.device_path), None)
        
        if new_info and not new_info['readonly']:
            self.log(100, "修复成功！设备已恢复读写。")
            return True
        else:
            self.log(100, "完成，但设备状态可能仍为只读，请插拔重试。")
            return True # 视为完成

    def _fsck(self, partition, check_only=True):
        fstype = partition['fstype']
        path = partition['path']
        if not fstype or fstype == '未知': return
        
        cmd = self._get_fsck_command(fstype, path, check_only)
        if not cmd: return
        
        mode = "检查" if check_only else "修复"
        self.log(30 if check_only else 60, f"正在{mode}分区 {path} ({fstype})...")
        
        subprocess.run(cmd, capture_output=True)

    def _get_fsck_command(self, fstype, device_path, check_only=True):
        fstype = fstype.lower()
        if fstype.startswith('ext'):
            return ['fsck', '-n' if check_only else '-y', device_path]
        elif fstype == 'vfat':
            return ['fsck.vfat', '-n' if check_only else '-a', device_path]
        elif fstype == 'exfat':
            return ['fsck.exfat', '-n' if check_only else '-y', device_path]
        elif fstype == 'ntfs':
            return ['ntfsfix', '-n' if check_only else '-b', '-d', device_path]
        elif fstype == 'btrfs':
            return ['btrfs', 'check', '--readonly' if check_only else '--repair', device_path]
        elif fstype == 'xfs':
            cmd = ['xfs_repair', device_path]
            if check_only:
                cmd.insert(1, '-n')
            return cmd
        elif fstype == 'f2fs':
            return ['fsck.f2fs', '-n' if check_only else '-f', device_path]
        return None


class USBFormatter:
    """U盘格式化功能 (CLI模式，需 Root)"""
    
    SUPPORTED_FS = {
        'vfat':  {'label': 'FAT32',  'cmd': 'mkfs.vfat',   'label_flag': '-n', 'max_label': 11},
        'exfat': {'label': 'exFAT',  'cmd': 'mkfs.exfat',  'label_flag': '-L', 'max_label': 15},
        'ntfs':  {'label': 'NTFS',   'cmd': 'mkfs.ntfs',   'label_flag': '-L', 'max_label': 32},
        'ext4':  {'label': 'ext4',   'cmd': 'mkfs.ext4',   'label_flag': '-L', 'max_label': 16},
    }
    
    def __init__(self, device_path, fstype='vfat', label='', quick=True,
                 partition_only=False, partition_path=''):
        self.device_path = device_path
        self.device_name = os.path.basename(device_path)
        self.fstype = fstype
        self.label = label[:self.SUPPORTED_FS.get(fstype, {}).get('max_label', 11)] if label else ''
        self.quick = quick
        self.partition_only = partition_only
        self.partition_path = partition_path

    def log(self, step, message):
        print(f"[PROGRESS]:{step}:{message}", flush=True)

    def _umount_all(self):
        """强制卸载设备所有分区"""
        try:
            result = subprocess.run(['lsblk', self.device_path, '-n', '-o', 'NAME,MOUNTPOINT', '-r'],
                                   capture_output=True, text=True)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[1].startswith('/'):
                    subprocess.run(['umount', '-f', f"/dev/{parts[0]}"], capture_output=True)
            for i in range(1, 10):
                for suffix in [str(i), f"p{i}"]:
                    subprocess.run(['umount', '-f', f"{self.device_path}{suffix}"],
                                 capture_output=True, timeout=5)
            subprocess.run(['umount', '-f', self.device_path], capture_output=True, timeout=5)
            time.sleep(1)
        except Exception as e:
            self.log(10, f"卸载时遇到问题: {e}")

    def _mkfs(self, target_path):
        """对目标路径执行 mkfs"""
        # 在格式化前再次检查并强制卸载，防止分区被自动挂载
        subprocess.run(['umount', '-f', target_path], capture_output=True, timeout=10)
        time.sleep(0.5)
        
        fs_info = self.SUPPORTED_FS[self.fstype]
        cmd = [fs_info['cmd']]
        if self.fstype == 'ntfs' and self.quick:
            cmd.append('-f')
        if self.fstype == 'vfat':
            cmd.extend(['-F', '32'])
        if self.label:
            cmd.extend([fs_info['label_flag'], self.label])
        cmd.append(target_path)
        self.log(60, f"执行: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            self.log(80, f"格式化失败: {result.stderr.strip()}")
            return False
        return True

    def run_format(self):
        """执行格式化流程"""
        fs_info = self.SUPPORTED_FS.get(self.fstype)
        if not fs_info:
            self.log(0, f"错误: 不支持的文件系统 {self.fstype}")
            return False
        if self.partition_only:
            return self._run_partition_format()
        return self._run_whole_disk_format()

    def _run_partition_format(self):
        """单分区格式化：仅格式化指定分区，不动分区表"""
        fs_info = self.SUPPORTED_FS[self.fstype]
        target = self.partition_path
        if not target or not os.path.exists(target):
            self.log(0, f"错误: 分区 {target} 不存在")
            return False
        self.log(0, f"开始格式化分区 {target} → {fs_info['label']}")
        self.log(20, f"正在卸载 {target}...")
        subprocess.run(['umount', '-f', target], capture_output=True, timeout=10)
        time.sleep(0.5)
        self.log(50, f"正在格式化 {target} 为 {fs_info['label']}...")
        if not self._mkfs(target):
            return False
        self.log(90, "刷新设备状态...")
        subprocess.run(['udevadm', 'trigger', '--name-match', os.path.basename(target)], capture_output=True)
        time.sleep(2)
        self.log(100, f"分区格式化完成！{target} → {fs_info['label']}")
        return True

    def _run_whole_disk_format(self):
        """整盘格式化：清除分区表，创建单分区并格式化"""
        fs_info = self.SUPPORTED_FS[self.fstype]
        self.log(0, f"开始格式化 {self.device_path} → {fs_info['label']}")
        self.log(10, "正在卸载设备所有分区...")
        self._umount_all()
        self.log(30, "正在重建分区表...")
        try:
            subprocess.run(['parted', '-s', self.device_path, 'mklabel', 'msdos'],
                         capture_output=True, check=True)
            subprocess.run(['parted', '-s', self.device_path, 'mkpart', 'primary',
                          self.fstype if self.fstype != 'vfat' else 'fat32', '1MiB', '100%'],
                         capture_output=True, check=True)
            time.sleep(2)
            subprocess.run(['partprobe', self.device_path], capture_output=True)
            time.sleep(1)
        except subprocess.CalledProcessError as e:
            self.log(30, f"分区表重建失败: {e}")
            return False
        partition_path = f"{self.device_path}1"
        if not os.path.exists(partition_path):
            partition_path = f"{self.device_path}p1"
        if not os.path.exists(partition_path):
            self.log(50, f"找不到新分区: {partition_path}")
            return False
        self.log(50, f"正在格式化为 {fs_info['label']}...")
        if not self._mkfs(partition_path):
            return False
        self.log(90, "刷新设备状态...")
        subprocess.run(['udevadm', 'trigger', '--name-match', self.device_name], capture_output=True)
        time.sleep(2)
        self.log(100, f"格式化完成！{self.device_path} → {fs_info['label']}")
        return True


class SecureEraser:
    """U盘安全擦除功能 (CLI模式，需 Root)"""
    
    def __init__(self, device_path, passes=1):
        self.device_path = device_path
        self.device_name = os.path.basename(device_path)
        self.passes = passes  # 擦除次数 (1=快速零填充, 3=DoD标准)

    def log(self, step, message):
        print(f"[PROGRESS]:{step}:{message}", flush=True)

    def run_erase(self):
        """执行安全擦除"""
        self.log(0, f"开始安全擦除 {self.device_path} ({self.passes}遍)")
        
        # 1. 卸载
        self.log(5, "正在卸载设备...")
        try:
            result = subprocess.run(['lsblk', self.device_path, '-n', '-o', 'NAME,MOUNTPOINT', '-r'],
                                   capture_output=True, text=True)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[1].startswith('/'):
                    subprocess.run(['umount', f"/dev/{parts[0]}"], capture_output=True)
        except: pass
        
        # 2. 获取设备大小用于进度计算
        try:
            result = subprocess.run(['blockdev', '--getsize64', self.device_path],
                                   capture_output=True, text=True)
            total_bytes = int(result.stdout.strip())
        except:
            total_bytes = 0
        
        total_mb = total_bytes // (1024 * 1024) if total_bytes else 0
        
        # 3. 执行多遍擦除
        for pass_num in range(1, self.passes + 1):
            base_pct = int((pass_num - 1) / self.passes * 80) + 10
            end_pct = int(pass_num / self.passes * 80) + 10
            
            self.log(base_pct, f"第 {pass_num}/{self.passes} 遍: {'零填充' if pass_num % 2 == 1 else '随机数据'}...")
            
            # 奇数遍用零填充，偶数遍用随机数据
            source = '/dev/zero' if pass_num % 2 == 1 else '/dev/urandom'
            
            try:
                # 使用 dd 进行块级擦写，bs=4M 提升速度
                process = subprocess.Popen(
                    ['dd', f'if={source}', f'of={self.device_path}', 'bs=4M', 'conv=fsync', 'status=progress'],
                    stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True
                )
                
                # 从 stderr 读取 dd 的 status=progress 输出
                for line in process.stderr:
                    line = line.strip()
                    # dd 输出类似: "1073741824 bytes (1.1 GB, 1.0 GiB) copied"
                    if 'bytes' in line and total_mb > 0:
                        try:
                            written_bytes = int(line.split()[0])
                            written_mb = written_bytes // (1024 * 1024)
                            pct = base_pct + int((written_mb / total_mb) * (end_pct - base_pct))
                            pct = min(pct, end_pct)
                            self.log(pct, f"第 {pass_num} 遍: 已写入 {written_mb}MB / {total_mb}MB")
                        except: pass
                
                process.wait()
                # dd 写满设备后 returncode 通常非0 (No space left)，这是正常的
                
            except Exception as e:
                self.log(end_pct, f"第 {pass_num} 遍擦除异常: {e}")
        
        # 4. 同步磁盘缓存
        self.log(92, "同步数据到磁盘...")
        subprocess.run(['sync'], capture_output=True)
        
        # 5. 重建空白分区表
        self.log(95, "重建空白分区表...")
        try:
            subprocess.run(['parted', '-s', self.device_path, 'mklabel', 'msdos'],
                         capture_output=True)
        except: pass
        
        self.log(100, f"安全擦除完成！设备已清空。")
        return True


class VentoyInstaller:
    """Ventoy 启动盘制作 (使用官方 Ventoy 安装到U盘)"""
    
    VENTOY_VERSION = "1.1.12"
    VENTOY_URL = f"https://github.com/ventoy/Ventoy/releases/download/v{VENTOY_VERSION}/ventoy-{VENTOY_VERSION}-linux.tar.gz"
    CACHE_DIR = "/tmp/ventoy_cache"
    
    def __init__(self, device_path, use_gpt=False, secure_boot=False, reserve_mb=0, is_update=False, fs_type='ntfs'):
        self.device_path = device_path
        self.device_name = os.path.basename(device_path)
        self.use_gpt = use_gpt
        self.secure_boot = secure_boot
        self.reserve_mb = reserve_mb
        self.is_update = is_update
        self.fs_type = fs_type

    def log(self, step, message):
        print(f"[PROGRESS]:{step}:{message}", flush=True)

    def _find_ventoy_dir(self, base_dir):
        """在解压目录中查找 Ventoy2Disk.sh 所在的实际目录"""
        # 直接匹配期望路径
        expected = os.path.join(base_dir, f"ventoy-{self.VENTOY_VERSION}")
        if os.path.isfile(os.path.join(expected, "Ventoy2Disk.sh")):
            return expected
        # 遍历查找（兼容不同版本目录名称变化）
        try:
            for entry in os.listdir(base_dir):
                candidate = os.path.join(base_dir, entry)
                if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, "Ventoy2Disk.sh")):
                    return candidate
        except OSError:
            pass
        return None

    def run_install(self):
        """安装 Ventoy 到目标U盘 (优先使用离线包)"""
        self.log(0, "准备安装 Ventoy 启动盘环境...")
        
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        tar_name = f"ventoy-{self.VENTOY_VERSION}-linux.tar.gz"
        
        # 1. 检查缓存中是否已有可用的解压目录
        extract_dir = self._find_ventoy_dir(self.CACHE_DIR)
        if extract_dir:
            self.log(30, f"使用已缓存的 Ventoy 安装包: {extract_dir}")
        else:
            # 2. 查找本地离线包 (安装目录 → 脚本同目录 → 常见路径)
            tarball = None
            search_dirs = [
                '/usr/share/usb-fix-tool',                    # deb 安装路径
                '/opt/usb-fix-tool',                          # 备用安装路径
                os.path.dirname(os.path.abspath(__file__)),    # 脚本同目录
                os.path.expanduser('~'),                      # 用户主目录
                '/tmp',                                       # 临时目录
            ]
            # 如果是通过 pkexec 调用，也搜索原始脚本路径
            if len(sys.argv) > 0:
                script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                if script_dir not in search_dirs:
                    search_dirs.insert(0, script_dir)
            
            for d in search_dirs:
                candidate = os.path.join(d, tar_name)
                if os.path.isfile(candidate):
                    tarball = candidate
                    self.log(10, f"找到离线包: {candidate}")
                    break
            
            # 3. 没有本地包则联网下载
            if not tarball:
                self.log(5, f"未找到离线包，正在下载 Ventoy v{self.VENTOY_VERSION}...")
                tarball = os.path.join(self.CACHE_DIR, tar_name)
                try:
                    import urllib.request
                    urllib.request.urlretrieve(self.VENTOY_URL, tarball)
                    self.log(25, "下载完成")
                except Exception as e:
                    self.log(10, f"下载失败: {e}")
                    return False
            
            # 4. 解压
            self.log(30, "正在解压 Ventoy...")
            try:
                result = subprocess.run(
                    ['tar', '-xzf', tarball, '-C', self.CACHE_DIR],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    self.log(30, f"解压失败: {result.stderr}")
                    return False
            except Exception as e:
                self.log(30, f"解压异常: {e}")
                return False
            
            # 重新查找解压后的目录
            extract_dir = self._find_ventoy_dir(self.CACHE_DIR)
            if not extract_dir:
                self.log(35, f"解压完成但找不到 Ventoy 安装目录，缓存内容: {os.listdir(self.CACHE_DIR)}")
                return False
        
        # 5. 卸载U盘所有分区 (强制)
        self.log(40, "正在卸载设备分区...")
        try:
            result = subprocess.run(['lsblk', self.device_path, '-n', '-o', 'NAME,MOUNTPOINT', '-r'],
                                   capture_output=True, text=True)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[1].startswith('/'):
                    subprocess.run(['umount', '-f', f"/dev/{parts[0]}"], capture_output=True)
            
            # 暴力卸载所有可能的分区
            for i in range(1, 10):
                for suffix in [str(i), f"p{i}"]:
                    subprocess.run(['umount', '-f', f"{self.device_path}{suffix}"], capture_output=True, timeout=5)
            subprocess.run(['umount', '-f', self.device_path], capture_output=True, timeout=5)
            time.sleep(1)
        except Exception as e:
            self.log(40, f"卸载检查异常: {e}")
        
        # 6. 确认 Ventoy2Disk.sh 存在并赋予执行权限
        ventoy_sh = os.path.join(extract_dir, "Ventoy2Disk.sh")
        if not os.path.exists(ventoy_sh):
            self.log(50, f"找不到 Ventoy2Disk.sh: {ventoy_sh}")
            # 列出目录内容帮助排查
            try:
                contents = os.listdir(extract_dir)
                self.log(50, f"目录内容: {contents}")
            except: pass
            return False
        
        # 确保脚本有执行权限
        try:
            os.chmod(ventoy_sh, 0o755)
            # 同时给目录下所有 .sh 文件加执行权限
            for f in os.listdir(extract_dir):
                if f.endswith('.sh'):
                    os.chmod(os.path.join(extract_dir, f), 0o755)
            # tool 子目录
            tool_dir = os.path.join(extract_dir, 'tool')
            if os.path.isdir(tool_dir):
                for root, dirs, files in os.walk(tool_dir):
                    for f in files:
                        fpath = os.path.join(root, f)
                        try:
                            os.chmod(fpath, 0o755)
                        except: pass
        except Exception as e:
            self.log(50, f"设置执行权限时出错: {e}")
        
        # 7. 执行 Ventoy 安装或升级
        action_name = "升级" if self.is_update else "安装"
        self.log(50, f"正在{action_name} Ventoy 到 {self.device_path}...")
        try:
            # 构建命令
            # Ventoy 没有 -n 非交互参数，通过 stdin 管道写 'y' 跳过确认
            if self.is_update:
                cmd = ['bash', ventoy_sh, '-u']  # -u = 安全升级（不破坏数据）
            else:
                cmd = ['bash', ventoy_sh, '-I']  # -I = 全新强制安装
                if self.use_gpt:
                    cmd.append('-g')       # GPT 分区表
                if self.secure_boot:
                    cmd.append('-s')       # Secure Boot 支持
                if self.reserve_mb > 0:
                    cmd.extend(['-r', str(self.reserve_mb)])  # 保留空间 (MB)
                
            cmd.append(self.device_path)
            
            self.log(55, f"执行命令: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True, bufsize=1, cwd=extract_dir
            )
            
            # 通过 stdin 发送 'y' 跳过所有交互确认
            try:
                process.stdin.write('y\n')
                process.stdin.write('y\n')
                process.stdin.flush()
            except: pass
            
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.log(60, line)
            
            process.wait(timeout=300)  # 最长等待5分钟
            
            if process.returncode != 0:
                self.log(80, f"Ventoy {action_name}失败 (退出码: {process.returncode})，请检查设备状态。")
                return False
        except subprocess.TimeoutExpired:
            self.log(80, f"Ventoy {action_name}超时 (>5分钟)")
            try:
                process.kill()
            except: pass
            return False
        except Exception as e:
            self.log(80, f"执行异常: {e}")
            return False
        
        # 8. 等待系统重新识别分区
        self.log(85, "等待系统识别新分区...")
        time.sleep(3)
        subprocess.run(['udevadm', 'trigger', '--name-match', self.device_name], capture_output=True)
        subprocess.run(['udevadm', 'settle', '--timeout=5'], capture_output=True)
        time.sleep(2)
        
        # 9. 安装后格式化数据分区为用户指定的文件系统
        # Ventoy2Disk.sh 默认 exFAT，如果用户选了其他格式需手动 mkfs
        if not self.is_update and self.fs_type and self.fs_type != 'exfat':
            data_part = f"{self.device_path}1"  # Ventoy 数据分区始终是第一分区
            if os.path.exists(data_part):
                # 确保分区未挂载
                subprocess.run(['umount', data_part], capture_output=True)
                
                mkfs_map = {
                    'ntfs': ['mkfs.ntfs', '-f', '-L', 'Ventoy', data_part],
                    'fat32': ['mkfs.vfat', '-F', '32', '-n', 'Ventoy', data_part],
                    'ext4': ['mkfs.ext4', '-F', '-L', 'Ventoy', data_part],
                }
                mkfs_cmd = mkfs_map.get(self.fs_type)
                if mkfs_cmd:
                    self.log(92, f"正在将数据分区格式化为 {self.fs_type.upper()}...")
                    try:
                        ret = subprocess.run(mkfs_cmd, capture_output=True, text=True, timeout=120)
                        if ret.returncode == 0:
                            self.log(95, f"数据分区已格式化为 {self.fs_type.upper()}")
                        else:
                            self.log(95, f"格式化 {self.fs_type.upper()} 失败: {ret.stderr.strip()}，但 Ventoy 引导已安装成功")
                    except Exception as e:
                        self.log(95, f"格式化异常: {e}，但 Ventoy 引导已安装成功")
            else:
                self.log(92, f"未找到数据分区 {data_part}，跳过文件系统格式化")
        
        self.log(100, f"Ventoy {action_name}成功！" + ("请将 ISO 镜像文件复制到U盘即可启动。" if not self.is_update else ""))
        return True


# ============================================
# 前端GUI (依赖PyQt5)
# ============================================

# 延迟导入PyQt5，只有在GUI模式下才需要
def run_gui():
    try:
        from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                                    QWidget, QTableWidget, QTableWidgetItem, QPushButton, 
                                    QLabel, QTextEdit, QHeaderView, QCheckBox, QMessageBox,
                                    QProgressBar, QGroupBox, QSplitter, QLineEdit, QDialog, QFrame)
        from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
        from PyQt5.QtGui import QFont, QIcon, QImage, QPixmap, QIntValidator
    except ImportError:
        print("请安装PyQt5", file=sys.stderr)
        return

    class RepairWorker(QThread):
        progress_updated = pyqtSignal(int, str)
        repair_finished = pyqtSignal(bool, str)
        log_message = pyqtSignal(str)
        
        def __init__(self, device_path, script_path):
            super().__init__()
            self.device_path = device_path
            self.script_path = script_path
        
        def run(self):
            try:
                self.log_message.emit(f"正在申请权限以修复设备: {self.device_path}...")
                
                # 使用pkexec提权调用自身
                cmd = ['pkexec', sys.executable, self.script_path, '--repair', self.device_path]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                
                success = False
                for line in process.stdout:
                    line = line.strip()
                    if line.startswith("[PROGRESS]:"):
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            try:
                                progress = int(parts[1])
                                msg = parts[2]
                                self.progress_updated.emit(progress, msg)
                                self.log_message.emit(msg)
                                if progress == 100: success = True
                            except: pass
                    else:
                        # 普通输出也记录
                        if line: self.log_message.emit(line)
                
                process.wait()
                if process.returncode == 0:
                    self.repair_finished.emit(True, "修复流程完成")
                else:
                    self.repair_finished.emit(False, "修复被取消或失败")
                    
            except Exception as e:
                self.repair_finished.emit(False, str(e))

    class FormatWorker(QThread):
        """格式化工作线程 (通过 pkexec 提权)"""
        progress_updated = pyqtSignal(int, str)
        finished = pyqtSignal(bool, str)
        log_message = pyqtSignal(str)
        
        def __init__(self, device_path, fstype, label, quick, script_path,
                     partition_only=False, partition_path=''):
            super().__init__()
            self.device_path = device_path
            self.fstype = fstype
            self.label = label
            self.quick = quick
            self.script_path = script_path
            self.partition_only = partition_only
            self.partition_path = partition_path
        
        def run(self):
            try:
                cmd = ['pkexec', sys.executable, self.script_path, 
                       '--format', self.device_path, '--fstype', self.fstype]
                if self.label:
                    cmd.extend(['--label', self.label])
                if self.quick:
                    cmd.append('--quick')
                if self.partition_only and self.partition_path:
                    cmd.extend(['--format-partition', self.partition_path])
                
                self.log_message.emit(f"执行: {' '.join(cmd)}")
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                
                for line in process.stdout:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("[PROGRESS]:"):
                        # 格式: [PROGRESS]:数字:消息
                        try:
                            _, prog_str, msg = line.split(':', 2)
                            progress = int(prog_str)
                            self.progress_updated.emit(progress, msg)
                            self.log_message.emit(msg)
                        except (ValueError, TypeError):
                            self.log_message.emit(line)
                    else:
                        self.log_message.emit(line)
                
                process.wait()
                success = (process.returncode == 0)
                self.finished.emit(success, "格式化完成" if success else f"格式化失败 (退出码: {process.returncode})")
            except Exception as e:
                self.finished.emit(False, f"格式化异常: {str(e)}")

    class EraseWorker(QThread):
        """安全擦除工作线程 (通过 pkexec 提权)"""
        progress_updated = pyqtSignal(int, str)
        finished = pyqtSignal(bool, str)
        log_message = pyqtSignal(str)
        
        def __init__(self, device_path, passes, script_path):
            super().__init__()
            self.device_path = device_path
            self.passes = passes
            self.script_path = script_path
        
        def run(self):
            try:
                cmd = ['pkexec', sys.executable, self.script_path,
                       '--erase', self.device_path, '--passes', str(self.passes)]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                for line in process.stdout:
                    line = line.strip()
                    if not line: continue
                    if line.startswith("[PROGRESS]:"):
                        try:
                            _, prog_str, msg = line.split(':', 2)
                            self.progress_updated.emit(int(prog_str), msg)
                            self.log_message.emit(msg)
                        except (ValueError, TypeError):
                            self.log_message.emit(line)
                    else:
                        self.log_message.emit(line)
                process.wait()
                success = (process.returncode == 0)
                self.finished.emit(success, "安全擦除完成" if success else f"擦除失败 (退出码: {process.returncode})")
            except Exception as e:
                self.finished.emit(False, f"擦除异常: {str(e)}")

    class VentoyWorker(QThread):
        """Ventoy 安装工作线程 (通过 pkexec 提权)"""
        progress_updated = pyqtSignal(int, str)
        finished = pyqtSignal(bool, str)
        log_message = pyqtSignal(str)
        
        def __init__(self, device_path, script_path, use_gpt=False, secure_boot=False, reserve_mb=0, is_update=False, fs_type='ntfs'):
            super().__init__()
            self.device_path = device_path
            self.script_path = script_path
            self.use_gpt = use_gpt
            self.secure_boot = secure_boot
            self.reserve_mb = reserve_mb
            self.is_update = is_update
            self.fs_type = fs_type
        
        def run(self):
            try:
                cmd = ['pkexec', sys.executable, self.script_path,
                       '--ventoy', self.device_path]
                if self.is_update:
                    cmd.append('--ventoy-update')
                else:
                    if self.use_gpt:
                        cmd.append('--ventoy-gpt')
                    if self.secure_boot:
                        cmd.append('--ventoy-secureboot')
                    if self.reserve_mb > 0:
                        cmd.extend(['--ventoy-reserve', str(self.reserve_mb)])
                    if self.fs_type:
                        cmd.extend(['--ventoy-fstype', self.fs_type])
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                success = False
                for line in process.stdout:
                    line = line.strip()
                    if line.startswith("[PROGRESS]:"):
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            try:
                                progress = int(parts[1])
                                msg = parts[2]
                                self.progress_updated.emit(progress, msg)
                                self.log_message.emit(msg)
                                if progress == 100: success = True
                            except: pass
                    elif line:
                        self.log_message.emit(line)
                process.wait()
                action_name = "更新" if self.is_update else "安装"
                self.finished.emit(success, f"Ventoy {action_name}完成" if success else f"Ventoy {action_name}失败或被取消")
            except Exception as e:
                self.finished.emit(False, str(e))

    class USBFixTool(QMainWindow):
        def __init__(self):
            super().__init__()
            self.devices = []
            self.selected_device = None
            self.repair_worker = None
            self.format_worker = None
            self.erase_worker = None
            self.ventoy_worker = None
            self.init_ui()
            self.refresh_devices()
            
            self.timer = QTimer()
            self.timer.timeout.connect(self.refresh_devices)
            self.timer.start(5000)
        
        def init_ui(self):
            self.setWindowTitle("U盘工具箱 v1.3")
            self.setGeometry(100, 60, 900, 700)
            self.setMinimumSize(800, 600)
            
            try: self.setWindowIcon(QIcon.fromTheme('drive-removable-media'))
            except: pass
            
            central_widget = QWidget()
            central_widget.setObjectName("centralWidget")
            self.setCentralWidget(central_widget)
            
            root = QVBoxLayout(central_widget)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)
            
            # ── 顶栏 ──
            topbar = QWidget()
            topbar.setObjectName("topbar")
            topbar.setFixedHeight(48)
            tb = QHBoxLayout(topbar)
            tb.setContentsMargins(20, 0, 20, 0)
            
            title_label = QLabel("U盘工具箱")
            title_label.setObjectName("appTitle")
            tb.addWidget(title_label)
            
            tb.addStretch()
            
            # --- 主题切换器 ---
            theme_label = QLabel("主题:")
            theme_label.setStyleSheet("color: #656d76; font-size: 12px; margin-right: 4px;")
            tb.addWidget(theme_label)
            
            from PyQt5.QtWidgets import QComboBox
            self.theme_combo = QComboBox()
            self.theme_combo.addItems(["Modern Light", "Dark Hacker", "Fluent Glass"])
            self.theme_combo.currentTextChanged.connect(self.change_theme)
            self.theme_combo.setStyleSheet("""
                QComboBox { border: 1px solid #d1d9e0; border-radius: 4px; padding: 4px 8px; font-size: 12px; background: transparent; }
                QComboBox::drop-down { border: none; }
            """)
            tb.addWidget(self.theme_combo)
            
            # 加一点边距
            spacer = QWidget()
            spacer.setFixedWidth(16)
            tb.addWidget(spacer)
            
            self.status_indicator = QLabel("就绪")
            self.status_indicator.setObjectName("statusChip")
            tb.addWidget(self.status_indicator)
            
            root.addWidget(topbar)
            
            # ── 主体区域 ──
            body = QWidget()
            body.setObjectName("bodyWidget")
            body_layout = QVBoxLayout(body)
            body_layout.setContentsMargins(20, 12, 20, 12)
            body_layout.setSpacing(12)
            root.addWidget(body, 1)
            
            # ── 设备表格 ──
            section_title = QLabel("检测到的 USB 设备")
            section_title.setObjectName("sectionTitle")
            body_layout.addWidget(section_title)
            
            self.devices_table = QTableWidget()
            self.devices_table.setObjectName("devicesTable")
            self.devices_table.setColumnCount(5)
            self.devices_table.setHorizontalHeaderLabels(["", "设备", "容量", "状态", "文件系统"])
            self.devices_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.devices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            self.devices_table.setColumnWidth(0, 40)
            self.devices_table.setSelectionBehavior(QTableWidget.SelectRows)
            self.devices_table.setAlternatingRowColors(True)
            self.devices_table.verticalHeader().setVisible(False)
            self.devices_table.setShowGrid(False)
            self.devices_table.cellClicked.connect(self.on_device_selected)
            body_layout.addWidget(self.devices_table)
            
            # ── 操作按钮栏 ──
            btn_bar = QWidget()
            btn_bar.setObjectName("btnBar")
            bl = QHBoxLayout(btn_bar)
            bl.setContentsMargins(0, 0, 0, 0)
            bl.setSpacing(8)
            
            self.refresh_btn = QPushButton("刷新")
            self.refresh_btn.setObjectName("flatBtn")
            self.refresh_btn.setCursor(Qt.PointingHandCursor)
            self.refresh_btn.clicked.connect(self.refresh_devices)
            bl.addWidget(self.refresh_btn)
            
            self.repair_btn = QPushButton("修复只读")
            self.repair_btn.setObjectName("accentBtn")
            self.repair_btn.setCursor(Qt.PointingHandCursor)
            self.repair_btn.clicked.connect(self.repair_device)
            self.repair_btn.setEnabled(False)
            bl.addWidget(self.repair_btn)
            
            self.format_btn = QPushButton("格式化")
            self.format_btn.setObjectName("accentBtn")
            self.format_btn.setCursor(Qt.PointingHandCursor)
            self.format_btn.clicked.connect(self.format_device)
            self.format_btn.setEnabled(False)
            bl.addWidget(self.format_btn)
            
            self.erase_btn = QPushButton("安全擦除")
            self.erase_btn.setObjectName("dangerBtn")
            self.erase_btn.setCursor(Qt.PointingHandCursor)
            self.erase_btn.clicked.connect(self.erase_device)
            self.erase_btn.setEnabled(False)
            bl.addWidget(self.erase_btn)
            
            self.ventoy_btn = QPushButton("制作启动盘")
            self.ventoy_btn.setObjectName("accentBtn")
            self.ventoy_btn.setCursor(Qt.PointingHandCursor)
            self.ventoy_btn.clicked.connect(self.install_ventoy)
            self.ventoy_btn.setEnabled(False)
            bl.addWidget(self.ventoy_btn)
            
            bl.addStretch()
            
            help_btn = QPushButton("帮助")
            help_btn.setObjectName("ghostBtn")
            help_btn.setCursor(Qt.PointingHandCursor)
            help_btn.clicked.connect(self.show_help)
            bl.addWidget(help_btn)
            
            about_btn = QPushButton("关于")
            about_btn.setObjectName("ghostBtn")
            about_btn.setCursor(Qt.PointingHandCursor)
            about_btn.clicked.connect(self.show_about)
            bl.addWidget(about_btn)
            
            body_layout.addWidget(btn_bar)
            
            # ── 分隔线 ──
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setObjectName("separator")
            body_layout.addWidget(sep)
            
            # ── 下半区：信息 + 进度 + 日志 ──
            self.splitter = QSplitter(Qt.Vertical)
            self.splitter.setObjectName("mainSplitter")
            self.splitter.setHandleWidth(1)
            body_layout.addWidget(self.splitter, 1)
            
            # 设备详情
            info_widget = QWidget()
            info_layout = QVBoxLayout(info_widget)
            info_layout.setContentsMargins(0, 8, 0, 0)
            info_layout.setSpacing(6)
            
            info_title = QLabel("设备详情")
            info_title.setObjectName("sectionTitle")
            info_layout.addWidget(info_title)
            
            self.details_text = QTextEdit()
            self.details_text.setObjectName("infoBox")
            self.details_text.setMaximumHeight(80)
            self.details_text.setReadOnly(True)
            self.details_text.setPlaceholderText("勾选一个设备以查看详情…")
            info_layout.addWidget(self.details_text)
            
            
            self.progress_bar = QProgressBar()
            self.progress_bar.setObjectName("progressBar")
            self.progress_bar.setVisible(False)
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setFixedHeight(6)
            info_layout.addWidget(self.progress_bar)
            
            self.status_label = QLabel("等待操作…")
            self.status_label.setObjectName("statusLabel")
            info_layout.addWidget(self.status_label)
            
            self.splitter.addWidget(info_widget)
            
            # 日志
            log_widget = QWidget()
            log_layout = QVBoxLayout(log_widget)
            log_layout.setContentsMargins(0, 8, 0, 0)
            log_layout.setSpacing(6)
            
            log_title = QLabel("操作日志")
            log_title.setObjectName("sectionTitle")
            log_layout.addWidget(log_title)
            
            self.log_text = QTextEdit()
            self.log_text.setObjectName("logBox")
            self.log_text.setReadOnly(True)
            log_layout.addWidget(self.log_text)
            
            self.splitter.addWidget(log_widget)
            self.splitter.setSizes([160, 240])
            
            self.log_message("[启动] 工具箱就绪 · 普通用户模式")
            
            # 初始化默认主题
            self.change_theme("Modern Light")
        
        def change_theme(self, theme_name):
            if theme_name == "Modern Light":
                self.setStyleSheet(self._get_light_stylesheet())
            elif theme_name == "Dark Hacker":
                self.setStyleSheet(self._get_dark_stylesheet())
            elif theme_name == "Fluent Glass":
                self.setStyleSheet(self._get_glass_stylesheet())
            # 刷新设备详情颜色以适配新主题
            if self.selected_device:
                self.update_device_details()
        
        def resizeEvent(self, event):
            """响应式布局：根据窗口大小动态调整分割比例"""
            super().resizeEvent(event)
            h = self.height()
            if h < 600:
                # 小窗口：压缩详情区，留更多空间给表格
                self.details_text.setMaximumHeight(60)
                self.splitter.setSizes([120, 200])
            elif h < 800:
                self.details_text.setMaximumHeight(80)
                self.splitter.setSizes([160, 240])
            else:
                # 大窗口：扩展所有区域
                self.details_text.setMaximumHeight(120)
                self.splitter.setSizes([220, 350])
        
        def _get_light_stylesheet(self):
            return """
            /* ── 全局 ── */
            * { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; outline: none; font-size: 13px; }
            QMainWindow { background-color: #f8fafc; }
            #centralWidget { background-color: #f8fafc; }

            /* ── 顶栏 ── */
            #topbar { background-color: #ffffff; border-bottom: 1px solid #e2e8f0; }
            #appTitle { color: #0f172a; font-size: 18px; font-weight: 800; letter-spacing: 0px; }
            #statusChip { color: #059669; font-size: 11px; font-weight: 600; padding: 4px 12px; background-color: #d1fae5; border-radius: 12px; }

            /* ── 主体 ── */
            #bodyWidget { background-color: #f8fafc; }
            #sectionTitle { color: #64748b; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; padding-bottom: 6px; }
            #separator { border: none; background-color: #cbd5e1; max-height: 1px; }

            /* ── 设备表格 ── */
            #devicesTable { 
                background-color: #ffffff; 
                alternate-background-color: #f8fafc; 
                border: 1px solid #e2e8f0; 
                border-radius: 8px;
                color: #334155; 
                font-size: 13px; 
                selection-background-color: #eff6ff; 
                selection-color: #2563eb; 
            }
            #devicesTable::item { padding: 12px 14px; border-bottom: 1px solid #f1f5f9; }
            QHeaderView::section { 
                background-color: #ffffff; 
                color: #94a3b8; 
                padding: 10px 14px; 
                border: none; 
                border-bottom: 2px solid #f1f5f9; 
                font-weight: 700; 
                font-size: 11px; 
                text-transform: uppercase; 
            }

            /* ── 扁平按钮 ── */
            QPushButton { border-radius: 6px; outline: none; }
            
            #flatBtn { background-color: #ffffff; color: #475569; border: 1px solid #cbd5e1; padding: 8px 18px; font-size: 13px; font-weight: 600; }
            #flatBtn:hover { background-color: #f1f5f9; border-color: #94a3b8; color: #0f172a; }
            #flatBtn:pressed { background-color: #e2e8f0; }

            #accentBtn { background-color: #3b82f6; color: #ffffff; border: none; padding: 8px 18px; font-size: 13px; font-weight: 600; box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.5); }
            #accentBtn:hover { background-color: #2563eb; }
            #accentBtn:pressed { background-color: #1d4ed8; }
            #accentBtn:disabled { background-color: #e2e8f0; color: #94a3b8; }

            #dangerBtn { background-color: #ef4444; color: #ffffff; border: none; padding: 8px 18px; font-size: 13px; font-weight: 600; }
            #dangerBtn:hover { background-color: #dc2626; }
            #dangerBtn:pressed { background-color: #b91c1c; }
            #dangerBtn:disabled { background-color: #e2e8f0; color: #94a3b8; }

            #ghostBtn { background-color: transparent; color: #64748b; border: 1px solid #e2e8f0; padding: 8px 14px; font-size: 13px; font-weight: 500; }
            #ghostBtn:hover { color: #0f172a; background-color: #f1f5f9; border-color: #cbd5e1; }

            /* ── 信息框 & 日志 ── */
            #infoBox { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; color: #334155; font-size: 13px; leading: 1.6; }
            #logBox  { background-color: #1e293b; border: 1px solid #0f172a; border-radius: 8px; padding: 12px; color: #34d399; font-family: "Consolas", "Courier New", monospace; font-size: 12px; }
            #statusLabel { color: #64748b; font-size: 12px; font-weight: 500; padding: 4px 0; }

            /* ── 进度条 ── */
            #progressBar { background-color: #e2e8f0; border: none; border-radius: 3px; max-height: 6px; }
            #progressBar::chunk { background-color: #3b82f6; border-radius: 3px; }

            /* ── 消息框 ── */
            QMessageBox { background-color: #ffffff; }
            QMessageBox QLabel { color: #0f172a; font-size: 13px; }
            QMessageBox QPushButton { background-color: #3b82f6; color: white; border: none; border-radius: 6px; padding: 8px 24px; min-width: 80px; font-weight: 600; }
            QMessageBox QPushButton:hover { background-color: #2563eb; }

            /* ── 分割器 ── */
            QSplitter::handle { background-color: #e2e8f0; height: 1px; width: 1px; }
            """
            
        def _get_dark_stylesheet(self):
            return """
            * { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; font-size: 13px; }
            QMainWindow, #centralWidget, #bodyWidget { background-color: #0d1117; color: #c9d1d9; }
            QDialog { background-color: #0d1117; color: #c9d1d9; }
            QDialog QLabel { color: #c9d1d9; }
            QDialog QComboBox, QDialog QSpinBox, QDialog QLineEdit { background: #161b22; color: #c9d1d9; border: 1px solid #30363d; border-radius: 4px; padding: 6px; }
            #topbar { background-color: #161b22; border-bottom: 1px solid #30363d; }
            #appTitle { color: #58a6ff; font-size: 18px; font-weight: 600; letter-spacing: 1px; }
            #statusChip { color: #3fb950; font-size: 11px; font-weight: 500; padding: 3px 10px; background-color: rgba(46,160,67,0.15); border: 1px solid rgba(46,160,67,0.4); border-radius: 4px; }
            #sectionTitle { color: #8b949e; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; padding-bottom: 4px; }
            #separator, QFrame[frameShape="4"] { border: none; background-color: #30363d; max-height: 1px; }
            #devicesTable { background-color: #0d1117; alternate-background-color: #161b22; border: 1px solid #30363d; color: #c9d1d9; font-size: 13px; selection-background-color: #1f385c; selection-color: #ffffff; }
            #devicesTable::item { padding: 8px 12px; border-bottom: 1px solid #21262d; }
            QHeaderView::section { background-color: #161b22; color: #8b949e; padding: 8px 12px; border: none; border-bottom: 1px solid #30363d; font-weight: 600; font-size: 11px; text-transform: uppercase; }
            #flatBtn, #ghostBtn { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 7px 16px; font-size: 13px; border-radius: 4px; }
            #flatBtn:hover, #ghostBtn:hover { background-color: #30363d; border-color: #8b949e; }
            #flatBtn:pressed, #ghostBtn:pressed { background-color: #161b22; }
            #accentBtn, QDialog QPushButton[text="开始格式化"], QDialog QPushButton[text="开始安装 Ventoy"], QDialog QPushButton[text="开始升级 Ventoy"] { background-color: #238636; color: #ffffff; border: 1px solid rgba(240,246,252,0.1); padding: 7px 16px; font-size: 13px; font-weight: 600; border-radius: 4px; }
            #accentBtn:hover, QDialog QPushButton:hover { background-color: #2ea043; }
            #accentBtn:disabled { background-color: #21262d; color: #484f58; border-color: #30363d; }
            QDialog QPushButton[text="取消"] { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 7px 16px; border-radius: 4px; }
            #dangerBtn { background-color: #da3633; color: #ffffff; border: 1px solid rgba(240,246,252,0.1); padding: 7px 16px; font-size: 13px; font-weight: 600; border-radius: 4px; }
            #dangerBtn:hover { background-color: #f85149; }
            #dangerBtn:disabled { background-color: #21262d; color: #484f58; border-color: #30363d; }
            #infoBox { background-color: #0d1117; border: 1px solid #30363d; padding: 10px; color: #c9d1d9; font-size: 13px; border-radius: 4px; }
            #logBox { background-color: #0d1117; border: 1px solid #30363d; padding: 10px; color: #7ee787; font-family: "Consolas", monospace; font-size: 12px; border-radius: 4px; }
            #statusLabel { color: #8b949e; font-size: 12px; }
            #progressBar { background-color: #21262d; border: none; border-radius: 3px; }
            #progressBar::chunk { background-color: #238636; border-radius: 3px; }
            QCheckBox, QRadioButton { color: #c9d1d9; spacing: 6px; }
            QCheckBox::indicator, QRadioButton::indicator { width: 14px; height: 14px; background-color: #0d1117; border: 1px solid #30363d; border-radius: 3px; }
            QRadioButton::indicator { border-radius: 7px; }
            QCheckBox::indicator:checked, QRadioButton::indicator:checked { background-color: #238636; border-color: #238636; }
            QMessageBox { background-color: #0d1117; color: #c9d1d9; }
            QSplitter::handle { background-color: #30363d; height: 1px; }
            """

        def _get_glass_stylesheet(self):
            return """
            * { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; font-size: 13px; }
            QMainWindow, #centralWidget, #bodyWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f0f4fd, stop:1 #e0e7ff); }
            QDialog { background: #f0f4fd; }
            #topbar { background-color: rgba(255, 255, 255, 0.7); border-bottom: 1px solid rgba(255, 255, 255, 0.5); }
            #appTitle { color: #1e3a8a; font-size: 16px; font-weight: 700; }
            #statusChip { color: #047857; font-size: 11px; font-weight: 600; padding: 3px 12px; background-color: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; }
            #sectionTitle { color: #4338ca; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; }
            #separator { border: none; background-color: rgba(0,0,0,0.05); max-height: 1px; }
            #devicesTable { background-color: rgba(255, 255, 255, 0.6); alternate-background-color: rgba(255, 255, 255, 0.4); border: 1px solid rgba(255,255,255,0.8); border-radius: 8px; color: #1f2937; gridline-color: transparent; selection-background-color: rgba(79, 70, 229, 0.2); selection-color: #312e81; }
            #devicesTable::item { padding: 10px 12px; border-bottom: 1px solid rgba(0,0,0,0.03); }
            QHeaderView::section { background-color: transparent; color: #4b5563; padding: 10px 12px; border: none; border-bottom: 1px solid rgba(0,0,0,0.05); font-weight: 700; font-size: 11px; text-transform: uppercase; }
            #flatBtn, #ghostBtn { background-color: rgba(255,255,255,0.7); color: #374151; border: 1px solid rgba(255,255,255,0.9); padding: 8px 18px; font-size: 13px; font-weight: 500; border-radius: 6px; }
            #flatBtn:hover, #ghostBtn:hover { background-color: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            #accentBtn { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #3b82f6); color: #ffffff; border: none; padding: 8px 18px; font-size: 13px; font-weight: 700; border-radius: 6px; }
            #accentBtn:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338ca, stop:1 #2563eb); }
            #accentBtn:disabled { background: rgba(0,0,0,0.1); color: #9ca3af; }
            #dangerBtn { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #ec4899); color: #ffffff; border: none; padding: 8px 18px; font-size: 13px; font-weight: 700; border-radius: 6px; }
            #dangerBtn:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dc2626, stop:1 #db2777); }
            #dangerBtn:disabled { background: rgba(0,0,0,0.1); color: #9ca3af; }
            #infoBox { background-color: rgba(255, 255, 255, 0.6); border: 1px solid rgba(255,255,255,0.8); padding: 12px; color: #1f2937; font-size: 13px; border-radius: 8px; }
            #logBox { background-color: #1e293b; border: 1px solid rgba(0,0,0,0.1); padding: 12px; color: #34d399; font-family: "Consolas", monospace; font-size: 12px; border-radius: 8px; }
            #statusLabel { color: #6b7280; font-size: 12px; font-weight: 500; }
            #progressBar { background-color: rgba(0,0,0,0.05); border: none; border-radius: 3px; }
            #progressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #3b82f6); border-radius: 3px; }
            QCheckBox, QRadioButton { color: #1f2937; spacing: 8px; }
            QCheckBox::indicator, QRadioButton::indicator { width: 16px; height: 16px; background-color: rgba(255,255,255,0.8); border: 1px solid rgba(0,0,0,0.2); border-radius: 4px; }
            QRadioButton::indicator { border-radius: 9px; }
            QCheckBox::indicator:checked, QRadioButton::indicator:checked { background-color: #4f46e5; border-color: #4f46e5; }
            QSplitter::handle { background-color: rgba(0,0,0,0.05); height: 1px; }
            QDialog QComboBox, QDialog QSpinBox, QDialog QLineEdit { background: rgba(255,255,255,0.7); border: 1px solid rgba(0,0,0,0.1); padding: 6px; border-radius: 4px; }
            QDialog QPushButton[text="开始格式化"], QDialog QPushButton[text="开始安装 Ventoy"], QDialog QPushButton[text="开始升级 Ventoy"] { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #3b82f6); color: white; border-radius: 6px; padding: 10px; font-weight: bold; border: none; }
            """


        
        def show_help(self):
            help_text = """U盘多功能工具箱 - 使用说明

【功能介绍】
  · 🔧 修复只读: 自动检测并修复文件系统错误
  · 💾 格式化: 支持 FAT32, exFAT, NTFS, ext4
  · 🗑️ 安全擦除: 零填充/随机数据覆写，不可恢复
  · 💿 启动盘制作: 基于 Ventoy，复制 ISO 即可启动

【使用步骤】
  1. 插入U盘并点击"刷新"
  2. 勾选要操作的设备
  3. 点击对应功能按钮
  4. 按提示输入密码 (用于提权)
  5. 等待完成

【注意事项】
  · 操作过程中请勿拔除设备
  · 格式化和擦除会销毁所有数据，请先备份
  · 启动盘制作需联网下载 Ventoy (仅首次)"""
            QMessageBox.information(self, "使用帮助", help_text)

        def show_about(self):
            about_text = """关于 U盘只读修复工具

本工具用于检测和修复U盘只读状态。"""
            QMessageBox.information(self, "关于", about_text)

        def refresh_devices(self):
            self.devices = USBAnalyzer.get_usb_devices()
            self.devices_table.setRowCount(len(self.devices))
            for i, device in enumerate(self.devices):
                checkbox = QCheckBox()
                checkbox.stateChanged.connect(lambda s, idx=i: self.on_device_checked(s, idx))
                self.devices_table.setCellWidget(i, 0, checkbox)
                self.devices_table.setItem(i, 1, QTableWidgetItem(device['name']))
                self.devices_table.setItem(i, 2, QTableWidgetItem(device['size']))
                status_item = QTableWidgetItem(device['status'])
                status_item.setForeground(Qt.red if device['readonly'] else Qt.darkGreen)
                self.devices_table.setItem(i, 3, status_item)
                fstypes = [p['fstype'] for p in device['partitions'] if p['fstype'] and p['fstype'] != '未知']
                self.devices_table.setItem(i, 4, QTableWidgetItem(', '.join(fstypes) if fstypes else '未知'))

        def on_device_checked(self, state, index):
            if state == Qt.Checked:
                # Uncheck others
                for i in range(self.devices_table.rowCount()):
                    if i != index:
                        w = self.devices_table.cellWidget(i, 0)
                        if w: w.blockSignals(True); w.setChecked(False); w.blockSignals(False)
                
                self.selected_device = self.devices[index]
                self.update_device_details()
                self.repair_btn.setEnabled(True)
                self.format_btn.setEnabled(True)
                self.erase_btn.setEnabled(True)
                self.ventoy_btn.setEnabled(True)
            else:
                self.selected_device = None
                self.details_text.clear()
                self.repair_btn.setEnabled(False)
                self.format_btn.setEnabled(False)
                self.erase_btn.setEnabled(False)
                self.ventoy_btn.setEnabled(False)

        def on_device_selected(self, row, column):
            w = self.devices_table.cellWidget(row, 0)
            if w: w.setChecked(True)

        def update_device_details(self):
            if not self.selected_device: return
            d = self.selected_device
            
            # 根据当前主题决定 HTML 颜色
            is_dark = "Dark Hacker" in self.theme_combo.currentText()
            text_color = "#c9d1d9" if is_dark else "#334155"
            label_color = "#8b949e" if is_dark else "#64748b"
            border_color = "#30363d" if is_dark else "#e2e8f0"
            status_color = "#ef4444" if d['readonly'] else ("#3fb950" if is_dark else "#10b981")
            accent_color = "#58a6ff" if is_dark else "#3b82f6"
            
            html = f"""
            <div style='line-height: 1.4; color: {text_color}; font-size: 13px;'>
                <table width='100%' cellpadding='2'>
                    <tr>
                        <td width='70'><b style='color: {label_color};'>设备名称:</b></td><td>{d['name']}</td>
                        <td width='70'><b style='color: {label_color};'>设备路径:</b></td><td><code>{d['path']}</code></td>
                    </tr>
                    <tr>
                        <td><b style='color: {label_color};'>设备容量:</b></td><td>{d['size']}</td>
                        <td><b style='color: {label_color};'>当前状态:</b></td><td><b style='color: {status_color};'>{d['status']}</b></td>
                    </tr>
                </table>
                <div style='margin-top: 8px; border-top: 1px solid {border_color}; padding-top: 6px;'>
                    <b style='color: {label_color};'>分区详情:</b>
                </div>
                <table width='100%' cellpadding='1' style='font-size: 12px; color: {label_color};'>
            """
            
            if not d['partitions']:
                html += f"<tr><td><i style='color: {label_color};'>(无分区信息)</i></td></tr>"
            else:
                for p in d['partitions']:
                    html += f"<tr><td>• <b style='color: {text_color};'>{p['name']}</b>: {p['fstype']} ({p['size']}) &nbsp;→&nbsp; <code style='color: {accent_color};'>{p['mountpoint']}</code></td></tr>"
            
            html += "</table></div>"
            self.details_text.setHtml(html)

        def set_busy(self, busy):
            """统一设置忙碌状态，禁用/恢复所有操作按钮"""
            enabled = not busy
            self.repair_btn.setEnabled(enabled and self.selected_device is not None)
            self.format_btn.setEnabled(enabled and self.selected_device is not None)
            self.erase_btn.setEnabled(enabled and self.selected_device is not None)
            self.ventoy_btn.setEnabled(enabled and self.selected_device is not None)
            self.refresh_btn.setEnabled(enabled)
            self.progress_bar.setVisible(busy)
            if busy:
                self.progress_bar.setValue(0)
                self.status_indicator.setText("工作中")
                self.status_indicator.setStyleSheet("color: #9a6700; font-size: 11px; font-weight: 500; padding: 3px 10px; background-color: #fff8c5; border: 1px solid #d4a72c;")
            else:
                self.status_indicator.setText("就绪")
                self.status_indicator.setStyleSheet("color: #1a7f37; font-size: 11px; font-weight: 500; padding: 3px 10px; background-color: #dafbe1; border: 1px solid #aceebb;")

        def repair_device(self):
            if not self.selected_device: return
            confirm = QMessageBox.question(self, "确认修复", 
                f"确定要修复设备 {self.selected_device['name']} 吗？\n\n注意：这需要管理员权限，可能会要求输入密码。",
                QMessageBox.Yes | QMessageBox.No)
            if confirm != QMessageBox.Yes: return
            
            self.set_busy(True)
            self.repair_worker = RepairWorker(self.selected_device['path'], os.path.abspath(sys.argv[0]))
            self.repair_worker.progress_updated.connect(self.update_progress)
            self.repair_worker.log_message.connect(self.log_message)
            self.repair_worker.repair_finished.connect(self.on_task_finished)
            self.repair_worker.start()

        def format_device(self):
            if not self.selected_device: return
            
            from PyQt5.QtWidgets import QComboBox, QRadioButton, QButtonGroup, QGridLayout, QGroupBox
            
            fd = QDialog(self)
            fd.setWindowTitle("格式化选项")
            fd.setMinimumWidth(480)
            fd.setStyleSheet("""
                QDialog { background-color: #ffffff; color: #0f172a; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; }
                QDialog QLabel { color: #334155; font-size: 13px; }
                QDialog QComboBox, QDialog QLineEdit { background: #f8fafc; color: #0f172a; padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 13px; }
                QDialog QComboBox:focus, QDialog QLineEdit:focus { border: 1px solid #3b82f6; }
                QDialog QComboBox::drop-down { border: none; width: 22px; }
                QDialog QCheckBox, QDialog QRadioButton { color: #334155; font-size: 13px; spacing: 8px; }
                QDialog QCheckBox::indicator, QDialog QRadioButton::indicator { width: 18px; height: 18px; border: 1px solid #cbd5e1; border-radius: 4px; background: #ffffff; }
                QDialog QRadioButton::indicator { border-radius: 9px; }
                QDialog QCheckBox::indicator:checked, QDialog QRadioButton::indicator:checked { background-color: #3b82f6; border-color: #3b82f6; }
                QDialog QPushButton { border-radius: 6px; font-size: 13px; font-weight: 600; outline: none; }
            """)
            fl = QVBoxLayout(fd)
            fl.setContentsMargins(24, 24, 24, 20)
            fl.setSpacing(12)
            
            # 设备信息
            dev_frame = QFrame()
            dev_frame.setStyleSheet("background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 6px;")
            dev_fl = QHBoxLayout(dev_frame)
            dev_fl.setContentsMargins(12, 6, 12, 6)
            dev_icon = QLabel("💾")
            dev_icon.setStyleSheet("font-size: 16px; background: transparent; border: none;")
            dev_fl.addWidget(dev_icon)
            dev_info = QLabel(f"  {self.selected_device['name']}  ·  {self.selected_device['size']}")
            dev_info.setStyleSheet("font-size: 13px; font-weight: 700; color: #166534; background: transparent; border: none;")
            dev_fl.addWidget(dev_info)
            dev_fl.addStretch()
            fl.addWidget(dev_frame)
            
            # 操作模式
            mode_box = QGroupBox("操作模式")
            mode_box.setStyleSheet("QGroupBox { font-weight: bold; color: #64748b; border: 1px solid #e2e8f0; border-radius: 6px; margin-top: 8px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }")
            mode_vl = QVBoxLayout(mode_box)
            mode_vl.setSpacing(6)
            whole_radio = QRadioButton("整盘格式化（清除分区表，创建单分区）")
            part_radio = QRadioButton("仅格式化指定分区（保留分区表）")
            whole_radio.setChecked(True)
            mode_group = QButtonGroup(fd)
            mode_group.addButton(whole_radio)
            mode_group.addButton(part_radio)
            mode_vl.addWidget(whole_radio)
            mode_vl.addWidget(part_radio)
            fl.addWidget(mode_box)
            
            # 分区选择
            part_label = QLabel("选择分区:")
            fl.addWidget(part_label)
            part_combo = QComboBox()
            partitions = self.selected_device.get('partitions', [])
            part_paths = []
            for p in partitions:
                display = f"{p['name']}  ·  {p['fstype']}  ·  {p['size']}  →  {p['mountpoint']}"
                part_combo.addItem(display)
                part_paths.append(f"/dev/{p['name']}")
            if not partitions:
                part_combo.addItem("(无分区)")
            fl.addWidget(part_combo)
            
            # 格式化选项
            opts_box = QGroupBox("格式化选项")
            opts_box.setStyleSheet("QGroupBox { font-weight: bold; color: #64748b; border: 1px solid #e2e8f0; border-radius: 6px; margin-top: 8px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }")
            opts_gl = QGridLayout(opts_box)
            opts_gl.setSpacing(10)
            opts_gl.setContentsMargins(12, 12, 12, 12)
            opts_gl.addWidget(QLabel("文件系统:"), 0, 0)
            fs_combo = QComboBox()
            fs_combo.addItems(["FAT32 (vfat)", "exFAT", "NTFS", "ext4"])
            opts_gl.addWidget(fs_combo, 0, 1)
            opts_gl.addWidget(QLabel("卷标 (可选):"), 1, 0)
            label_input = QLineEdit()
            label_input.setPlaceholderText("KYLIN_USB")
            opts_gl.addWidget(label_input, 1, 1)
            quick_check = QCheckBox("快速格式化")
            quick_check.setChecked(True)
            opts_gl.addWidget(quick_check, 2, 0, 1, 2)
            fl.addWidget(opts_box)
            
            # 警告
            warn_label = QLabel()
            warn_label.setWordWrap(True)
            fl.addWidget(warn_label)
            
            def update_mode():
                is_part = part_radio.isChecked()
                part_label.setVisible(is_part)
                part_combo.setVisible(is_part)
                if is_part:
                    warn_label.setText("ℹ️ 仅格式化选中的分区，其他分区数据不受影响。")
                    warn_label.setStyleSheet("color: #1e40af; font-size: 12px; padding: 8px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px;")
                else:
                    warn_label.setText("⚠️ 整盘格式化将清除分区表和所有数据！")
                    warn_label.setStyleSheet("color: #991b1b; font-size: 12px; padding: 8px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px;")
            whole_radio.toggled.connect(update_mode)
            update_mode()
            
            fl.addStretch()
            
            btn_layout = QHBoxLayout()
            ok_btn = QPushButton("开始格式化")
            ok_btn.setStyleSheet("background: #3b82f6; color: white; padding: 8px 24px; border-radius: 6px;")
            ok_btn.setCursor(Qt.PointingHandCursor)
            ok_btn.clicked.connect(fd.accept)
            cancel_btn = QPushButton("取消")
            cancel_btn.setStyleSheet("background: #ffffff; color: #475569; padding: 8px 24px; border: 1px solid #cbd5e1; border-radius: 6px;")
            cancel_btn.setCursor(Qt.PointingHandCursor)
            cancel_btn.clicked.connect(fd.reject)
            btn_layout.addStretch()
            btn_layout.addWidget(cancel_btn)
            btn_layout.addWidget(ok_btn)
            fl.addLayout(btn_layout)
            
            if fd.exec_() != QDialog.Accepted: return
            
            fs_map = {'FAT32 (vfat)': 'vfat', 'exFAT': 'exfat', 'NTFS': 'ntfs', 'ext4': 'ext4'}
            fstype = fs_map.get(fs_combo.currentText(), 'vfat')
            label = label_input.text().strip()
            quick = quick_check.isChecked()
            partition_only = part_radio.isChecked()
            partition_path = ''
            
            if partition_only:
                idx = part_combo.currentIndex()
                if idx < 0 or idx >= len(part_paths):
                    QMessageBox.warning(self, "错误", "请选择一个有效的分区")
                    return
                partition_path = part_paths[idx]
                confirm = QMessageBox.warning(self, "确认格式化分区",
                    f"即将格式化分区 {partition_path} 为 {fs_combo.currentText()}\n\n"
                    "该分区上的数据将被销毁，其他分区不受影响。\n确定继续吗？",
                    QMessageBox.Yes | QMessageBox.No)
            else:
                confirm = QMessageBox.warning(self, "⚠️ 数据将被销毁",
                    f"整盘格式化 {self.selected_device['name']} 为 {fs_combo.currentText()}\n\n"
                    "分区表将被清除，所有数据将被销毁！\n确定继续吗？",
                    QMessageBox.Yes | QMessageBox.No)
            if confirm != QMessageBox.Yes: return
            
            self.set_busy(True)
            self.format_worker = FormatWorker(
                self.selected_device['path'], fstype, label, quick,
                os.path.abspath(sys.argv[0]),
                partition_only=partition_only, partition_path=partition_path
            )
            self.format_worker.progress_updated.connect(self.update_progress)
            self.format_worker.log_message.connect(self.log_message)
            self.format_worker.finished.connect(self.on_task_finished)
            self.format_worker.start()

        def erase_device(self):
            if not self.selected_device: return
            
            confirm = QMessageBox.warning(self, "⚠️ 安全擦除 - 不可逆操作",
                f"将对 {self.selected_device['name']} ({self.selected_device['size']}) 执行安全擦除。\n\n"
                "此操作会用零数据覆写整个设备，数据将无法恢复！\n\n确定继续吗？",
                QMessageBox.Yes | QMessageBox.No)
            if confirm != QMessageBox.Yes: return
            
            # 二次确认
            double_confirm = QMessageBox.critical(self, "最终确认",
                "请再次确认：所有数据将被永久销毁！", QMessageBox.Yes | QMessageBox.No)
            if double_confirm != QMessageBox.Yes: return
            
            self.set_busy(True)
            self.erase_worker = EraseWorker(self.selected_device['path'], 1, os.path.abspath(sys.argv[0]))
            self.erase_worker.progress_updated.connect(self.update_progress)
            self.erase_worker.log_message.connect(self.log_message)
            self.erase_worker.finished.connect(self.on_task_finished)
            self.erase_worker.start()

        def install_ventoy(self):
            if not self.selected_device: return
            
            from PyQt5.QtWidgets import (QComboBox, QSpinBox, QRadioButton, QButtonGroup, 
                                        QGridLayout, QGroupBox, QDialog, QVBoxLayout, 
                                        QHBoxLayout, QLabel, QPushButton, QFrame, QMessageBox)
            
            vd = QDialog(self)
            vd.setWindowTitle("制作/升级 Ventoy 启动盘")
            vd.setMinimumSize(540, 580)
            vd.setStyleSheet("""
                QDialog { background-color: #ffffff; color: #0f172a; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; }
                QDialog QLabel { color: #334155; font-size: 13px; }
                QDialog QComboBox { 
                    background: #f8fafc; color: #0f172a; padding: 6px 10px; 
                    border: 1px solid #cbd5e1; border-radius: 4px; font-size: 13px;
                }
                QDialog QComboBox:focus { border: 1px solid #3b82f6; }
                QDialog QComboBox::drop-down { border: none; width: 22px; }
                QDialog QComboBox QAbstractItemView {
                    background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                    selection-background-color: #eff6ff; selection-color: #2563eb;
                    font-size: 13px;
                }
                QDialog QSpinBox {
                    background: #f8fafc; color: #0f172a; padding: 6px; 
                    border: 1px solid #cbd5e1; border-radius: 4px; font-size: 13px;
                    min-width: 120px;
                }
                QDialog QSpinBox:focus { border: 1px solid #3b82f6; }
                QDialog QSpinBox::up-button, QDialog QSpinBox::down-button {
                    width: 24px; border: none; background: #e2e8f0; border-radius: 2px; margin: 1px;
                }
                QDialog QCheckBox, QDialog QRadioButton { color: #334155; font-size: 13px; spacing: 8px; }
                QDialog QCheckBox::indicator, QDialog QRadioButton::indicator { width: 18px; height: 18px; border: 1px solid #cbd5e1; border-radius: 4px; background: #ffffff; }
                QDialog QRadioButton::indicator { border-radius: 9px; }
                QDialog QCheckBox::indicator:checked, QDialog QRadioButton::indicator:checked { background-color: #3b82f6; border-color: #3b82f6; }
            """)
            
            vl = QVBoxLayout(vd)
            vl.setSpacing(14)
            vl.setContentsMargins(24, 24, 24, 20)
            
            # 标题
            title = QLabel("💿  Ventoy 启动盘管理")
            title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0f172a; padding-bottom: 2px;")
            vl.addWidget(title)
            
            # 设备信息卡片
            dev_frame = QFrame()
            dev_frame.setStyleSheet("background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 6px;")
            dev_fl = QHBoxLayout(dev_frame)
            dev_fl.setContentsMargins(10, 4, 10, 4)
            dev_icon = QLabel("🔌")
            dev_icon.setStyleSheet("font-size: 16px; background: transparent; border: none;")
            dev_fl.addWidget(dev_icon)
            dev_info = QLabel(f"  {self.selected_device['name']}　·　{self.selected_device['size']}")
            dev_info.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e40af; background: transparent; border: none;")
            dev_fl.addWidget(dev_info)
            dev_fl.addStretch()
            vl.addWidget(dev_frame)
            
            # 分隔线
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet("background-color: #e2e8f0; max-height: 1px; border: none;")
            vl.addWidget(sep)
            
            # 安装模式
            mode_label = QLabel("操作模式")
            mode_label.setStyleSheet("font-weight: 700; color: #64748b; font-size: 11px; text-transform: uppercase; letter-spacing: 1.2px;")
            vl.addWidget(mode_label)
            
            mode_layout = QHBoxLayout()
            install_radio = QRadioButton("全新安装 (清除数据)")
            update_radio = QRadioButton("升级安装 (不清除数据)")
            install_radio.setChecked(True)
            mode_group = QButtonGroup(vd)
            mode_group.addButton(install_radio)
            mode_group.addButton(update_radio)
            mode_layout.addWidget(install_radio)
            mode_layout.addWidget(update_radio)
            mode_layout.addStretch()
            vl.addLayout(mode_layout)
            
            # 高级选项容器
            options_box = QGroupBox("安装选项")
            options_box.setStyleSheet("QGroupBox { font-weight: bold; color: #64748b; border: 1px solid #e2e8f0; border-radius: 8px; margin-top: 12px; padding-top: 12px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }")
            options_layout = QGridLayout(options_box)
            options_layout.setContentsMargins(15, 15, 15, 15)
            options_layout.setSpacing(12)
            
            # 分区表类型
            options_layout.addWidget(QLabel("分区表类型:"), 0, 0)
            pt_combo = QComboBox()
            pt_combo.addItems(["MBR (兼容旧 BIOS)", "GPT (推荐 UEFI)"])
            pt_combo.setCurrentIndex(1)
            options_layout.addWidget(pt_combo, 0, 1)
            
            # 文件系统格式
            options_layout.addWidget(QLabel("分区文件系统:"), 1, 0)
            fs_combo = QComboBox()
            fs_combo.addItems(["exFAT (原生默认)", "NTFS (支持大文件)", "FAT32", "ext4"])
            fs_combo.setCurrentIndex(0)
            options_layout.addWidget(fs_combo, 1, 1)
            
            # 保留空间
            options_layout.addWidget(QLabel("尾部保留空间:"), 2, 0)
            reserve_spin = QSpinBox()
            reserve_spin.setRange(0, 65536)
            reserve_spin.setValue(256)
            reserve_spin.setSuffix("  MB")
            reserve_spin.setSpecialValueText("不保留")
            options_layout.addWidget(reserve_spin, 2, 1)
            
            # Secure Boot
            sb_check = QCheckBox("启用 Secure Boot 引导支持")
            sb_check.setChecked(True)
            options_layout.addWidget(sb_check, 3, 0, 1, 2)
            
            vl.addWidget(options_box)
            
            # 警告提示
            note_frame = QFrame()
            note_frame.setStyleSheet("background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;")
            note_fl = QVBoxLayout(note_frame)
            note_fl.setContentsMargins(16, 12, 16, 12)
            note = QLabel()
            note.setStyleSheet("font-size: 13px; font-weight: 500; background: transparent; border: none; line-height: 1.5;")
            note.setWordWrap(True)
            note_fl.addWidget(note)
            vl.addWidget(note_frame)
            
            vl.addStretch()
            
            # 按钮区
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(12)
            cancel_btn = QPushButton("取消")
            cancel_btn.setStyleSheet("background: #ffffff; color: #475569; padding: 8px 20px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; font-weight: 500; min-width: 80px;")
            cancel_btn.setCursor(Qt.PointingHandCursor)
            cancel_btn.clicked.connect(vd.reject)
            
            ok_btn = QPushButton("开始安装 Ventoy")
            ok_btn.setStyleSheet("background: #3b82f6; color: white; padding: 10px 24px; border: none; border-radius: 6px; font-size: 13px; font-weight: 600; min-width: 140px;")
            ok_btn.setCursor(Qt.PointingHandCursor)
            ok_btn.clicked.connect(vd.accept)
            
            btn_layout.addStretch()
            btn_layout.addWidget(cancel_btn)
            btn_layout.addWidget(ok_btn)
            vl.addLayout(btn_layout)
            
            # 动态更新警告提示与选项的可用性
            def update_ui_for_mode():
                if update_radio.isChecked():
                    options_box.setDisabled(True)
                    note.setText("ℹ️  升级操作不会格式化您的U盘，此操作仅更新 Ventoy 引导程序，不会破坏已有 ISO 数据。")
                    note_frame.setStyleSheet("background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px;")
                    note.setStyleSheet("color: #1e40af; font-size: 13px; font-weight: 500; background: transparent; border: none;")
                    ok_btn.setText("开始升级 Ventoy")
                else:
                    options_box.setDisabled(False)
                    note.setText("⚠️  全新安装会重新分区，设备上的数据将被完全清除！安装后只需将 ISO 文件拷入U盘即可。")
                    note_frame.setStyleSheet("background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;")
                    note.setStyleSheet("color: #991b1b; font-size: 13px; font-weight: 500; background: transparent; border: none;")
                    ok_btn.setText("开始安装 Ventoy")
            
            install_radio.toggled.connect(update_ui_for_mode)
            update_radio.toggled.connect(update_ui_for_mode)
            update_ui_for_mode()  # 初始化一下UI状态
            
            if vd.exec_() != QDialog.Accepted: return
            
            is_update = update_radio.isChecked()
            use_gpt = (pt_combo.currentIndex() == 1)
            secure_boot = sb_check.isChecked()
            reserve_mb = reserve_spin.value()
            
            # 获取映射后的文件系统类型
            fs_map = {0: 'exfat', 1: 'ntfs', 2: 'fat32', 3: 'ext4'}
            fs_type = fs_map.get(fs_combo.currentIndex(), 'exfat')
            
            # 二次确认
            if is_update:
                confirm = QMessageBox.question(self, "确认升级",
                    f"即将在 {self.selected_device['name']} 上升级 Ventoy。\n\n"
                    "此操作不会清除您的数据。确定继续吗？",
                    QMessageBox.Yes | QMessageBox.No)
            else:
                confirm = QMessageBox.warning(self, "⚠️ 数据将被销毁",
                    f"即将在 {self.selected_device['name']} 上安装 Ventoy。\n\n"
                    f"分区表: {'GPT' if use_gpt else 'MBR'}\n"
                    f"文件系统: {fs_type.upper()}\n"
                    "此操作将销毁设备上的所有数据！确定继续吗？",
                    QMessageBox.Yes | QMessageBox.No)
            if confirm != QMessageBox.Yes: return
            
            self.set_busy(True)
            self.ventoy_worker = VentoyWorker(
                self.selected_device['path'], os.path.abspath(sys.argv[0]),
                use_gpt=use_gpt, secure_boot=secure_boot, reserve_mb=reserve_mb, 
                is_update=is_update, fs_type=fs_type
            )
            self.ventoy_worker.progress_updated.connect(self.update_progress)
            self.ventoy_worker.log_message.connect(self.log_message)
            self.ventoy_worker.finished.connect(self.on_task_finished)
            self.ventoy_worker.start()

        def update_progress(self, value, message):
            self.progress_bar.setValue(value)
            self.status_label.setText(message)

        def log_message(self, message):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.append(f"[{timestamp}] {message}")

        def on_task_finished(self, success, message):
            self.set_busy(False)
            self.status_label.setText("就绪")
            
            if success:
                QMessageBox.information(self, "成功", message)
                self.refresh_devices()
            else:
                QMessageBox.warning(self, "失败", message)

    from PyQt5.QtCore import Qt
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    

    window = USBFixTool()
    window.show()
    sys.exit(app.exec_())

    return dialog.exec_() == QDialog.Accepted

def main():
    parser = argparse.ArgumentParser(description="U盘多功能工具箱")
    parser.add_argument('--repair', help="修复指定设备 (CLI模式)", metavar="DEVICE_PATH")
    parser.add_argument('--format', help="格式化指定设备 (CLI模式)", metavar="DEVICE_PATH")
    parser.add_argument('--fstype', help="格式化文件系统类型", default="vfat", choices=['vfat', 'exfat', 'ntfs', 'ext4'])
    parser.add_argument('--label', help="格式化卷标", default="")
    parser.add_argument('--quick', help="快速格式化", action='store_true')
    parser.add_argument('--format-partition', help="仅格式化指定分区路径 (如 /dev/sda1)", metavar="PARTITION_PATH", default="")
    parser.add_argument('--erase', help="安全擦除指定设备 (CLI模式)", metavar="DEVICE_PATH")
    parser.add_argument('--passes', help="擦除遍数", type=int, default=1)
    parser.add_argument('--ventoy', help="安装 Ventoy 到指定设备 (CLI模式)", metavar="DEVICE_PATH")
    parser.add_argument('--ventoy-update', help="升级 Ventoy (不清除数据)", action='store_true')
    parser.add_argument('--ventoy-gpt', help="Ventoy 使用 GPT 分区表", action='store_true')
    parser.add_argument('--ventoy-secureboot', help="Ventoy 启用 Secure Boot", action='store_true')
    parser.add_argument('--ventoy-reserve', help="Ventoy 保留空间 (MB)", type=int, default=0)
    parser.add_argument('--ventoy-fstype', help="Ventoy 分区文件系统 (ntfs/exfat/fat32/ext4)", default="ntfs")
    args = parser.parse_args()
    
    if args.repair:
        if os.geteuid() != 0:
            print("[PROGRESS]:0:错误: 需要Root权限执行修复")
            sys.exit(1)
        repairman = USBRepairman(args.repair)
        repairman.run_repair()
    elif args.format:
        if os.geteuid() != 0:
            print("[PROGRESS]:0:错误: 需要Root权限执行格式化")
            sys.exit(1)
        partition_only = bool(args.format_partition)
        formatter = USBFormatter(args.format, args.fstype, args.label, args.quick,
                                 partition_only=partition_only, partition_path=args.format_partition)
        success = formatter.run_format()
        sys.exit(0 if success else 1)
    elif args.erase:
        if os.geteuid() != 0:
            print("[PROGRESS]:0:错误: 需要Root权限执行安全擦除")
            sys.exit(1)
        eraser = SecureEraser(args.erase, args.passes)
        success = eraser.run_erase()
        sys.exit(0 if success else 1)
    elif args.ventoy:
        if os.geteuid() != 0:
            print("[PROGRESS]:0:错误: 需要Root权限安装 Ventoy")
            sys.exit(1)
        installer = VentoyInstaller(args.ventoy, 
                                    use_gpt=args.ventoy_gpt,
                                    secure_boot=args.ventoy_secureboot,
                                    reserve_mb=args.ventoy_reserve,
                                    is_update=args.ventoy_update,
                                    fs_type=args.ventoy_fstype)
        success = installer.run_install()
        sys.exit(0 if success else 1)
    else:
        run_gui()

if __name__ == '__main__':
    main()
