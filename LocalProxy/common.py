#!-*-coding:utf-8-*-
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


def parse_header(data):
    '''
    :param data: client http request (whole)
    :return: destination address, port, data, support https or not
    '''
    data_list = data.split(CRLF+CRLF)
    dest_addr = None
    dest_port = 80
    if not data_list[0]:
        return None
    for line in data_list[0].split(CRLF):
        if len(line)>6 and b'Host: ' == line[:6]:
            host = line[6:]
            host_list = host.split(b':')
            dest_addr = host_list[0]
            if len(host_list)-1:
                try:
                    dest_port=int(host_list[1])
                except:
                    return None
            break
    line = data_list[0].split(CRLF)[0]

    https_support = True if (len(line) > 7 and line[0:7] == b'CONNECT') else False
    if (len(line)>=7 and line[0:7] != b'CONNECT') or len(line)<7:
        request_line_list = line.split(SPACE)
        if len(request_line_list) > 2:
            uri = to_str(request_line_list[1])
            if len(uri) < 6 or  (len(uri) >6 and 'http' != uri[0:4].lower() ):
                uri = 'http://'+to_str(dest_addr)+':'+str(dest_port)+uri
                request_line_list[1] = uri.encode()
                line_new = SPACE.join(request_line_list)
                data = data.replace(line,line_new)
    if dest_addr:
        return (to_str(dest_addr), int(dest_port), data, https_support)
    return None



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
    在这里，作者认为，IP被禁止后的表现有：
    1）socks 套接字都无法建立
    2）可以建立TCP连接，返回的页面是特定页面，如安全狗的
    3）返回特定的状态码或非200 的，其实策略3完全可以被策略2替代
    对应的识别策略
    1）客户端请求应为CONNECT，配置 forbidden_type 为 status_code，且 content 为 503
    （说实话，很多支持CONNECT的代理服务器在遇到目标端口不可用时的表现是超长时间的等待，
    或者不会返回503，等奇怪现象，所以在这种屏蔽策略下，使用大量IP，限制自己的访问频率最好）
    2）配置 forbidden_type 为 str （字符串) ，或是 regex （正则），在 content 中填写对应的内容
    3）配置 forbidden_type 为 status_code，content 填写被屏蔽时的状态码.
    搞了这么多看起来有用的东西，但由于从免费网站上抓取到的代理的可用性十分低，所以实际上没
    必要使用这些策略。最好的策略还是限制好自己的访问频率，然后通过本项目的本地代理服务器去
    访问目标站点。
    :param config:
    :param host:
    :param data:
    :return: boolean value ,distinguish type
    '''
    #host = self.r_dst_host
    #data = to_str(data)
    type = config['forbidden_type'].get(host)
    content = config['forbidden_content'].get(host)
    if not type or not content:
        return None , None
    status_code = get_status_code(data)

    if type=='str':
        return to_bytes(content) in data
    elif type == 'status_code':
        return str(status_code) in content.split(',')
    elif type =='regex':
        import re
        result = re.findall(content, data)
        return result is not None
    else:
        pass
    return None,None


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
