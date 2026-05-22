'''

This file contains classes and functions that implement the TFTP service

'''

import socket
import struct
import os
import select
import time
import math
import json
from services import helpers

class ParentSocket(socket.socket):
    '''Subclassed socket.socket to enable a link-back to the client object.'''
    parent = None

class Client:
    '''Client instance for TFTPD.'''
    def __init__(self, mainsock, parent):
        self.default_retries = parent.default_retries
        self.timeout = parent.timeout
        self.ip = parent.ip
        self.message, self.address = mainsock.recvfrom(1024)
        self.logger = helpers.get_child_logger(parent.logger, 'Client.{0}'.format(self.address))
        self.netboot_directory = parent.netboot_directory
        self.logger.debug('Receiving request...')
        self.retries = self.default_retries
        self.block = 1
        self.blksize = 5120
        self.sent_time = float('inf')
        self.dead = False
        self.fh = None
        self.filename = ''
        self.wrap = 0
        self.arm_wrap = False
        self.handle() # message from the main socket

    def ready(self):
        '''Called when there is something to be read on our socket.'''
        self.message = self.sock.recv(1024)
        self.handle()

    def send_block(self):
        '''
            Sends the next block of data, setting the timeout and retry
            variables accordingly.
        '''
        data = None
        try:
            self.fh.seek(self.blksize * (self.block - 1))
            data = self.fh.read(self.blksize)
        except:
            self.logger.error('Error while reading block {0}'.format(self.block))
            self.dead = True
            return
        # opcode 3 == DATA, wraparound block number
        response = struct.pack('!HH', 3, self.block % 65536)
        response += data
        self.sock.sendto(response, self.address)
        self.logger.debug('Sending block {0}/{1}'.format(self.block, self.lastblock))
        self.retries -= 1
        self.sent_time = time.time()

    def no_ack(self):
        '''Determines if we timed out waiting for an ACK from the client.'''
        if self.sent_time + self.timeout < time.time():
            return True
        return False

    def no_retries(self):
        '''Determines if the client ran out of retry attempts.'''
        if not self.retries:
            return True
        return False

    def valid_mode(self):
        '''Determines if the file read mode octet; if not, send an error.'''
        mode = self.message.split(b'\x00')[1]
        if mode == b'octet': return True
        self.send_error(5, 'Mode {0} not supported'.format(mode))
        return False

    def check_file(self):
        '''
            Determines if the file exists under the netboot_directory,
            and if it is a file; if not, send an error.
        '''
        filename = self.message.split(b'\x00')[0].decode('ascii').lstrip('/')
        if "grub.cfg" in filename :
            try:
                with open('config/leases.json', 'r') as file:
                    config=json.load(file)
                    file.close()
                    mac=[key for key, entry in config.items() if entry.get("ip") == self.address[0]][0]
                    filename=config[mac]["filename"]
            except:
                pass
        try:
            filename = helpers.normalize_path(self.netboot_directory, filename)
        except helpers.PathTraversalException:
            self.send_error(2, 'Path traversal error', filename = filename)
            return False
        if os.path.isfile(filename):
            self.filename = filename
            return True
        self.send_error(1, 'File Not Found', filename = filename)
        return False

    def parse_options(self):
        '''
            Extracts the options sent from a client; if any, calculates the last
            block based on the filesize and blocksize.
        '''
        options = self.message.split(b'\x00')[2: -1]
        options = dict(zip((i.decode('ascii') for i in options[0::2]), map(int, options[1::2])))
        self.changed_blksize = 'blksize' in options
        if self.changed_blksize:
            self.blksize = options['blksize']
        #self.blksize=5120
        self.lastblock = math.ceil(self.filesize / float(self.blksize))
        self.tsize = True if 'tsize' in options else False
        if self.filesize > (2 ** 16) * self.blksize:
            self.logger.warning('Request too big, attempting transfer anyway.')
            self.logger.debug('Details: Filesize {0} is too big for blksize {1}.'.format(self.filesize, self.blksize))
        if len(options):
            # we need to know later if we actually had any options
            self.block = 0
            return True
        else:
            return False

    def reply_options(self):
        '''Acknowledges any options received.'''
        # only called if options, so send them all
        response = struct.pack("!H", 6)
        if self.changed_blksize:
            response += b'blksize' + b'\x00'
            response += str(self.blksize).encode('ascii') + b'\x00'
        if self.tsize:
            response += b'tsize' + b'\x00'
            response += str(self.filesize).encode('ascii') + b'\x00'
        self.sock.sendto(response, self.address)

    def new_request(self):
        '''
            When receiving a read request from the parent socket, open our
            own socket and check the read request; if we don't have any options,
            send the first block.
        '''
        self.sock = ParentSocket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.ip, 0))
        # used by select() to find ready clients
        self.sock.parent = self
        if not self.valid_mode() or not self.check_file():
            # some clients just ACK the error (wrong code?)
            # so forcefully shutdown
            self.complete()
            return
        self.fh = open(self.filename, 'rb')
        self.filesize = os.path.getsize(self.filename)
        self.logger.info('File {0} ({1} bytes) requested'.format(self.filename, self.filesize))
        if not self.parse_options():
            # no options received so start transfer
            if self.block == 1:
                self.send_block()
            return
        self.reply_options() # we received some options so ACK those first

    def send_error(self, code = 1, message = 'File Not Found', filename = ''):
        '''
            Sends an error code and string to a client. See RFC1350, page 10 for
            details.

            Value   Meaning
            =====   =======
            0       Not defined, see error message (if any).
            1       File not found.
            2       Access violation.
            3       Disk full or allocation exceeded.
            4       Illegal TFTP operation.
            5       Unknown transfer ID.
            6       File already exists.
            7       No such user.
        '''
        response =  struct.pack('!H', 5) # error opcode
        response += struct.pack('!H', code) # error code
        response += message.encode('ascii')
        response += b'\x00'
        self.sock.sendto(response, self.address)
        self.logger.debug('Sending {0}: {1} {2}'.format(code, message, filename))

    def complete(self):
        '''
            Closes a file and socket after sending it
            and marks ourselves as dead to be cleaned up.
        '''
        try:
            self.fh.close()
        except AttributeError:
            pass # we have not opened yet or file-not-found
        self.sock.close()
        self.dead = True

    def handle(self):
        '''Takes the message from the parent socket and act accordingly.'''
        # if addr not in ongoing, call this, else ready()
        [opcode] = struct.unpack('!H', self.message[:2])
        if opcode == 1:
            self.message = self.message[2:]
            self.new_request()
        elif opcode == 4:
            [block] = struct.unpack('!H', self.message[2:4])
            if block == 0 and self.arm_wrap:
                self.wrap += 1
                self.arm_wrap = False
            if block == 32768:
                self.arm_wrap = True
            if block < self.block % 65536:
                self.logger.warning('Ignoring duplicated ACK received for block {0}'.format(self.block))
            elif block > self.block % 65536:
                self.logger.warning('Ignoring out of sequence ACK received for block {0}'.format(self.block))
            elif block + self.wrap * 65536 == self.lastblock:
                if self.filesize % self.blksize == 0:
                    self.block = block + 1
                    self.send_block()
                self.logger.debug('Completed sending {0}'.format(self.filename))
                self.complete()
            else:
                self.block = block + 1
                self.retries = self.default_retries
                self.send_block()
        elif opcode == 2:
            # write request
            self.sock = ParentSocket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.ip, 0))
            # used by select() to find ready clients
            self.sock.parent = self
            # send error
            self.send_error(4, 'Write support not implemented')
            self.dead = True


class TFTPD:
    '''
        This class implements a read-only TFTP server
        implemented from RFC1350 and RFC2348
    '''
    def __init__(self, **server_settings):
        self.ip = server_settings.get('ip', '0.0.0.0')
        self.port = int(server_settings.get('port', 69))
        self.netboot_directory = server_settings.get('netboot_directory', '.')
        self.log_level = server_settings.get('log_level', False)
        self.logger = server_settings.get('logger', None)
        self.default_retries = server_settings.get('default_retries', 10)
        self.timeout = server_settings.get('timeout', 1)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", self.port))

        self.logger.debug('NOTICE: TFTP server started in debug mode. TFTP server is using the following:')
        self.logger.info('Server IP: {0}'.format(self.ip))
        self.logger.info('Server Port: {0}'.format(self.port))
        self.logger.info('Network Boot Directory: {0}'.format(self.netboot_directory))

        self.ongoing = []

    def listen(self,p_queue):
        '''This method listens for incoming requests.'''
        while True:
            # remove complete clients to select doesn't fail
            # Use a copy to iterate safely
            dead_clients = [client for client in self.ongoing if client.dead]
            for client in dead_clients:
                if client in self.ongoing:
                    self.ongoing.remove(client)
            
            # Only include clients with valid sockets
            valid_clients = []
            for client in self.ongoing:
                if not client.dead and hasattr(client, 'sock') and client.sock:
                    try:
                        # Check if socket is valid by getting its file descriptor
                        if hasattr(client.sock, 'fileno') and client.sock.fileno() >= 0:
                            valid_clients.append(client)
                        else:
                            # Socket is invalid, mark client as dead
                            client.dead = True
                    except:
                        # Socket operation failed, mark client as dead
                        client.dead = True
            
            try:
                rlist, _, _ = select.select([self.sock] + [client.sock for client in valid_clients], [], [], 1)
            except Exception as e:
                # If select fails, continue to next iteration
                continue
                
            for sock in rlist:
                if sock == self.sock:
                    # main socket, so new client
                    self.ongoing.append(Client(sock, self))
                else:
                    # client socket, so tell the client object it's ready
                    sock.parent.ready()
            # if we haven't received an ACK in timeout time, retry
            [client.send_block() for client in self.ongoing if client.no_ack()]
            # if we have run out of retries, kill the client
            for client in self.ongoing:
                if client.no_retries():
                    client.logger.error('Timeout while sending {0}'.format(client.filename))
                    client.complete()
