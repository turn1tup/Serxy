import sys
import os
import logging
import signal
from Global import GLOBAL
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))
from LocalProxy import eventloop, tcprelay, asyncdns
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

        config['black_host_enable'] = _f('black_host_enable',False,None)['Global']
        config['black_host_list'] = _f('black_host_list',False,None)['Global'].split(',')

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

    except Exception as e:
        logging.warn('local proxy server get config error : %r'%e)
        return
def Server():


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

            #daemon.set_user(config.get('user', None))
            loop.run()
        except Exception as e:
            import traceback
            traceback.print_exc()
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
