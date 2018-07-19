#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2015 clowwindy
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import, division, print_function, \
    with_statement

import socket
import struct
import logging


class RejectHostException(Exception):
    def __init__(self,err='Host has been rejected'):
        Exception.__init__(self,err)

def compat_ord(s):
    if type(s) == int:
        return s
    return _ord(s)


def compat_chr(d):
    if bytes == str:
        return _chr(d)
    return bytes([d])


_ord = ord
_chr = chr
ord = compat_ord
chr = compat_chr


def to_bytes(s):
    if bytes != str:
        if type(s) == str:
            return s.encode('utf-8')
    return s


def to_str(s):
    if bytes != str:
        if type(s) == bytes:
            return s.decode('utf-8')
    return s


def inet_ntop(family, ipstr):
    if family == socket.AF_INET:
        return to_bytes(socket.inet_ntoa(ipstr))
    elif family == socket.AF_INET6:
        import re
        v6addr = ':'.join(('%02X%02X' % (ord(i), ord(j))).lstrip('0')
                          for i, j in zip(ipstr[::2], ipstr[1::2]))
        v6addr = re.sub('::+', '::', v6addr, count=1)
        return to_bytes(v6addr)


def inet_pton(family, addr):
    addr = to_str(addr)
    if family == socket.AF_INET:
        return socket.inet_aton(addr)
    elif family == socket.AF_INET6:
        if '.' in addr:  # a v4 addr
            v4addr = addr[addr.rindex(':') + 1:]
            v4addr = socket.inet_aton(v4addr)
            v4addr = map(lambda x: ('%02X' % ord(x)), v4addr)
            v4addr.insert(2, ':')
            newaddr = addr[:addr.rindex(':') + 1] + ''.join(v4addr)
            return inet_pton(family, newaddr)
        dbyts = [0] * 8  # 8 groups
        grps = addr.split(':')
        for i, v in enumerate(grps):
            if v:
                dbyts[i] = int(v, 16)
            else:
                for j, w in enumerate(grps[::-1]):
                    if w:
                        dbyts[7 - j] = int(w, 16)
                    else:
                        break
                break
        return b''.join((chr(i // 256) + chr(i % 256)) for i in dbyts)
    else:
        raise RuntimeError("What family?")


def is_ip(address):
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            if type(address) != str:
                address = address.decode('utf8')
            inet_pton(family, address)
            return family
        except (TypeError, ValueError, OSError, IOError):
            pass
    return False


def patch_socket():
    if not hasattr(socket, 'inet_pton'):
        socket.inet_pton = inet_pton

    if not hasattr(socket, 'inet_ntop'):
        socket.inet_ntop = inet_ntop


patch_socket()


ADDRTYPE_IPV4 = 1
ADDRTYPE_IPV6 = 4
ADDRTYPE_HOST = 3


CRLF=b'\r\n'
SPACE = b'\x20'
#LF=b'\n'
def parse_header(data):
    #print(type(data))
    data_list = data.split(CRLF+CRLF)
    #addrtype = ADDRTYPE_IPV4
    dest_addr = None
    dest_port = 80
    #header_length = None
    if not data_list[0]:
        return None
    #headers=[]
    for line in data_list[0].split(CRLF):
        if len(line)>6 and b'Host: ' == line[:6]:
            #logging.info(line)
            host = line[6:]
            host_list = host.split(b':')
            dest_addr = host_list[0]
            #dest_port = 80
            if len(host_list)-1:
                try:
                    dest_port=int(host_list[1])
                except:
                    return None
            break
    line = data_list[0].split(CRLF)[0]
    if (len(line)>=7 and line[0:7] != b'CONNECT') or len(line)<7:
        request_line_list = line.split(SPACE)
        if len(request_line_list) > 2:
            uri = to_str(request_line_list[1])
            #print('uri : %s'%uri)
            if len(uri) < 6 or  (len(uri) >6 and 'http' != uri[0:4].lower() ):
                uri = 'http://'+to_str(dest_addr)+':'+str(dest_port)+uri
                #print('uri : %s' % uri)
                request_line_list[1] = uri.encode()
                line_new = SPACE.join(request_line_list)
                #print('line_new %r'%line_new)
                data = data.replace(line,line_new)
                #print(data)
    if dest_addr:
        return (to_str(dest_addr),int(dest_port),data)
    return None

def after_remote_sock_timeout(config,host,data):
    '''
    删除self中的该sock对象，通知queue_1
    :param config:
    :param host:
    :param data:
    :return:
    '''
    pass


def get_status_code(data):
    data = to_bytes(data)
    l1 = data.split(CRLF+CRLF)
    if len(l1)>0 and l1[0]:
        l2 = l1[0].split(CRLF)
        if len(l2)>0 and l2[0]:
            l3 = l2[0].split(SPACE)
            try:
                return int(l3[1])
            except:
                return None
    return None


def forbidden_or_not(config,host,data):
    '''
    判断当前使用的代理IP是否被禁止了，用户需要自定义目标站点禁止的方式，
    但是，仅仅依靠本函数是无法判别所有IP被禁止的情况的，还需要 tcprelay 的其他因素
    在这里，作者认为，IP被禁止后的表现有：
    1）socks 套接字都无法建立
    2）可以建立TCP连接，返回的页面是特定页面，如安全狗的，但状态码是200
    3）返回特定的状态码或非200 的
    这里先实现识别安全狗那种的，通过字符串即可
    :param config:
    :param host:
    :param data:
    :return: boolean value ,distinguish type
    '''
    #host = self.r_dest_host
    #data = to_str(data)
    type = config['forbidden_type'].get(host)
    content = config['forbidden_content'].get(host)
    if not type or not content:
        return None , None
    status_code = get_status_code(data)

    if type=='str':
        return to_bytes(content) in data, 'str'
    elif type == 'status_code':
        pass
    else:
        pass
    return None,None
    #if data=='remote_sock_error' or data=='no_data':
     #   #remote socks unavaiable
     #   pass

    #if status_code == 500 and type=='sock' and (not config['host_to_unavaiable_count'].get(host) or config['host_to_unavaiable_count'][host]<2):
        #
    #    pass
        # if type=='sock' and (not config['host_to_unavaiable_count'].get(host) or config['host_to_unavaiable_count'][host]<2):
        #     return True,'sock'
        # else:
        #     if not config['host_to_unavaiable_count'].get(host):
        #         config['host_to_unavaiable_count'][host] = 1
        #     else:
        #         config['host_to_unavaiable_count'][host] += 1
        #     return False,'sock'

    # if type == 'status_code':
    #     pass
    # elif type == 'str':
    #     return to_bytes(content) in data , 'str'
    # return False ,'finally'

class IPNetwork(object):
    ADDRLENGTH = {socket.AF_INET: 32, socket.AF_INET6: 128, False: 0}

    def __init__(self, addrs):
        self._network_list_v4 = []
        self._network_list_v6 = []
        if type(addrs) == str:
            addrs = addrs.split(',')
        list(map(self.add_network, addrs))

    def add_network(self, addr):
        if addr is "":
            return
        block = addr.split('/')
        addr_family = is_ip(block[0])
        addr_len = IPNetwork.ADDRLENGTH[addr_family]
        if addr_family is socket.AF_INET:
            ip, = struct.unpack("!I", socket.inet_aton(block[0]))
        elif addr_family is socket.AF_INET6:
            hi, lo = struct.unpack("!QQ", inet_pton(addr_family, block[0]))
            ip = (hi << 64) | lo
        else:
            raise Exception("Not a valid CIDR notation: %s" % addr)
        if len(block) is 1:
            prefix_size = 0
            while (ip & 1) == 0 and ip is not 0:
                ip >>= 1
                prefix_size += 1
            logging.warn("You did't specify CIDR routing prefix size for %s, "
                         "implicit treated as %s/%d" % (addr, addr, addr_len))
        elif block[1].isdigit() and int(block[1]) <= addr_len:
            prefix_size = addr_len - int(block[1])
            ip >>= prefix_size
        else:
            raise Exception("Not a valid CIDR notation: %s" % addr)
        if addr_family is socket.AF_INET:
            self._network_list_v4.append((ip, prefix_size))
        else:
            self._network_list_v6.append((ip, prefix_size))

    def __contains__(self, addr):
        addr_family = is_ip(addr)
        if addr_family is socket.AF_INET:
            ip, = struct.unpack("!I", socket.inet_aton(addr))
            return any(map(lambda n_ps: n_ps[0] == ip >> n_ps[1],
                           self._network_list_v4))
        elif addr_family is socket.AF_INET6:
            hi, lo = struct.unpack("!QQ", inet_pton(addr_family, addr))
            ip = (hi << 64) | lo
            return any(map(lambda n_ps: n_ps[0] == ip >> n_ps[1],
                           self._network_list_v6))
        else:
            return False

if __name__ == '__main__':
    str= b'''HTTP/1.1 304 Not Modified
Cache-Control: max-age=0, must-revalidate
Date: Tue, 17 Jul 2018 03:24:36 GMT
Etag: e16fcb8788a3c78955136c71e9dddd7c
Server: apache
Connection: close

'''
    print(get_status_code(str))

'''
def parse_header(data):
    #addrtype = ord(data[0])
    addrtype =ADDRTYPE_IPV4
    dest_addr = None
    dest_port = None
    header_length = 0
    print(data)
    if addrtype == ADDRTYPE_IPV4:
        if len(data) >= 7:
            dest_addr = socket.inet_ntoa(data[1:5])
            dest_port = struct.unpack('>H', data[5:7])[0]
            header_length = 7
        else:
            logging.warn('header is too short')
    elif addrtype == ADDRTYPE_HOST:
        if len(data) > 2:
            addrlen = ord(data[1])
            if len(data) >= 2 + addrlen:
                dest_addr = data[2:2 + addrlen]
                dest_port = struct.unpack('>H', data[2 + addrlen:4 +
                                                     addrlen])[0]
                header_length = 4 + addrlen
            else:
                logging.warn('header is too short')
        else:
            logging.warn('header is too short')
    elif addrtype == ADDRTYPE_IPV6:
        if len(data) >= 19:
            dest_addr = socket.inet_ntop(socket.AF_INET6, data[1:17])
            dest_port = struct.unpack('>H', data[17:19])[0]
            header_length = 19
        else:
            logging.warn('header is too short')
    else:
        logging.warn('unsupported addrtype %d, maybe wrong password or '
                     'encryption method' % addrtype)
    if dest_addr is None:
        return None
    return addrtype, to_bytes(dest_addr), dest_port, header_length


def pack_addr(address):
    address_str = to_str(address)
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            r = socket.inet_pton(family, address_str)
            if family == socket.AF_INET6:
                return b'\x04' + r
            else:
                return b'\x01' + r
        except (TypeError, ValueError, OSError, IOError):
            pass
    if len(address) > 255:
        address = address[:255]  # TODO
    return b'\x03' + chr(len(address)) + address
    





def test_inet_conv():
    ipv4 = b'8.8.4.4'
    b = inet_pton(socket.AF_INET, ipv4)
    assert inet_ntop(socket.AF_INET, b) == ipv4
    ipv6 = b'2404:6800:4005:805::1011'
    b = inet_pton(socket.AF_INET6, ipv6)
    assert inet_ntop(socket.AF_INET6, b) == ipv6


def test_parse_header():
    assert parse_header(b'\x03\x0ewww.google.com\x00\x50') == \
        (3, b'www.google.com', 80, 18)
    assert parse_header(b'\x01\x08\x08\x08\x08\x00\x35') == \
        (1, b'8.8.8.8', 53, 7)
    assert parse_header((b'\x04$\x04h\x00@\x05\x08\x05\x00\x00\x00\x00\x00'
                         b'\x00\x10\x11\x00\x50')) == \
        (4, b'2404:6800:4005:805::1011', 80, 19)


def test_pack_header():
    assert pack_addr(b'8.8.8.8') == b'\x01\x08\x08\x08\x08'
    assert pack_addr(b'2404:6800:4005:805::1011') == \
        b'\x04$\x04h\x00@\x05\x08\x05\x00\x00\x00\x00\x00\x00\x10\x11'
    assert pack_addr(b'www.google.com') == b'\x03\x0ewww.google.com'


def test_ip_network():
    ip_network = IPNetwork('127.0.0.0/24,::ff:1/112,::1,192.168.1.1,192.0.2.0')
    assert '127.0.0.1' in ip_network
    assert '127.0.1.1' not in ip_network
    assert ':ff:ffff' in ip_network
    assert '::ffff:1' not in ip_network
    assert '::1' in ip_network
    assert '::2' not in ip_network
    assert '192.168.1.1' in ip_network
    assert '192.168.1.2' not in ip_network
    assert '192.0.2.1' in ip_network
    assert '192.0.3.1' in ip_network  # 192.0.2.0 is treated as 192.0.2.0/23
    assert 'www.google.com' not in ip_network


if __name__ == '__main__':
    test_inet_conv()
    test_parse_header()
    test_pack_header()
    test_ip_network()
'''