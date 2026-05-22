'''

This file contains classes and functions that implement the DHCP service

'''
import socket
import struct
import json
import os
from collections import defaultdict
from time import time
import time as time2

TYPE_53_DHCPDISCOVER = 1
TYPE_53_DHCPREQUEST =  3

def get_config_dir():
    system_config_dir = '/etc/kylin-system-tools/pxe'
    local_config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    
    if os.path.exists(system_config_dir) and os.access(system_config_dir, os.W_OK):
        return system_config_dir
    elif os.path.exists(local_config_dir) and os.access(local_config_dir, os.W_OK):
        return local_config_dir
    else:
        return system_config_dir

CONFIG_DIR = get_config_dir()

class OutOfLeasesError(Exception):
    pass

def process_dict(obj):
    if isinstance(obj, dict):
        return {key.hex() if isinstance(key, bytes) else key: process_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [process_dict(item) for item in obj]
    elif isinstance(obj, bytes):
        return obj.decode('utf-8')
    else:
        return obj

class DHCPD:
    '''
        This class implements a DHCP Server, limited to PXE options.
        Implemented from RFC2131, RFC2132,
        https://en.wikipedia.org/wiki/Dynamic_Host_Configuration_Protocol,
        and http://www.pix.net/software/pxeboot/archive/pxespec.pdf.
    '''
    def __init__(self, **server_settings):
        self.nic = server_settings.get('nic', '')
        self.ip = server_settings.get('ip', '192.168.2.2')
        self.port = int(server_settings.get('port', 67))
        self.offer_from = server_settings.get('offer_from', '192.168.2.100')
        self.offer_to = server_settings.get('offer_to', '192.168.2.150')
        self.subnet_mask = server_settings.get('subnet_mask', '255.255.255.0')
        self.router = server_settings.get('router', '192.168.2.1')
        self.dns_server = server_settings.get('dns_server', '8.8.8.8')

        self.broadcast = server_settings.get('broadcast', '')
        if not self.broadcast:
            # calculate the broadcast address from ip and subnet_mask
            nip = struct.unpack('!I', socket.inet_aton(self.ip))[0]
            nmask = struct.unpack('!I', socket.inet_aton(self.subnet_mask))[0]
            nbroadcast = (nip & nmask) | ((~ nmask) & 0xffffffff)
            derived_broadcast = socket.inet_ntoa(struct.pack('!I', nbroadcast))
            self.broadcast = derived_broadcast

        self.file_server = server_settings.get('file_server', '192.168.2.2')
        self.file_name = server_settings.get('file_name', '')
        if not self.file_name:
            self.force_file_name = False
            #self.file_name = 'pxelinux.0'
        else:
            self.force_file_name = True
        self.ipxe = server_settings.get('use_ipxe', False)
        self.http = server_settings.get('use_http', False)
        self.mode_proxy = server_settings.get('mode_proxy', False) # ProxyDHCP mode
        self.static_config = server_settings.get('static_config', dict())
        self.whitelist = server_settings.get('whitelist', [])
        self.blacklist = server_settings.get('blacklist', [])
        self.log_level = server_settings.get('log_level', False)
        self.logger = server_settings.get('logger', None)
        self.save_leases_file = server_settings.get('saveleases', '')
        self.magic = struct.pack('!I', 0x63825363) # magic cookie

        if self.http and not self.ipxe:
            self.logger.warning('HTTP selected but iPXE disabled. PXE ROM must support HTTP requests.')
        if self.ipxe and self.http:
            self.file_name = 'http://{0}/{1}'.format(self.file_server, self.file_name)
        if self.ipxe and not self.http:
            self.file_name = 'tftp://{0}/{1}'.format(self.file_server, self.file_name)

        self.logger.debug('NOTICE: DHCP server started in debug mode. DHCP server is using the following:')
        self.logger.info('DHCP Server IP: {0}'.format(self.ip))
        self.logger.info('DHCP Server Port: {0}'.format(self.port))

        # debug info for ProxyDHCP mode
        if not self.mode_proxy:
            self.logger.info('Lease Range: {0} - {1}'.format(self.offer_from, self.offer_to))
            self.logger.info('Subnet Mask: {0}'.format(self.subnet_mask))
            self.logger.info('Router: {0}'.format(self.router))
            self.logger.info('DNS Server: {0}'.format(self.dns_server))
            self.logger.info('Broadcast Address: {0}'.format(self.broadcast))

        if self.static_config:
            self.logger.info('Using Static Leasing')
            self.logger.info('Using Static Leasing Whitelist: {0}'.format(self.whitelist))

        self.logger.info('File Server IP: {0}'.format(self.file_server))
        self.logger.info('File Name: {0}'.format(self.file_name))
        self.logger.info('ProxyDHCP Mode: {0}'.format(self.mode_proxy))
        self.logger.info('Using iPXE: {0}'.format(self.ipxe))
        self.logger.info('Using HTTP Server: {0}'.format(self.http))
        self.logger.info('Bind Nic: {0}'.format(self.nic))

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, self.nic.encode())
        self.sock.bind(('', self.port ))

        # key is MAC
        # separate options dict so we don't have to clean up on export
        self.options = dict()
        self.leases = defaultdict(lambda: {'ip': '', 'expire': 0, 'ipxe': self.ipxe})
        leases_path = os.path.join(CONFIG_DIR, 'leases.json')
        with open(leases_path, 'w') as file:
            json.dump({}, file, indent=4)
        if self.save_leases_file:
            try:
                leases_file = open(self.save_leases_file, 'rb')
                imported = json.load(leases_file)
                import_safe = dict()
                for lease in imported:
                    packed_mac = struct.pack('BBBBBB', *map(lambda x:int(x, 16), lease.split(':')))
                    import_safe[packed_mac] = imported[lease]
                self.leases.update(import_safe)
                self.logger.info('Loaded leases from {0}'.format(self.save_leases_file))
            except IOError:
                pass
            except ValueError:
                pass

    def export_leases(self):
        if self.save_leases_file:
            export_safe = dict()
            for lease in self.leases:
                # translate the key to json safe (and human readable) mac
                export_safe[self.get_mac(lease)] = self.leases[lease]
            leases_file = open(self.save_leases_file, 'w')
            json.dump(export_safe, leases_file)
            self.logger.info('Exported leases to {0}'.format(self.save_leases_file))

    def get_namespaced_static(self, path, fallback = {}):
        statics = self.static_config
        for child in path.split('.'):
            statics = statics.get(child, {})
        return statics if statics else fallback

    def next_ip(self):
        '''
            This method returns the next unleased IP from range;
            also does lease expiry by overwrite.
        '''

        # if we use ints, we don't have to deal with octet overflow
        # or nested loops (up to 3 with 10/8); convert both to 32-bit integers

        # e.g '192.168.1.1' to 3232235777
        encode = lambda x: struct.unpack('!I', socket.inet_aton(x))[0]

        # e.g 3232235777 to '192.168.1.1'
        decode = lambda x: socket.inet_ntoa(struct.pack('!I', x))
        from_host = encode(self.offer_from)
        to_host = encode(self.offer_to)

        # pull out already leased IPs
        leased = [self.leases[i]['ip'] for i in self.leases
                if self.leases[i]['expire'] > time()]

        # convert to 32-bit int
        leased = map(encode, leased)

        # loop through, make sure not already leased and not in form X.Y.Z.0
        for offset in range(to_host - from_host):
            if (from_host + offset) % 256 and from_host + offset not in leased:
                return decode(from_host + offset)
        raise OutOfLeasesError('Ran out of IP addresses to lease!')

    def tlv_encode(self, tag, value):
        '''Encode a TLV option.'''
        if type(value) is str:
            value = value.encode('ascii')
        value = bytes(value)
        return struct.pack('BB', tag, len(value)) + value

    def tlv_parse(self, raw):
        '''Parse a string of TLV-encoded options.'''
        ret = {}
        while(raw):
            [tag] = struct.unpack('B', raw[0:1])
            if tag == 0: # padding
                raw = raw[1:]
                continue
            if tag == 255: # end marker
                break
            [length] = struct.unpack('B', raw[1:2])
            value = raw[2:2 + length]
            raw = raw[2 + length:]
            if tag in ret:
                ret[tag].append(value)
            else:
                ret[tag] = [value]
        return ret

    def get_mac(self, mac):
        '''
            This method converts the MAC Address from binary to
            human-readable format for logging.
        '''
        return ':'.join(map(lambda x: hex(x)[2:].zfill(2), struct.unpack('BBBBBB', mac))).upper()

    def craft_header(self, message):
        '''This method crafts the DHCP header using parts of the message.'''
        xid, flags, yiaddr, giaddr, chaddr = struct.unpack('!4x4s2x2s4x4s4x4s16s', message[:44])
        client_mac = chaddr[:6]

        # op, htype, hlen, hops, xid
        response =  struct.pack('!BBBB4s', 2, 1, 6, 0, xid)
        if not self.mode_proxy:
            response += struct.pack('!HHI', 0, 0, 0) # secs, flags, ciaddr
        else:
            response += struct.pack('!HHI', 0, 0x8000, 0)
        if not self.mode_proxy:
            if self.leases[client_mac]['ip'] and self.leases[client_mac]['expire'] > time(): # OFFER
                offer = self.leases[client_mac]['ip']
            else: # ACK
                offer = self.get_namespaced_static('dhcp.binding.{0}.ipaddr'.format(self.get_mac(client_mac)))
                offer = offer if offer else self.next_ip()
                self.leases[client_mac]['ip'] = offer
                self.leases[client_mac]['expire'] = time() + 86400
                self.logger.info('New Assignment - MAC: {0} -> IP: {1}'.format(self.get_mac(client_mac), self.leases[client_mac]['ip']))
            response += socket.inet_aton(offer) # yiaddr
        else:
            response += socket.inet_aton('0.0.0.0')
        response += socket.inet_aton(self.file_server) # siaddr
        response += socket.inet_aton('0.0.0.0') # giaddr
        response += chaddr # chaddr

        # BOOTP legacy pad
        response += b'\x00' * 64 # server name
        if self.mode_proxy:
            response += self.file_name.encode('ascii')
            response += b'\x00' * (128 - len(self.file_name))
        else:
            response += b'\x00' * 128
        response += self.magic # magic section
        return (client_mac, response)

    def craft_options(self, opt53, client_mac):
        '''
            This method crafts the DHCP option fields
            opt53:
                2 - DHCPOFFER
                5 - DHCPACK
            See RFC2132 9.6 for details.
        '''

        response = self.tlv_encode(53, struct.pack('!B', opt53)) # message type, OFFER
        response += self.tlv_encode(54, socket.inet_aton(self.ip)) # DHCP Server
        if not self.mode_proxy:
            subnet_mask = self.get_namespaced_static('dhcp.binding.{0}.subnet'.format(self.get_mac(client_mac)), self.subnet_mask)
            response += self.tlv_encode(1, socket.inet_aton(subnet_mask)) # subnet mask
            router = self.get_namespaced_static('dhcp.binding.{0}.router'.format(self.get_mac(client_mac)), self.router)
            response += self.tlv_encode(3, socket.inet_aton(router)) # router
            dns_server = self.get_namespaced_static('dhcp.binding.{0}.dns'.format(self.get_mac(client_mac)), [self.dns_server])
            dns_server = b''.join([socket.inet_aton(i) for i in dns_server])
            response += self.tlv_encode(6, dns_server)
            response += self.tlv_encode(51, struct.pack('!I', 86400)) # lease time

        # TFTP Server OR HTTP Server; if iPXE, need both
        response += self.tlv_encode(66, self.file_server)

        # file_name null terminated
        filename = self.get_namespaced_static('dhcp.binding.{0}.rom'.format(self.get_mac(client_mac)))
        
        if not filename:
            if not self.ipxe or not self.leases[client_mac]['ipxe']:
                #未启用ipxe或者非ipxe请求
                # http://www.syslinux.org/wiki/index.php/PXELINUX#UEFI
                if 'options' in self.leases[client_mac] and 93 in self.leases[client_mac]['options'] and not self.force_file_name:
                    [arch] = struct.unpack("!H", self.leases[client_mac]['options'][93][0])
                    filename = {0: 'pxelinux.0', # BIOS/default
                                6: 'syslinux.efi32', # EFI IA32
                                7: 'syslinux.efi64', # EFI BC, x86-64
                                9: 'syslinux.efi64'  # EFI x86-64
                                }[arch]
                else:
                    #第二次请求匹配包名
                    filename = self.file_name
            else:
                #PXE首次请求
                try:
                    [arch] = struct.unpack("!H", self.options[client_mac][93][0])
                except:
                    self.leases[client_mac]['ipxe'] = True
                    arch=0
                filename = {0: 'x86.kpxe',  # BIOS/default
                            6: 'syslinux.efi32',  # EFI IA32
                            7: 'ipxe_efi/x86_64.efi',  # EFI BC, x86-64
                            9: 'ipxe_efi/x86_64.efi',  # EFI x86-64
                            11: 'ipxe_efi/arm64.efi', #arm64
                            12: 'BOOTMIPS.EFI', #3a400
                            39: 'ipxe_efi/loongarch64.efi',#3a5000
                            40: 'ipxe_efi/loongarch64.efi'#3a5000 http
                            }[arch]
                if 77 in self.options[client_mac] and 'iPXE'.encode() in  self.options[client_mac][77]:
                    filename="autoexec.ipxe"
                if opt53 == 5 and not self.leases[client_mac]['new']: # ACK
                    self.leases[client_mac]['ipxe'] = False
        response += self.tlv_encode(67, filename.encode('ascii') + b'\x00')
        if self.mode_proxy:
            response += self.tlv_encode(60, 'PXEClient')
            response += struct.pack('!BBBBBBB4sB', 43, 10, 6, 1, 0b1000, 10, 4, b'\x00' + b'PXE', 0xff)
        response += b'\xff'
        return response

    def dhcp_offer(self, message):
        '''This method responds to DHCP discovery with offer.'''
        client_mac, header_response = self.craft_header(message)
        options_response = self.craft_options(2, client_mac) # DHCPOFFER
        response = header_response + options_response
        self.logger.debug('DHCPOFFER - Sending the following')
        self.logger.debug('<--BEGIN HEADER-->')
        self.logger.debug('{0}'.format(repr(header_response)))
        self.logger.debug('<--END HEADER-->')
        self.logger.debug('<--BEGIN OPTIONS-->')
        self.logger.debug('{0}'.format(repr(options_response)))
        self.logger.debug('<--END OPTIONS-->')
        self.logger.debug('<--BEGIN RESPONSE-->')
        self.logger.debug('{0}'.format(repr(response)))
        self.logger.debug('<--END RESPONSE-->')
        try:
            self.sock.sendto(response, (self.broadcast, 68))
        except:
            #解决终端网卡重启问题
            time2.sleep(5)
            self.sock.sendto(response, (self.broadcast, 68))



    def dhcp_ack(self, message):
        '''This method responds to DHCP request with acknowledge.'''
        client_mac, header_response = self.craft_header(message)
        options_response = self.craft_options(5, client_mac) # DHCPACK
        response = header_response + options_response
        self.logger.debug('DHCPACK - Sending the following')
        self.logger.debug('<--BEGIN HEADER-->')
        self.logger.debug('{0}'.format(repr(header_response)))
        self.logger.debug('<--END HEADER-->')
        self.logger.debug('<--BEGIN OPTIONS-->')
        self.logger.debug('{0}'.format(repr(options_response)))
        self.logger.debug('<--END OPTIONS-->')
        self.logger.debug('<--BEGIN RESPONSE-->')
        self.logger.debug('{0}'.format(repr(response)))
        self.logger.debug('<--END RESPONSE-->')
        with open('config/leases.json', 'r') as file:
            config=json.load(file)
        # 深度合并
        for key, value in process_dict(self.leases).items():
            if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                config[key].update(value)
            else:
                config[key] = value
        with open('config/leases.json', 'w') as file:
            json.dump(config, file, indent=4)
        try:
            self.sock.sendto(response, (self.broadcast, 68))
        except:
            #解决终端网卡重启问题
            time2.sleep(5)
            self.sock.sendto(response, (self.broadcast, 68))

    def validate_req(self, client_mac):
        client_mac_str = self.get_mac(client_mac)
        self.logger.debug('Received request from {0}'.format(client_mac_str))
        self.logger.debug('{0}'.format(repr(self.options[client_mac])))
        self.logger.debug('<--END OPTIONS-->')
        # 黑名单检查（优先级最高）
        if client_mac_str in self.blacklist:
            self.logger.info('Blacklisted client request rejected from {0}'.format(client_mac_str))
            return False
        # 白名单检查（非空时自动启用）
        if self.whitelist and client_mac_str not in self.whitelist:
            self.logger.info('Non-whitelisted client request rejected from {0}'.format(client_mac_str))
            return False
        #客户端重启
        if 60 in self.options[client_mac] and 'PXEClient'.encode() in self.options[client_mac][60][0] and 77 not in  self.options[client_mac]:
            self.logger.info('iPXE client request received from {0}'.format(self.get_mac(client_mac)))
            self.leases[client_mac]['ipxe'] = True
            self.leases[client_mac]['new'] = True
            return True
        if 60 in self.options[client_mac] and 'PXEClient'.encode() in self.options[client_mac][60][0]:
            self.logger.info('PXE client request received from {0}'.format(self.get_mac(client_mac)))
            self.leases[client_mac]['new'] = False
            return True

        #安装期间获取
        if client_mac in self.leases:
            self.logger.info('Non-PXE client request received from {0}'.format(self.get_mac(client_mac)))
            self.leases[client_mac]['new'] = True
            return True

        self.logger.info('Ignore Non-PXE client request from {0}'.format(self.get_mac(client_mac)))
        return False

    def listen(self,p_queue):
        '''Main listen loop.'''
        while True:
            message, address = self.sock.recvfrom(1024)
            [client_mac] = struct.unpack('!28x6s', message[:34])
            self.logger.debug('Received message')
            self.logger.debug('<--BEGIN MESSAGE-->')
            self.logger.debug('{0}'.format(repr(message)))
            self.logger.debug('<--END MESSAGE-->')
            self.options[client_mac] = self.tlv_parse(message[240:])
            self.logger.debug('Parsed received options')
            self.logger.debug('<--BEGIN OPTIONS-->')
            self.logger.debug('{0}'.format(repr(self.options[client_mac])))
            self.logger.debug('<--END OPTIONS-->')
            if not self.validate_req(client_mac):
                continue
            type = ord(self.options[client_mac][53][0]) # see RFC2131, page 10
            if type == TYPE_53_DHCPDISCOVER:
                self.logger.info('Sending DHCPOFFER to {0}'.format(self.get_mac(client_mac)))
                try:
                    self.dhcp_offer(message)
                except OutOfLeasesError:
                    self.logger.critical('Ran out of leases')
            elif type == TYPE_53_DHCPREQUEST:
                self.logger.info('Sending DHCPACK to {0}'.format(self.get_mac(client_mac)))
                self.dhcp_ack(message)
            else:
                self.logger.debug('Unhandled DHCP message type {0} from {1}'.format(type, self.get_mac(client_mac)))
