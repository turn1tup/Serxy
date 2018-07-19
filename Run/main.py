
# !/usr/bin/env python
#-*-encoding:utf-8-*-
#部署时候，一定要记得mongodb的匿名访问问题
import sys
'''
try:
    from importlib import reload
    reload(sys)
except:
    reload(sys)
    '''
sys.path.append('..')

from multiprocessing import Process
from ProxiesGetter.proxiesGetter import RowProxiesGetterProcesses
from ProxiesGetter.proxiesGetter import DBProxiesGetterProcess
from ProxiesConfirmer.proxiesConfirmer import ConfirmerProcesses
from LocalProxy.server import Server

import logging
logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S'
        )
if __name__ == '__main__':

    ps = []
    p1 = Process(target=RowProxiesGetterProcesses,name='GetterProcesses')
    ps.append(p1)
    p2 = Process(target=DBProxiesGetterProcess, name='DBProxiesGetterProcess')
    ps.append(p2)
    p3 = Process(target=ConfirmerProcesses,name='ConfirmerProcesses')
    ps.append(p3)
    p5 = Process(target=Server, name='Server')
    ps.append(p5)

    for p in ps:
        p.daemon=1
        p.start()

    for p in ps:
        p.join()

