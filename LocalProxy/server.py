#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 clowwindy
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
import sys
import os
import logging
import signal
from Global import GLOBAL
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))
from LocalProxy import shell, daemon, eventloop, tcprelay, asyncdns
from DataAccess.mongodb import MongodbConnector
from Util.getConfig import GetProConfig


def get_config():
    config = {}
    try:
        pro_config = GetProConfig().get_section2dict()

        def _f(v, default, callback_fuct=None):
            if callback_fuct:
                return {
                    k: callback_fuct(pro_config.get(k).get(v) or pro_config['Global'].get(v) or default) for
                    k in
                    pro_config.keys()}
            else:
                return {
                    k: (pro_config.get(k).get(v) or pro_config['Global'].get(v) or default) for
                    k in
                    pro_config.keys()}
        config['GLOBAL'] = GLOBAL
        config['verbose'] = True
        config['server_port'] = int(pro_config['Global']['server_port'])
        config['timeout'] = int(pro_config['Global']['timeout'])
        config['server'] = pro_config['Global']['server_addr']
        config['workers'] = int(pro_config['Global']['workers'])
        config['recognize_host_type'] = pro_config['Global']['recognize_host_type']
        config['white_host_enable'] = True if pro_config['Global']['white_host_enable'] == 'True' else False
        config['white_host'] = [str(k) for k in pro_config.keys()]
        config['anonymous'] = True if pro_config['Global']['anonymous'] == 'True' else False

        config['db_connector'] = MongodbConnector()
        config['proxies_pool_max'] = _f('proxies_pool_max', 10, eval)
        #print(config['proxies_pool_max'])
        config['proxies_pool_min'] = _f('proxies_pool_min', 3, eval)
        config['forbidden_handle_or_not'] = _f('forbidden_handle_or_not',False,None)
        config['forbidden_type'] = _f('forbidden_type','status_code',None)
        config['forbidden_content'] = _f('forbidden_content','not 200',None)
        #config['retrive_time'] = _f('retrive_time', '60*60*1', eval)
        config['host_to_unavaiable_count'] = {}
        return config
        #retrive_time
        # config['forbidden_handle_or_not'] = {
        #     k: (pro_config.get(k).get('forbidden_handle_or_not') or pro_config['Global'].get('forbidden_type') or False) for
        # k in
        #     pro_config.keys()}
        #
        # config['forbidden_type'] = {
        #     k: (pro_config.get(k).get('forbidden_type') or pro_config['Global'].get('forbidden_type') or 'status_code') for
        # k in
        #     pro_config.keys()}
        #
        # config['forbidden_content'] = {
        #     k: (pro_config.get(k).get('forbidden_content') or pro_config['Global'].get('forbidden_content') or 'not 200')
        # for k in
        #     pro_config.keys()}
        #
        # config['retrive_time'] = {
        #     k: eval(pro_config.get(k).get('retrive_time') or pro_config['Global'].get('retrive_time') or '60*60*1') for
        # k in
        #     pro_config.keys()}


    except Exception as e:
        logging.warn('local proxy server get config error : %r'%e)
        return
def Server():
    #shell.check_python()

    #config = shell.get_config(False)

    #daemon.daemon_exec(config)

    config = get_config()
    if not config:
        return
    tcp_servers = []

    dns_resolver = asyncdns.DNSResolver()

    logging.info("starting server at %s:%d" %
                    (config['server'], config['server_port']))
    tcp_servers.append(tcprelay.TCPRelay(config, dns_resolver, False))

    def run_server():
        def child_handler(signum, _):
            logging.warn('received SIGQUIT, doing graceful shutting down..')
            list(map(lambda s: s.close(next_tick=True),
                     tcp_servers ))
        signal.signal(getattr(signal, 'SIGQUIT', signal.SIGTERM),
                      child_handler)

        def int_handler(signum, _):
            sys.exit(1)
        signal.signal(signal.SIGINT, int_handler)

        try:
            loop = eventloop.EventLoop()
            dns_resolver.add_to_loop(loop)
            list(map(lambda s: s.add_to_loop(loop), tcp_servers ))

            daemon.set_user(config.get('user', None))
            loop.run()
        except Exception as e:
            shell.print_exception(e)
            sys.exit(1)

    if int(config['workers']) > 1:
        if os.name == 'posix':
            children = []
            is_child = False
            for i in range(0, int(config['workers'])):
                r = os.fork()
                if r == 0:
                    logging.info('worker started')
                    is_child = True
                    run_server()
                    break
                else:
                    children.append(r)
            if not is_child:
                def handler(signum, _):
                    for pid in children:
                        try:
                            os.kill(pid, signum)
                            os.waitpid(pid, 0)
                        except OSError:  # child may already exited
                            pass
                    sys.exit()
                signal.signal(signal.SIGTERM, handler)
                signal.signal(signal.SIGQUIT, handler)
                signal.signal(signal.SIGINT, handler)

                # master
                for a_tcp_server in tcp_servers:
                    a_tcp_server.close()

                dns_resolver.close()

                for child in children:
                    os.waitpid(child, 0)
        else:
            logging.warn('worker is only available on Unix/Linux')
            run_server()
    else:
        run_server()


if __name__ == '__main__':
    main()
