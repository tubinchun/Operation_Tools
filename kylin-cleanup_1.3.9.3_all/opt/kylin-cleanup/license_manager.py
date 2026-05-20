#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kylin/openKylin 清理助手授权与运行状态遥测引擎 (License & Telemetry Manager)
"""

import os
import sys
import uuid
import hashlib
import json
import base64
import urllib.request
import urllib.error
import subprocess
import logging

LOG_FILE = "/var/log/kylin-cleanup-license.log"
LICENSE_FILE = "/etc/kylin-cleanup.lic"
TELEMETRY_URL = "http://api.ygwid.cn:8081/api/telemetry"
SECRET_SALT = "kylin_pro_v1_super_secret_salt_2024"
TOOL_NAME = "kylin-cleanup"

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    handlers=[logging.StreamHandler(),
                              logging.FileHandler(LOG_FILE) if os.access("/var/log", os.W_OK) else logging.NullHandler()])

def get_mac_address():
    """获取设备首个物理网卡的纯净 MAC 地址"""
    mac_num = uuid.getnode()
    mac = ':'.join(('%012X' % mac_num)[i:i+2] for i in range(0, 12, 2))
    return mac

def get_os_version():
    """读取 Kylin 特有的 .kyinfo 或底层 /etc/os-release 获取确切发行版"""
    # 优先从 .kyinfo 获取详细的 dist_id
    if os.path.exists('/etc/.kyinfo'):
        try:
            with open('/etc/.kyinfo', 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if 'dist_id=' in line:
                        return line.split('=', 1)[1].strip()
        except Exception:
            pass

    # 兜底使用 os-release
    if os.path.exists('/etc/os-release'):
        try:
            with open('/etc/os-release', 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('PRETTY_NAME='):
                        return line.split('=')[1].strip().strip('"').strip("'")
        except Exception:
            pass
            
    return "Unknown-Kylin"

def get_system_machine_id():
    """获取系统级的机器唯一标识符 (通常对所有用户可见)"""
    for p in ['/etc/machine-id', '/var/lib/dbus/machine-id']:
        if os.path.exists(p):
            try:
                with open(p, 'r') as f:
                    return f.read().strip()
            except:
                pass
    return "UNKNOWN_MID"

def get_device_sn():
    """多级尝试获取机器序列号，增加非 root 用户的兼容性"""
    
    # 1. 优先从官方 .kyinfo 获取 (通常对全部用户可读)
    if os.path.exists('/etc/.kyinfo'):
        try:
            with open('/etc/.kyinfo', 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if '=' in line:
                        parts = line.split('=', 1)
                        if len(parts) < 2: continue
                        k = parts[0].strip().lower()
                        v = parts[1].strip()
                        if k in ['sn', 'key'] and v and v != "0":
                            return v.upper()
        except: pass
            
    # 2. 尝试从 sysfs 获取 (部分内核允许普通用户读取)
    for p in ['/sys/class/dmi/id/product_serial', '/sys/class/dmi/id/board_serial']:
        if os.path.exists(p):
            try:
                with open(p, 'r') as f:
                    sn = f.read().strip()
                    if sn and "To be filled" not in sn and "None" not in sn:
                        return sn
            except: pass

    # 3. 实在不行尝试 dmidecode (由于 sudo -n 限制，UI 模式下可能失败)
    try:
        result = subprocess.run(['sudo', '-n', 'dmidecode', '-s', 'system-serial-number'], 
                                capture_output=True, text=True, timeout=1)
        if result.returncode == 0:
            sn = result.stdout.strip()
            if sn and "To be filled" not in sn:
                return sn
    except: pass
        
    return "UNKNOWN_SN"

def generate_hardware_fingerprint():
    """组合关键标识获取硬件指纹字典"""
    return {
        "mac": get_mac_address(),
        "os_version": get_os_version(),
        "sn": get_device_sn(),
        "mid": get_system_machine_id()
    }

def get_machine_code():
    """获取显示给用户的简短机器码 (基于 MID/MAC/SN/SALT 的哈希截断)"""
    fp = generate_hardware_fingerprint()
    # 使用 MID (machine-id) 作为主锚点，更稳健
    raw_str = f"{fp['mid']}_{fp['mac']}_{fp['sn']}_{SECRET_SALT}"
    hash_obj = hashlib.sha256(raw_str.encode('utf-8'))
    b32 = base64.b32encode(hash_obj.digest()).decode('utf-8')
    return b32[:16]

def _cipher_data(data, encrypt=True):
    """简易轻量级流加密（XOR + Base64），防明文嗅探"""
    key_bytes = SECRET_SALT.encode('utf-8')
    if encrypt:
        json_bytes = json.dumps(data).encode('utf-8')
        res = bytearray(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(json_bytes))
        return base64.b64encode(res).decode('utf-8')
    else:
        enc = base64.b64decode(data)
        res = bytearray(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(enc))
        return json.loads(res.decode('utf-8'))

def verify_license_key(key, machine_code=None):
    """
    离线激活算法 (4位数字验证)
    原理：激活码 = SHA256(机器码 + 特定盐值) 的整型模 10000，取 4 位填充
    """
    if not key:
        return False
        
    if not machine_code:
        machine_code = get_machine_code()
        
    expected_hash = hashlib.sha256((machine_code + "_" + SECRET_SALT).encode('utf-8'))
    expected_key = str(int(expected_hash.hexdigest(), 16) % 10000).zfill(4)
    
    return key.strip() == expected_key

def read_local_license():
    """从统一的安全凭证库读取离线激活码"""
    if os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE, 'r') as f:
                return f.read().strip()
        except Exception as e:
            logging.error(f"无法读取授权文件 {LICENSE_FILE}: {e}")
    return ""

def write_local_license(key):
    """将有效的激活码持久化保存 (仅在内容变化时触发提权)"""
    if not key:
        return False
        
    try:
        # 1. 检查当前文件内容，如果已经一致则跳过，避免触发 sudo/pkexec 弹窗
        if os.path.exists(LICENSE_FILE):
            with open(LICENSE_FILE, 'r') as f:
                if f.read().strip() == key.strip():
                    return True
                    
        # 2. 由于存放在 /etc 下，需要采用提权手段写入
        import shutil
        sudo_cmd = ["sudo", "-n"]
        for cmd in ["pkexec", "kysec-polkit", "kdesu", "gksudo", "sudo"]:
            if shutil.which(cmd):
                sudo_cmd = [cmd]
                break
                
        p = subprocess.Popen(sudo_cmd + ["tee", LICENSE_FILE], 
                             stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.communicate(input=key.encode('utf-8'))
        return p.returncode == 0
    except Exception as e:
        logging.error(f"持久化授权文件失败: {e}")
        return False

def check_online_activation():
    """
    通过 HTTP POST 上报设备统计特征，并从远端获取授权状态。
    无论本地是否激活，都会尝试上报心跳以同步状态。
    """
    local_key = read_local_license()
    is_locally_active = verify_license_key(local_key)
    
    payload = generate_hardware_fingerprint()
    payload['machine_code'] = get_machine_code()
    payload['tool_name'] = TOOL_NAME
    payload['is_active'] = is_locally_active
    payload['license_key'] = local_key if is_locally_active else ""
    
    encrypted_payload = _cipher_data(payload, encrypt=True)
    wrapper = {"data": encrypted_payload}
    json_data = json.dumps(wrapper).encode('utf-8')
    
    req = urllib.request.Request(TELEMETRY_URL, data=json_data, 
                                 headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                result_wrapper = json.loads(response.read().decode('utf-8'))
                if 'data' in result_wrapper:
                    result = _cipher_data(result_wrapper['data'], encrypt=False)
                    if result.get('status') == 'active':
                        license_key = result.get('license_key')
                        if license_key:
                            write_local_license(license_key)
                        return True
    except Exception as e:
        logging.warning(f"在线统计服务器连接失败，转为离线验证: {e}")
        
    return False

def check_active():
    """综合验证入口：优先看本地文件离线密钥是否合法，同时尝试联网上报状态同步"""
    local_license = read_local_license()
    is_active = verify_license_key(local_license)
    
    # 异步或作为副作用尝试联网同步（如果联网同步成功且返回了新授权，会更新本地）
    # 在此由于是脚本运行，我们同步调用，但即使失败也以本地为准
    try:
        online_res = check_online_activation()
        if online_res:
            is_active = True
    except:
        pass
        
    return is_active

def parse_qr_activation_url():
    """生成用于离线终端请求激活码的完整扫描 URL（加密载荷以实现隐身采集）"""
    mc = get_machine_code()
    fp = generate_hardware_fingerprint()
    import urllib.parse
    
    # 将详尽信息打包成 JSON 并进行 Base64 编码，实现 URL 层面上的“隐身”
    payload_data = {
        "mc": mc,
        "t": TOOL_NAME,
        "m": fp['mac'],
        "s": fp['sn'],
        "ov": fp['os_version'],
        "mid": fp['mid']
    }
    payload_json = json.dumps(payload_data)
    token = base64.b64encode(payload_json.encode('utf-8')).decode('utf-8')
    
    # 您的企业自动算号注册机页面搭建在如下网址
    REGISTER_URL = f"http://api.ygwid.cn:8081/admin/qr_activate?token={urllib.parse.quote(token)}" 
    return REGISTER_URL

# 若本模块作为命令行独立被调用 (bash 调用验证用)
if __name__ == "__main__":
    if check_active():
        sys.exit(0)  # 0代表已激活，放行执行后续 bash 代码
    else:
        sys.exit(1)  # 1代表未激活，拦截
