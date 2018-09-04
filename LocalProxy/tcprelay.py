#!-*-coding:utf-8-*-
import os
import time
import socket
import errno
import logging
import traceback
from LocalProxy import eventloop, common
from LocalProxy.common import parse_header

# we clear at most TIMEOUTS_CLEAN_SIZE timeouts each time
TIMEOUTS_CLEAN_SIZE = 512

MSG_FASTOPEN = 0x20000000

# SOCKS command definition
CMD_CONNECT = 1
CMD_BIND = 2
CMD_UDP_ASSOCIATE = 3

# for each opening port, we have a TCP Relay

# for each connection, we have a TCP Relay Handler to handle the connection

# for each handler, we have 2 sockets:
#    local:   connected to the client
#    remote:  connected to remote server

# for each handler, it could be at one of several stages:

# as sslocal:
# stage 0 SOCKS hello received from local, send hello to local
# stage 1 addr received from local, query DNS for remote
# stage 2 UDP assoc
# stage 3 DNS resolved, connect to remote
# stage 4 still connecting, more data from local received
# stage 5 remote connected, piping local and remote

# as ssserver:
# stage 0 just jump to stage 1
# stage 1 addr received from local, query DNS for remote
# stage 3 DNS resolved, connect to remote
# stage 4 still connecting, more data from local received
# stage 5 remote connected, piping local and remote

STAGE_INIT = 0
STAGE_ADDR = 1
STAGE_UDP_ASSOC = 2
STAGE_DNS = 3
STAGE_CONNECTING = 4
STAGE_STREAM = 5
STAGE_DESTROYED = -1

# for each handler, we have 2 stream directions:
#    upstream:    from client to server direction
#                 read local and write to remote
#    downstream:  from server to client direction
#                 read remote and write to local

STREAM_UP = 0
STREAM_DOWN = 1

# for each stream, it's waiting for reading, or writing, or both
WAIT_STATUS_INIT = 0
WAIT_STATUS_READING = 1
WAIT_STATUS_WRITING = 2
WAIT_STATUS_READWRITING = WAIT_STATUS_READING | WAIT_STATUS_WRITING

BUF_SIZE = 32 * 1024
from Global import GLOBAL
'''675
           TCPRelayHandler(self, self._fd_to_handlers,
                                self._eventloop, conn[0], self._config,
                                self._dns_resolver, self._is_local)
'''
class TCPRelayHandler(object):
    def __init__(self, server, fd_to_handlers, loop, local_sock, config,
                 dns_resolver, is_local):
        self._server = server
        self._fd_to_handlers = fd_to_handlers
        self._loop = loop
        self._local_sock = local_sock
        self._remote_sock = None
        self._config = config
        self._dns_resolver = dns_resolver
        self._is_local = is_local
        self._stage = STAGE_INIT
        self._fastopen_connected = False
        self._data_to_write_to_local = []
        self._data_to_write_to_remote = []
        self._upstream_status = WAIT_STATUS_READING
        self._downstream_status = WAIT_STATUS_INIT
        self._client_address = local_sock.getpeername()[:2]
        self._remote_address = None
        if 'forbidden_ip' in config:
            self._forbidden_iplist = config['forbidden_ip']
        else:
            self._forbidden_iplist = None

        fd_to_handlers[local_sock.fileno()] = self
        local_sock.setblocking(False)
        local_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        loop.add(local_sock, eventloop.POLL_IN | eventloop.POLL_ERR,
                 self._server)
        self.last_activity = 0
        self._update_activity()

        ##标记是否向客户端写回过数据
        self._data_send = False
        #以下变量 仅 测试使用
        self._ps = None
        self.print_peer_first = False

    def __hash__(self):
        # default __hash__ is id / 16
        # we want to eliminate collisions
        return id(self)

    @property
    def remote_address(self):
        return self._remote_address

    def _update_activity(self, data_len=0):
        # tell the TCP Relay we have activities recently
        # else it will think we are inactive and timed out
        self._server.update_activity(self, data_len)

    def _update_stream(self, stream, status):
        # update a stream to a new waiting status

        # check if status is changed
        # only update if dirty
        dirty = False
        if stream == STREAM_DOWN:
            if self._downstream_status != status:
                self._downstream_status = status
                dirty = True
        elif stream == STREAM_UP:
            if self._upstream_status != status:
                self._upstream_status = status
                dirty = True
        if dirty:

            if self._local_sock:
                event = eventloop.POLL_ERR
                if self._downstream_status & WAIT_STATUS_WRITING:
                    event |= eventloop.POLL_OUT
                if self._upstream_status & WAIT_STATUS_READING:
                    event |= eventloop.POLL_IN
                self._loop.modify(self._local_sock, event)

            if self._remote_sock:
                event = eventloop.POLL_ERR
                if self._downstream_status & WAIT_STATUS_READING:
                    event |= eventloop.POLL_IN
                if self._upstream_status & WAIT_STATUS_WRITING:
                    event |= eventloop.POLL_OUT
                self._loop.modify(self._remote_sock, event)

    def _write_to_sock(self, data, sock):
        # write data to sock
        # if only some of the data are written, put remaining in the buffer
        # and update the stream to wait for writing
        if not data or not sock:
            return False
        uncomplete = False
        try:
            l = len(data)
            s = sock.send(data)
            if s < l:
                data = data[s:]
                uncomplete = True
        except (OSError, IOError) as e:
            error_no = eventloop.errno_from_exception(e)
            if error_no in (errno.EAGAIN, errno.EINPROGRESS,
                            errno.EWOULDBLOCK):
                uncomplete = True
            else:
                if self._config['verbose']:
                    traceback.print_exc()
                self.destroy()
                return False
        if uncomplete:
            if sock == self._local_sock:
                self._data_to_write_to_local.append(data)
                self._update_stream(STREAM_DOWN, WAIT_STATUS_WRITING)
            elif sock == self._remote_sock:
                self._data_to_write_to_remote.append(data)
                self._update_stream(STREAM_UP, WAIT_STATUS_WRITING)
            else:
                logging.error('write_all_to_sock:unknown socket')
        else:
            if sock == self._local_sock:
                self._update_stream(STREAM_DOWN, WAIT_STATUS_READING)
            elif sock == self._remote_sock:
                self._update_stream(STREAM_UP, WAIT_STATUS_READING)
            else:
                logging.error('write_all_to_sock:unknown socket')
        return True

    def _handle_stage_connecting(self, data):
        self._data_to_write_to_remote.append(data)

    def _remove_proxy(self,proxy=None):
        '''
        移除host2dict对象中的指定代理(self._config['host2dict'][self.r_dst_host])
        :return: boolean
        '''

        if not proxy and self._remote_sock:
            try:
                add = self._remote_sock.getpeername()[0]
                port = self._remote_sock.getpeername()[1]
                proxy = '%s:%d'%(add,port)
            except:
                proxy = None
        if not proxy:
            #logging.debug('remove proxy error,no proxy')
            return
        if self._config.get('host2dict') and self.r_dst_host and self._config['host2dict'].get(self.r_dst_host):
            #foreach list object
            length = len(self._config['host2dict'][self.r_dst_host])
            for i in range(length):
                if self._config['host2dict'][self.r_dst_host][i]['proxy'] == proxy:
                    self._config['host2dict'][self.r_dst_host].remove(self._config['host2dict'][self.r_dst_host][i])
                    logging.info('remove proxy from memory:%r'%proxy)
                    return proxy
        return
#            remote_addr, remote_port = self._config['host2dict'][r_dst_host] \
#                [self._config['host2position'][r_dst_host]] \
#                    ['proxy'].split(':')

    def _handle_stage_addr(self, data):
        try:
            dest_data_tuple = parse_header(data)
            if dest_data_tuple is None:
                raise Exception('can not parse header')
            r_dst_host = '%s:%d' % (dest_data_tuple[0], dest_data_tuple[1]) \
                if self._config['recognize_host_type'] == 2 \
                else dest_data_tuple[0]
            self.r_dst_host = r_dst_host
            if self._config['black_host_enable']:
                for b in self._config.get('black_host_list') or []:
                    if b :
                        if dest_data_tuple[0].endswith(b):
                            logging.warning('black host : %s'%dest_data_tuple[0])
                            return
            data = dest_data_tuple[2]

            logging.info('connecting %s:%d from %s:%d' %
                         (str(dest_data_tuple[0]), int(dest_data_tuple[1]),
                          self._client_address[0], self._client_address[1]))


            if self._config['white_host_enable'] and r_dst_host not in self._config['white_host']:
                logging.warn('Reject the host:{}'.format(r_dst_host))
                raise common.RejectHostException
            if not self._config.get('host2dict'):
                self._config['host2dict'] = {}
                self._config['host2position'] = {}

            max = self._config['proxies_pool_max'].get(r_dst_host) or self._config['proxies_pool_max'].get('Global') or 30
            min = self._config['proxies_pool_min'].get(r_dst_host) or self._config['proxies_pool_min'].get('Global') or 10
            anonymous = self._config['anonymous']
            https_support = dest_data_tuple[3]
            score_available = self._config['GLOBAL'].GLOBAL_VARIABLE['SERVER_CONFIG'].score_available
            def _p(limit, anonymous=False):
                return self._config['db_connector'].get_all(
                    {'score': {'$gt': score_available}, 'anonymous': {'$in': [True, anonymous]}, 'https_support': {'$in': [True, https_support]},'host:%s'%self.r_dst_host:{'$exists':False}}, limit=limit)

            if not self._config['host2dict'].get(r_dst_host):
                #在本地代理服务器这进行数据库查询合适吗，有优化方案吗
                #想过用协程，但是好像搞不了..
                proxies = _p(max,anonymous)
                #测试使用
                #logging.info(proxies)
                self._config['host2dict'][r_dst_host] = proxies
                self._config['host2position'][r_dst_host] = 0

            #测试使用
            logging.info('[-]host:%s pool length:%d'%(r_dst_host,len(self._config['host2dict'][r_dst_host])))

            pool_length = len(self._config['host2dict'][r_dst_host])
            #如果池子代理数小于最低下限，则从数据库中补充到max
            if pool_length < min:
                diff = max - pool_length
                self._config['host2dict'][r_dst_host].extend(_p(diff,anonymous))

            pool_length = len(self._config['host2dict'][r_dst_host])
            #测试使用
            logging.info('[+]host:%s pool length:%d'%(r_dst_host,pool_length))

            if(pool_length)<1:
                logging.warn('[!] no proxy is avaiable!!!')
                self.destroy()
                return

            remote_addr, remote_port = self._config['host2dict'][r_dst_host] \
                [self._config['host2position'][r_dst_host]] \
                    ['proxy'].split(':')

            #测试使用
            #remote_addr, remote_port = '127.0.0.7',8899

            self._config['host2position'][r_dst_host] = (self._config['host2position'][r_dst_host]+1)%len(self._config['host2dict'][r_dst_host])
            self._remote_address = (common.to_str(remote_addr), int(remote_port))
            # pause reading
            self._update_stream(STREAM_UP, WAIT_STATUS_WRITING)
            self._stage = STAGE_DNS

            self._data_to_write_to_remote.append(data)
                # notice here may go into _handle_dns_resolved directly
            self._dns_resolver.resolve(remote_addr,
                                        self._handle_dns_resolved)
            #print('remote_addr :{}'.format(remote_addr))
        except Exception as e:
            self._log_error(e)
            #if self._config['verbose']:
            traceback.print_exc()
            self.destroy()

    def _create_remote_socket(self, ip, port):
        addrs = socket.getaddrinfo(ip, port, 0, socket.SOCK_STREAM,
                                   socket.SOL_TCP)
        if len(addrs) == 0:
            raise Exception("getaddrinfo failed for %s:%d" % (ip, port))
        af, socktype, proto, canonname, sa = addrs[0]
        if self._forbidden_iplist:
            if common.to_str(sa[0]) in self._forbidden_iplist:
                raise Exception('IP %s is in forbidden list, reject' %
                                common.to_str(sa[0]))
        remote_sock = socket.socket(af, socktype, proto)
        self._remote_sock = remote_sock
        self._fd_to_handlers[remote_sock.fileno()] = self
        remote_sock.setblocking(False)
        remote_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        return remote_sock

    def _handle_dns_resolved(self, result, error):
        if error:
            self._log_error(error)
            self.destroy()
            return
        if result:
            ip = result[1]
            if ip:

                try:
                    self._stage = STAGE_CONNECTING
                    remote_addr = ip
                    remote_port = self._remote_address[1]

                    remote_sock = self._create_remote_socket(remote_addr,
                                                             remote_port)
                    try:
                        remote_sock.connect((remote_addr, remote_port))
                    except (OSError, IOError) as e:
                        if eventloop.errno_from_exception(e) == \
                                errno.EINPROGRESS:
                            pass
                    self._loop.add(remote_sock,
                                   eventloop.POLL_ERR | eventloop.POLL_OUT,
                                   self._server)
                    self._stage = STAGE_CONNECTING
                    self._update_stream(STREAM_UP, WAIT_STATUS_READWRITING)
                    self._update_stream(STREAM_DOWN, WAIT_STATUS_READING)
                    return
                except Exception as e:
                    if self._config['verbose']:
                        traceback.print_exc()
        self.destroy()

    def _on_local_read(self):
        #
        #logging.info('_on_local_read')
        # handle all local read events and dispatch them to methods for
        # each stage
        if not self._local_sock:
            return
        is_local = self._is_local
        data = None
        try:
            data = self._local_sock.recv(BUF_SIZE)
        except (OSError, IOError) as e:
            if eventloop.errno_from_exception(e) in \
                    (errno.ETIMEDOUT, errno.EAGAIN, errno.EWOULDBLOCK):
                return
        if not data:
            self.destroy()
            return
        self._update_activity(len(data))
        if not data:
            return
        if self._stage == STAGE_STREAM:
            self._write_to_sock(data, self._remote_sock)
            return
        # elif is_local and self._stage == STAGE_INIT:
        #     # TODO check auth method
        #     self._write_to_sock(b'\x05\00', self._local_sock)
        #     self._stage = STAGE_ADDR
        #     return
        elif self._stage == STAGE_CONNECTING:
            self._handle_stage_connecting(data)
        elif not is_local and self._stage == STAGE_INIT:
            self._handle_stage_addr(data)

    def _on_remote_read(self):
        # handle all remote read events
        data = None
        try:
            data = self._remote_sock.recv(BUF_SIZE)

        except (OSError, IOError) as e:
            if eventloop.errno_from_exception(e) in \
                    (errno.ETIMEDOUT, errno.EAGAIN, errno.EWOULDBLOCK):
                return
        if not data:
            self.destroy()
            return
            forbidden, type = common.forbidden_or_not(self._config, self.r_dst_host, data)
        if forbidden:
            logging.info('Forbidden event -- proxy:{0}-- website:{1}'.format(
                self._remote_sock.getpeername(),
                self.r_dst_host))
            self.destroy(type='forbidden')
            return

        self._update_activity(len(data))
        try:
            self._write_to_sock(data, self._local_sock)
            self._data_send = True
        except Exception as e:
            if self._config['verbose']:
                traceback.print_exc()
            # TODO use logging when debug completed
            self.destroy()

    def _on_local_write(self):
        # handle local writable event
        #self._data_send = True
        #logging.info('on local write')
        if self._data_to_write_to_local:
            data = b''.join(self._data_to_write_to_local)
            self._data_to_write_to_local = []
            self._write_to_sock(data, self._local_sock)
        else:
            self._update_stream(STREAM_DOWN, WAIT_STATUS_READING)

    def _on_remote_write(self):
        #logging.info('_on_remote_write')
        # handle remote writable event
        self._stage = STAGE_STREAM
        if self._data_to_write_to_remote:
            data = b''.join(self._data_to_write_to_remote)
            self._data_to_write_to_remote = []
            self._write_to_sock(data, self._remote_sock)
        else:
            self._update_stream(STREAM_UP, WAIT_STATUS_READING)

    def _on_local_error(self):
        logging.debug('got local error')
        if self._local_sock:
            logging.error(eventloop.get_sock_error(self._local_sock))
        self.destroy()

    def _on_remote_error(self):
        logging.debug('got remote error')
        if self._remote_sock:
            logging.error(eventloop.get_sock_error(self._remote_sock))
        self.destroy(type='connection_reset')

    def handle_event(self, sock, event):
        # handle all events in this handler and dispatch them to methods
        if self._stage == STAGE_DESTROYED:
            logging.debug('ignore handle_event: destroyed')
            return
        # order is important

        if sock == self._remote_sock:
            #测试使用
            if not self.print_peer_first:
                logging.info('peername  %s:%d'%(sock.getpeername()[0],sock.getpeername()[1]))
                logging.info('pid:%d'%os.getpid())
                self.print_peer_first = True
            if event & eventloop.POLL_ERR:
                self._on_remote_error()
                if self._stage == STAGE_DESTROYED:
                    return
            if event & (eventloop.POLL_IN | eventloop.POLL_HUP):
                self._on_remote_read()
                if self._stage == STAGE_DESTROYED:
                    return
            if event & eventloop.POLL_OUT:
                self._on_remote_write()
        elif sock == self._local_sock:
            if event & eventloop.POLL_ERR:
                self._on_local_error()
                if self._stage == STAGE_DESTROYED:
                    return
            if event & (eventloop.POLL_IN | eventloop.POLL_HUP):
                self._on_local_read()
                if self._stage == STAGE_DESTROYED:
                    return
            if event & eventloop.POLL_OUT:
                self._on_local_write()
        else:
            logging.warn('unknown socket')

    def _log_error(self, e):
        logging.error('%s when handling connection from %s:%d' %
                      (e, self._client_address[0], self._client_address[1]))

    def destroy(self,type=None):
        # destroy the handler and release any resources
        if self._stage == STAGE_DESTROYED:
            # this couldn't happen
            logging.debug('already destroyed')
            return
        self._stage = STAGE_DESTROYED

        if type:
            try:
                proxy = self._remove_proxy()
                if type == 'forbidden':
                    self._config['GLOBAL'].PRIORITY_QUEUE_1.put(
                        {'type': type, 'proxy': proxy, 'host': self.r_dst_host, 'score': -1})
                else:
                    #connection_reset / timeout
                    if hasattr(self, 'r_dst_host'):
                        self._config['GLOBAL'].PRIORITY_QUEUE_1.put({'type': type, 'proxy': proxy,'host':self.r_dst_host,'score':-1})
                #.#测试使用
                if  self._data_send :
                    logging.info('[*] send partition data')
                else:
                    logging.info('[*] no data')
            except Exception as e:
                if self._config['verbose']:
                    traceback.print_exc()

        if self._remote_address:
            logging.debug('destroy: %s:%d' %
                          self._remote_address)
        else:
            logging.debug('destroy')
        if self._remote_sock:
            logging.debug('destroying remote')
            self._loop.remove(self._remote_sock)
            del self._fd_to_handlers[self._remote_sock.fileno()]
            self._remote_sock.close()
            self._remote_sock = None
        if self._local_sock:
            logging.debug('destroying local')
            self._loop.remove(self._local_sock)
            del self._fd_to_handlers[self._local_sock.fileno()]
            self._local_sock.close()
            self._local_sock = None
        self._dns_resolver.remove_callback(self._handle_dns_resolved)
        self._server.remove_handler(self)


class TCPRelay(object):
    def __init__(self, config, dns_resolver, is_local, stat_callback=None):
        self._config = config
        self._is_local = is_local
        self._dns_resolver = dns_resolver
        self._closed = False
        self._eventloop = None
        self._fd_to_handlers = {}

        self._timeout = config['timeout']
        self._timeouts = []  # a list for all the handlers
        # we trim the timeouts once a while
        self._timeout_offset = 0   # last checked position for timeout
        self._handler_to_timeouts = {}  # key: handler value: index in timeouts


        listen_addr = config['server']
        listen_port = config['server_port']
        self._listen_port = listen_port

        addrs = socket.getaddrinfo(listen_addr, listen_port, 0,
                                   socket.SOCK_STREAM, socket.SOL_TCP)
        if len(addrs) == 0:
            raise Exception("can't get addrinfo for %s:%d" %
                            (listen_addr, listen_port))
        af, socktype, proto, canonname, sa = addrs[0]
        server_socket = socket.socket(af, socktype, proto)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(sa)
        server_socket.setblocking(False)
        server_socket.listen(1024)
        self._server_socket = server_socket
        self._stat_callback = stat_callback

    def add_to_loop(self, loop):
        if self._eventloop:
            raise Exception('already add to loop')
        if self._closed:
            raise Exception('already closed')
        self._eventloop = loop
        self._eventloop.add(self._server_socket,
                            eventloop.POLL_IN | eventloop.POLL_ERR, self)
        self._eventloop.add_periodic(self.handle_periodic)

    def remove_handler(self, handler):
        index = self._handler_to_timeouts.get(hash(handler), -1)
        if index >= 0:
            # delete is O(n), so we just set it to None
            self._timeouts[index] = None
            del self._handler_to_timeouts[hash(handler)]

    def update_activity(self, handler, data_len):
        if data_len and self._stat_callback:
            self._stat_callback(self._listen_port, data_len)

        # set handler to active
        now = int(time.time())
        if now - handler.last_activity < eventloop.TIMEOUT_PRECISION:
            # thus we can lower timeout modification frequency
            return
        handler.last_activity = now
        index = self._handler_to_timeouts.get(hash(handler), -1)
        if index >= 0:
            # delete is O(n), so we just set it to None
            self._timeouts[index] = None
        length = len(self._timeouts)
        self._timeouts.append(handler)
        self._handler_to_timeouts[hash(handler)] = length

    def _sweep_timeout(self):
        # tornado's timeout memory management is more flexible than we need
        # we just need a sorted last_activity queue and it's faster than heapq
        # in fact we can do O(1) insertion/remove so we invent our own
        if self._timeouts:
            now = time.time()
            length = len(self._timeouts)
            pos = self._timeout_offset
            while pos < length:
                handler = self._timeouts[pos]
                if handler:
                    if now - handler.last_activity < self._timeout:
                        break
                    else:
                        if handler.remote_address:
                            logging.warn('timed out: %s:%d' %
                                         handler.remote_address)
                        else:
                            logging.warn('timed out')
                        handler.destroy(type='timeout')
                        self._timeouts[pos] = None  # free memory
                        pos += 1
                else:
                    pos += 1
            if pos > TIMEOUTS_CLEAN_SIZE and pos > length >> 1:
                # clean up the timeout queue when it gets larger than half
                # of the queue
                self._timeouts = self._timeouts[pos:]
                for key in self._handler_to_timeouts:
                    self._handler_to_timeouts[key] -= pos
                pos = 0
            self._timeout_offset = pos

    def handle_event(self, sock, fd, event):
        # handle events and dispatch to handlers

        # if sock:
        #     logging.log(shell.VERBOSE_LEVEL, 'fd %d %s', fd,
        #                 eventloop.EVENT_NAMES.get(event, event))
        if sock == self._server_socket:
            if event & eventloop.POLL_ERR:
                # TODO
                raise Exception('server_socket error')
            try:
                logging.debug('accept')
                conn = self._server_socket.accept()
                TCPRelayHandler(self, self._fd_to_handlers,
                                self._eventloop, conn[0], self._config,
                                self._dns_resolver, self._is_local)
            except (OSError, IOError) as e:
                error_no = eventloop.errno_from_exception(e)
                if error_no in (errno.EAGAIN, errno.EINPROGRESS,
                                errno.EWOULDBLOCK):
                    return
                else:
                    if self._config['verbose']:
                        traceback.print_exc()
        else:
            if sock:
                handler = self._fd_to_handlers.get(fd, None)
                if handler:
                    handler.handle_event(sock, event)
            else:
                logging.warn('poll removed fd')

    def handle_periodic(self):
        if self._closed:
            if self._server_socket:
                self._eventloop.remove(self._server_socket)
                self._server_socket.close()
                self._server_socket = None
                logging.info('closed TCP port %d', self._listen_port)
            if not self._fd_to_handlers:
                logging.info('stopping')
                self._eventloop.stop()
        self._sweep_timeout()

    def close(self, next_tick=False):
        logging.debug('TCP close')
        self._closed = True
        if not next_tick:
            if self._eventloop:
                self._eventloop.remove_periodic(self.handle_periodic)
                self._eventloop.remove(self._server_socket)
            self._server_socket.close()
            for handler in list(self._fd_to_handlers.values()):
                handler.destroy()
