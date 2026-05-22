import socket
import struct
import fcntl
import configparser
import base64
import subprocess
import re
import threading
import os,shutil
import logging
from urllib.parse import parse_qs, unquote, urlparse
import queue
from services import helpers
import json
MAX_REQUEST_SIZE = 1024 * 1024 * 1024  # 10MB
ALLOWED_METHODS = ['GET', 'POST']
CHUNK_SIZE = 4096 * 1024  # 4MB分块大小
FILE_ROOT = os.path.abspath('netboot')
sys_logger = logging.getLogger('M-PXE')
http_logger=helpers.get_child_logger(sys_logger, 'HTTP')
routes = {}
msg_queue = queue.Queue()
def route(path):
    def decorator(func):
        routes[path] = func
        return func
    return decorator
@route(r'^/?$')
def redirect_handler(params):
    response = [
        "HTTP/1.1 301 Moved Permanently",
        "Location: /web/index.html",
        "Content-Type: text/html; charset=utf-8",
        "\r\n"
    ]
    html_content = f"""
    <!DOCTYPE html>
    <html>
        <head><title>Redirecting...</title></head>
        <body>
            <h1>Redirecting to /web/index.html</h1>
            <p>如果浏览器没有自动跳转，请<a href="/web/index.html">点击这里</a>。</p>
        </body>
    </html>
    """
    return "\r\n".join(response).encode() + html_content.encode()

def check_port_available(port,protocol="tcp"):
    """检查端口是否可绑定（未被占用）"""
    if protocol=="tcp":
        opt=socket.SOCK_STREAM
    else:
        opt=socket.SOCK_DGRAM
    try:
        with socket.socket(socket.AF_INET, opt) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
            s.bind(('', port))  # 尝试绑定所有接口
            s.close()
            return "not running"
    except OSError:
        return "running"
    
def get_nic_info():
    """
    获取 Linux 系统中所有网卡的 IPv4 地址和子网掩码
    返回格式: [{'nic': 网卡名称, 'ip': IP地址, 'mask': 子网掩码}, ...]
    """
    nic_info = []
    
    with open("/proc/net/dev", "r") as f:
        lines = f.readlines()[2:]
        nics = [line.split(":")[0].strip() for line in lines]
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        for nic in nics:
            try:
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
            except IOError:
                continue
    
    return nic_info

@route('/web/get_blackwhitelist')
def get_blackwhitelist(params):
    """获取黑白名单配置"""
    try:
        with open('config/config.json', 'r') as file:
            config = json.load(file)
        return format_response(200, {
            "code": 0,
            "whitelist": config.get('DHCP_WHITELIST', []),
            "blacklist": config.get('DHCP_BLACKLIST', [])
        })
    except Exception as e:
        return format_response(200, {"code": 1, "msg": str(e)})

def parse_mac_list(mac_str):
    """解析MAC地址列表，支持逗号和换行分隔"""
    if not mac_str:
        return []
    # 先按换行分割，再按逗号分割
    macs = []
    for line in mac_str.replace('\r\n', '\n').split('\n'):
        for mac in line.split(','):
            mac = mac.strip().upper()
            if mac:
                macs.append(mac)
    return macs

@route('/web/set_blackwhitelist')
def set_blackwhitelist(params):
    """设置黑白名单"""
    try:
        whitelist_str = params.get('whitelist', '')
        blacklist_str = params.get('blacklist', '')
        
        whitelist = parse_mac_list(whitelist_str)
        blacklist = parse_mac_list(blacklist_str)
        
        with open('config/config.json', 'r') as file:
            config = json.load(file)
        config['DHCP_WHITELIST'] = whitelist
        config['DHCP_BLACKLIST'] = blacklist
        with open('config/config.json', 'w') as file:
            json.dump(config, file, indent=4)
        
        restart_thread = threading.Thread(target=restartservice)
        restart_thread.daemon = True
        restart_thread.start()
        return format_response(200, {"code": 0, "msg": "更新成功"})
    except Exception as e:
        return format_response(200, {"code": 1, "msg": str(e)})

@route('/web/get_info')
def get_networkinfo(params):
    network_details = []

    with open('config/config.json', 'r') as file:
        config =json.load(file)

    network_details=get_nic_info()
    
    service_status={}
    service_status["nfs"]=check_port_available(2049)
    service_status["dhcp"]=check_port_available(67,"udp")
    service_status["tftp"]=check_port_available(69,"udp")
    service_status["http"]="running"

    return format_response(200, {"code": 0, "config": config,"data":network_details,"servicestatus":service_status})

@route('/web/get_server_info')
def get_server_info(params):

    # 获取所有网卡的地址信息
    with open('config/config.json', 'r') as file:
        configjson =json.load(file)

    directory = 'netboot/config/'
    code=0
    ipxefilelist=[]
    config = configparser.ConfigParser(
        allow_no_value=True,        # 允许空值
        delimiters=('='),           # 分隔符
        comment_prefixes=('#', ';') # 注释标识
    )

    try:
        # 使用 os.listdir() 获取文件夹中的文件列表
        directory_list = os.listdir(directory)
        
        # 输出文件列表
        for directory_name in directory_list:
            fileinfo={}
            config_file = directory+directory_name+"/config.ini"
            config.read(config_file, encoding='utf-8')
            fileinfo["isoname"] = config.get('config', 'isoname', fallback="mpxe.iso")
            fileinfo["ipxename"]=directory_name
            ipxefilelist.append(fileinfo)
            config.clear()
        fileinfo={}
        fileinfo["isoname"] = "本地启动"
        fileinfo["ipxename"]="local"
        ipxefilelist.append(fileinfo)
    except Exception as e:
        code=1
        msg="发生错误："+str(e)
        return format_response(200, {"code": code, "msg": msg})
    
    return format_response(200, {"code": code, "config": configjson,"data":ipxefilelist})

def write_config(new_config):
    with open('config/config.json', 'w') as file:
        json.dump(new_config, file, indent=4)

def format_response(status, data):
    """标准化响应格式"""
    return f'HTTP/1.1 {status}\r\nContent-Type: application/json\r\n\r\n{json.dumps(data)}'

@route('/web/saveandrestart')
def saveandrestart(params):

    required_fields = ['ip_address', 'gateway','name', 'netmask', 'ip_start', 'ip_end']
    if not all(params.get(field) for field in required_fields):
        return format_response(400, {"code": -1, "msg": "缺少必要参数"})
    # 使用上下文管理器确保文件操作安全
    with open('config/config.json', 'r+') as file:
        try:
            config = json.load(file)
        except json.JSONDecodeError as e:
            return format_response(500, {"code": -2, "msg": f"配置文件损坏: {str(e)}"})
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
        file.seek(0)
        json.dump(config, file, indent=4)
        file.truncate()
    write_config(config)
    output = subprocess.check_output(['bash', 'scripts/gen_boot_ipxe.sh'], text=True)
    restart_thread = threading.Thread(target=restartservice)
    restart_thread.daemon = True
    restart_thread.start()
    return format_response(200, {"code": 0, "msg": f"更新成功"})

@route('/web/setserver')
def setserver(params):
    with open('config/config.json', 'r') as file:
        config =json.load(file)

    log_level = params.get('log_level')
    menu_timeout = params.get('menu_timeout')
    menu_default = params.get('menu_default')
    http_port = int(params.get('http_port'))
    old_http_port = config["HTTP_PORT"]
    config.update({
        "LOG_LEVEL": log_level,
        "MENU_DEFAULT": menu_default,
        "MENU_TIMEOUT": menu_timeout,
        "HTTP_PORT": http_port
    })
    write_config(config)
    restart_thread = threading.Thread(target=restartservice)
    restart_thread.daemon = True
    restart_thread.start()
    if http_port != old_http_port:
        output = subprocess.check_output(['bash', 'scripts/gen_boot_ipxe.sh'], text=True)
    # 返回响应
    return format_response(200, {"code": 0, "msg": f"重启成功"})

@route('/web/getisoipxe')
def getisoipxe(params):
    directory = 'netboot/config/'
    code=0
    msg=""
    ipxefilelist=[]
    config = configparser.ConfigParser(
        allow_no_value=True,        # 允许空值
        delimiters=('='),           # 分隔符
        comment_prefixes=('#', ';') # 注释标识
    )

    try:
        # 使用 os.listdir() 获取文件夹中的文件列表
        directory_list = os.listdir(directory)
        # 输出文件列表
        for directory_name in directory_list:
            fileinfo={}
            config_file = directory+directory_name+"/config.ini"
            if os.path.exists(config_file):
                config.read(config_file, encoding='utf-8')
                fileinfo["isoname"] = config.get('config', 'isoname', fallback="mpxe.iso")
                fileinfo["extpathname"] = config.get('config', 'extpathname', fallback="mpxe_extfile")
                fileinfo["autoinstall"] = config.get('config', 'autoinstall', fallback="false")
                fileinfo["class"] = config.get('config', 'class', fallback="Preseed")
                fileinfo["ipxename"]=directory_name
                    
                with open(directory+directory_name+"/grub.cfg_tpl",'r') as file:
                    file_read=file.readlines()
                    fileinfo["grubcfg"]=''.join(file_read[0:])

                if os.path.exists(directory+directory_name+"/extfile.ini"):
                    with open(directory+directory_name+"/extfile.ini",'r') as file:
                        file_read=file.readlines()
                        fileinfo["mpxe_extfile"]=''.join(file_read[0:])

                with open(directory+directory_name+"/autoinstall.cfg_tpl",'r') as file:
                    file_read=file.readlines()
                    fileinfo["autoinstallcfg"]=''.join(file_read[0:])
                
                ipxefilelist.append(fileinfo)
                config.clear()
    except Exception as e:
        code=1
        msg="发生错误："+str(e)
    return format_response(200, {"code": code, "msg": msg,"data":ipxefilelist})

@route('/web/setisoipxe')
def setisoipxe(params):
    directory = 'netboot/config/'
    ipxename = params.get('ipxename')
    isoname = params.get('isoname')
    extpathname = params.get('extpathname')
    autoinstall = params.get('autoinstall')
    if autoinstall == "":
        autoinstall="false"
    code=0
    msg="保存成功"
    if not os.path.exists(directory+ipxename):
        os.mkdir(directory+ipxename)
    config = configparser.ConfigParser(
        allow_no_value=True,        # 允许空值
        delimiters=('='),           # 分隔符
        comment_prefixes=('#', ';') # 注释标识
    )
    config_file = directory+ipxename+"/config.ini"
    mpxe_extfile= directory+ipxename+"/extfile.ini"
    config.read(config_file, encoding='utf-8')
    if not config.has_section('config'):
        config.add_section('config')
    config.set('config', 'isoname', isoname)
    config.set('config', 'extpathname', extpathname)
    config.set('config', 'autoinstall', autoinstall)
    with open(config_file, 'w') as f:
        config.write(f)
    try:
        mpxe_extfile_content = params.get('mpxe_extfile')
        if mpxe_extfile_content:
            with open(mpxe_extfile,'w') as file:
                file.writelines(mpxe_extfile_content)
        grubcfg = params.get('grubcfg')
        if grubcfg:
            with open(directory+ipxename+"/grub.cfg_tpl",'w') as file:
                file.writelines(base64.b64decode(grubcfg).decode())
        if not os.path.exists(directory+ipxename+"/grub.efi"):
            import hashlib
            md5_hash = hashlib.md5()
            isopath="../iso/"+isoname
            md5_hash.update(isopath.encode('utf-8'))
            md5name = md5_hash.hexdigest()[:9]
            shutil.copy(directory+md5name+"/grub.efi",directory+ipxename)
        autoinstallcfg = params.get('autoinstallcfg')
        if autoinstallcfg:
            with open(directory+ipxename+"/autoinstall.cfg_tpl",'w') as file:
                file.writelines(base64.b64decode(autoinstallcfg).decode())
        output = subprocess.check_output(['bash', 'scripts/gen_boot_ipxe.sh','--notremount'], text=True)
    except Exception as e:
        code=1
        msg="发生错误："+str(e)
        http_logger.error(str(e))
    return format_response(200, {"code": code, "msg": msg})

@route('/web/delisoipxe')
def delisoipxe(params):
    ipxename = params.get('ipxename')
    code=0
    msg="删除成功"
    try:
        shutil.rmtree("netboot/config/"+ipxename)
        restart_thread = threading.Thread(target=restartservice)
        restart_thread.daemon = True
        restart_thread.start()
    except Exception as e:
        code=1
        msg="发生错误："+str(e)
    return format_response(200, {"code": code, "msg": msg})


@route('/web/restart')
def restartservice(params=""):
    global msg_queue
    msg_queue.put("restart")
    msg="restarting"
    return format_response(200, {"code": 0, "msg": msg})

@route('/web/rescan')
def rescan(params):
    output = subprocess.check_output(['bash', 'scripts/gen_boot_ipxe.sh','--rescan'], text=True)
    restart_thread = threading.Thread(target=restartservice)
    restart_thread.daemon = True
    restart_thread.start()
    msg=("重新扫描完成")
    return format_response(200, {"code": 0, "msg": msg})

@route('/monitor/statusreport')
def statusreport(params):
    progress = params.get('progress')
    status = params.get('status')
    msg = params.get('msg')
    mac = params.get('mac')
    
    with open('config/leases.json', 'r') as file:
        config=json.load(file)
        file.close()
        if mac in config:
            config[mac]["progress"]=progress
            config[mac]["status"]=status
            config[mac]["msg"]=msg
            with open('config/leases.json', 'w') as file:
                json.dump(config, file, indent=4)
                file.close()

    return format_response(200, {"code": 0, "msg": msg})


@route('/web/getclientlist')
def getclientlist(params):
    clientlist=[]
    msg=""
    with open('config/leases.json', 'r') as file:
        config=json.load(file)
        file.close()
        for key,entry in config.items():
            clientinfo={}
            clientinfo["mac"]=key
            clientinfo["ip"]=config[key]["ip"]
            clientinfo["isoname"]=""
            clientinfo["progress"]=0
            clientinfo["status"]="等待开始"
            try:
                clientinfo["isoname"]=config[key]["isoname"]
                clientinfo["progress"]=config[key]["progress"]
                clientinfo["status"]=config[key]["msg"]
            except:
                pass
            clientlist.append(clientinfo)

    return format_response(200, {"code": 0, "msg": msg, "data":clientlist})

@route(r'^/web/log$')
def get_log(params):
    """获取日志内容"""
    log_file = 'logs/pxe.log'
    try:
        lines = int(params.get('lines', 500))  # 默认返回最后500行
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            log_content = ''.join(all_lines[-lines:])
            return format_response(200, {"code": 0, "data": log_content})
    except FileNotFoundError:
        return format_response(200, {"code": 1, "msg": "日志文件不存在"})
    except Exception as e:
        return format_response(200, {"code": -1, "msg": str(e)})

sse_active = {}

def sse_log_handler(client):
    """SSE 流式日志处理器"""
    log_file = 'logs/pxe.log'
    client_addr = client.getpeername() if client else None
    sse_active[client_addr] = True
    try:
        with open(log_file, 'rb') as f:
            f.seek(0, 2)
            last_size = f.tell()
            client.sendall(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/event-stream\r\n"
                b"Cache-Control: no-cache\r\n"
                b"Connection: keep-alive\r\n"
                b"X-Accel-Buffering: no\r\n\r\n"
            )
            while client_addr in sse_active:
                try:
                    f.seek(0, 2)
                    current_size = f.tell()
                    if current_size > last_size:
                        f.seek(last_size)
                        new_content = f.read().decode('utf-8', errors='ignore')
                        for line in new_content.strip().split('\n'):
                            if line.strip():
                                client.sendall(f"data: {line.strip()}\n\n".encode())
                        last_size = current_size
                    elif current_size < last_size:
                        f.seek(0)
                        all_content = f.read().decode('utf-8', errors='ignore')
                        for line in all_content.strip().split('\n'):
                            if line.strip():
                                client.sendall(f"data: {line.strip()}\n\n".encode())
                        last_size = current_size
                    import time
                    time.sleep(0.3)
                except (ConnectionResetError, BrokenPipeError, OSError):
                    break
    except:
        pass
    finally:
        if client_addr in sse_active:
            del sse_active[client_addr]
        try:
            client.close()
        except:
            pass

@route(r'^/web/log/sse$')

def log_sse(params):
    return "__SSE__"


# ----------------------
# HTTP服务器
# ----------------------
class HTTPServer:
    def __init__(self, host='0.0.0.0', port=80, **server_settings):
        self.workers = []
        self.host = host
        self.port = port
        self.log_level = server_settings.get('log_level', False)
        self.logger = server_settings.get('logger', None)
        self.shutdown_flag = threading.Event()        

        self.mime_types = {
            '.html': 'text/html',
            '.htm': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.json': 'application/json'
        }

    def start(self,p_queue):        
        try:
            global msg_queue
            msg_queue=p_queue
            self.shutdown_flag.clear()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.settimeout(2)
            self.sock.bind((self.host, self.port))
            self.sock.listen(5)
            while not self.shutdown_flag.is_set():
                try:
                    client, addr = self.sock.accept()
                    worker = threading.Thread(target=self.handle_request, args=(client,addr))
                    self.workers.append(worker)
                    worker.start()
                except socket.timeout:
                    # 正常超时，继续检查关闭标志
                    continue
                except Exception as e:
                    self.logger.error(str(e))
                
        except KeyboardInterrupt:
            sys.exit('\nShutting down PXE Services...\n')
        finally:
            self.sock.close()
    def stop(self):
        """安全的服务停止"""
        self.logger.debug("正在关闭HTTP服务...")
        
        # 第一阶段：停止接受新连接
        self.shutdown_flag.set()
        
        # 第二阶段：关闭监听socket
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except OSError as e:
                self.logger.error(f"关闭socket异常: {str(e)}")        
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=5)
        self.logger.info("HTTP服务已安全停止")
    def is_safe_path(self, candidate_path):
        """强化路径安全检查"""
        file_root = os.path.abspath(FILE_ROOT)
        target_path = os.path.abspath(os.path.join(file_root, candidate_path))
        real_root = os.path.realpath(file_root)
        real_target = os.path.realpath(target_path)
        return real_target.startswith(real_root + os.sep) or real_target == real_root
    def handle_request(self, client,addr):
        try:
            request_data = b''
            headers = {}
            body = b''
            content_length = 0
            chunked = False
            # 设置接收超时(30秒)
            client.settimeout(30)
            # 第一阶段：接收请求头
            while b'\r\n\r\n' not in request_data:
                chunk = client.recv(4096)
                if not chunk:
                    break
                request_data += chunk
            if not request_data:
                return
            # 分割请求头和请求体
            header_end = request_data.find(b'\r\n\r\n')
            header_part = request_data[:header_end].decode(errors='ignore')
            body_part = request_data[header_end+4:]
            
            # 解析头部
            headers, _ = self.parse_request(header_part)
            
            # 获取内容长度和传输编码
            content_length = int(headers.get('Content-Length', 0))
            chunked = headers.get('Transfer-Encoding', '').lower() == 'chunked'
            # 第二阶段：接收请求体
            if chunked:
                # 分块传输处理
                while True:
                    # 查找块大小行
                    chunk_size_end = body_part.find(b'\r\n')
                    if chunk_size_end == -1:
                        # 需要更多数据
                        more_data = client.recv(4096)
                        if not more_data:
                            break
                        body_part += more_data
                        continue
                    chunk_size_line = body_part[:chunk_size_end]
                    try:
                        chunk_size = int(chunk_size_line, 16)
                    except ValueError:
                        break
                    # 0大小的块表示结束
                    if chunk_size == 0:
                        break
                    chunk_start = chunk_size_end + 2
                    chunk_end = chunk_start + chunk_size
                    
                    # 检查是否收到完整块
                    while len(body_part) < chunk_end + 2:
                        more_data = client.recv(4096)
                        if not more_data:
                            break
                        body_part += more_data
                    # 提取块数据
                    body += body_part[chunk_start:chunk_end]
                    body_part = body_part[chunk_end+2:]
            else:
                # 普通内容长度处理
                remaining = content_length - len(body_part)
                if remaining > 0:
                    # 接收剩余数据
                    while remaining > 0:
                        chunk = client.recv(min(4096, remaining))
                        if not chunk:
                            break
                        body_part += chunk
                        remaining -= len(chunk)
                body = body_part
            # 转换body为字符串
            try:
                body_str = body.decode('utf-8')
            except UnicodeDecodeError:
                body_str = body.decode('latin-1')
            # 合并参数
            query_params = parse_qs(headers.get('query', ''))
            post_params = parse_qs(body_str)
            merged_params = {}
            # 合并GET参数（保留重复参数的第一个值）
            for param, values in query_params.items():
                merged_params[param] = values[0] if values else ''
            # 合并POST参数（覆盖GET）
            for param, values in post_params.items():
                merged_params[param] = values[0] if values else ''
            # 动态路由匹配
            path = headers.get('path', '/web/index.html')
            handler = None
            for route_path in routes:
                if re.fullmatch(route_path, path):
                    handler = routes[route_path]
                    break
            if handler:
                response = handler(merged_params)
                if response == "__SSE__":
                    sse_log_handler(client)
                else:
                    client.sendall(response.encode() if isinstance(response, str) else response)
                    client.close()
            else:
                self.handle_file_request(headers, client,addr)
        except (ConnectionResetError, BrokenPipeError) as e:
            self.logger.warning(f"客户端连接中断: {str(e)}")
        except socket.timeout:
            self.logger.warning("请求接收超时")
        except Exception as e:
            self.logger.error(f"未知错误: {str(e)}")
            client.sendall(self.error_response(500, str(e)).encode())
        finally:
            client.close()
    def handle_file_request(self, headers, client,addr):
        """改进的文件处理方法（支持分块传输）"""
        try:
            # 获取并清洗路径（关键修改点）
            full_path = unquote(headers['path'])
            parsed_path = urlparse(full_path).path
            #如果加载过grub，则保存对应grub.cfg路径
            if "grub.efi" in parsed_path:
                with open('config/leases.json', 'r') as file:
                    config=json.load(file)
                    file.close()
                    for key, entry in config.items():
                        if isinstance(entry, dict) and entry.get("ip") == addr[0]:
                            config[key]["filename"]=os.path.dirname(parsed_path)[1:]+"/grub.cfg"

                            configini = configparser.ConfigParser(
                                allow_no_value=True,        # 允许空值
                                delimiters=('='),           # 分隔符
                                comment_prefixes=('#', ';') # 注释标识
                            )
                            config_file = "netboot"+"/"+os.path.dirname(parsed_path)[1:]+"/config.ini"
                            configini.read(config_file, encoding='utf-8')
                            isoname = configini.get('config', 'isoname')
                            config[key]["isoname"]=isoname
                            break
                    
                with open('config/leases.json', 'w') as file:
                    json.dump(config, file, indent=4)

            relative_path = parsed_path.lstrip('/')
            if not self.is_safe_path(relative_path):
                client.sendall(self.error_response(403, "Forbidden path").encode())
                return
            file_path = os.path.join(FILE_ROOT, relative_path)
            self.logger.info(f"{addr[0]} request file:{file_path}")
            file_ext = os.path.splitext(file_path)[1].lower()
            content_type = self.mime_types.get(file_ext, 'application/octet-stream')
            if not os.path.exists(file_path):
                client.sendall(self.error_response(404, "File not found").encode())
                return
            file_size = os.path.getsize(file_path)
            start, end = 0, file_size - 1
            
            if 'Range' in headers:
                try:
                    byte_range = headers['Range'].split('=')[1]
                    start_str, end_str = byte_range.split('-')
                    start = int(start_str) if start_str else 0
                    end = int(end_str) if end_str else file_size - 1
                    end = min(end, file_size - 1)
                except:
                    client.sendall(self.error_response(416, "Invalid range").encode())
                    return
            response_headers = [
                "HTTP/1.1 206 Partial Content" if 'Range' in headers else "HTTP/1.1 200 OK",
                f"Content-Type: {content_type}",
                f"Content-Length: {end - start + 1}",
                f"Accept-Ranges: bytes",
                f"Content-Range: bytes {start}-{end}/{file_size}",
                "\r\n"
            ]
            
            client.sendall("\r\n".join(response_headers).encode())
            
            with open(file_path, 'rb') as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk = f.read(min(CHUNK_SIZE, remaining))
                    if not chunk: break
                    try:
                        client.sendall(chunk)
                        remaining -= len(chunk)
                    except (ConnectionResetError, BrokenPipeError):
                        break
                        
        except Exception as e:
            self.logger.error(f"未知错误: {str(e)}")
            client.sendall(self.error_response(500, str(e)).encode())
    def parse_request(self, request):
        lines = request.split('\r\n')
        try:
            method, full_path, _ = lines[0].split()
        except ValueError:
            return {}, ''
            
        parsed = urlparse(full_path)
        headers = {
            'method': method,
            'path': parsed.path,
            'query': parsed.query 
        }
        
        for line in lines[1:]:
            if not line: break
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key] = value
                
        return headers, lines[-1]
    def error_response(self, code, message):
        return f"HTTP/1.1 {code}\r\nContent-Type: text/plain\r\n\r\n{message}"