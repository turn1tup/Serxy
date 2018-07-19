
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

from time import sleep
from Util.getConfig import GetServerConfig
#from Util.utilClass import PriorityQueue
from multiprocessing import Process
#from multiprocessing import Lock
#from queue import PriorityQueue
#from multiprocessing.managers import SyncManager
#from queue import Queue
#from multiprocessing import Queue
from ProxiesGetter.proxiesGetter import RowProxiesGetterProcesses
from ProxiesGetter.proxiesGetter import DBProxiesGetterProcess
#from threading import Thread
#from ProxiesGetter.proxiesGetter import Get
from ProxiesConfirmer.proxiesConfirmer import ConfirmerProcesses
from Global import GLOBAL
from LocalProxy.server import Server
from LocalProxy.waiter import Waiter
#import Global.GLOBAL
#from DataAccess.mongodb import MongodbConnector
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
    #p4 = Process(target=Waiter, name='Waiter')
    #ps.append(p4)
    p5 = Process(target=Server, name='Server')
    ps.append(p5)

    for p in ps:
        p.daemon=1
        p.start()

    for p in ps:
        p.join()



'''
    from Util.getConfig import GetProxiesGetterMethods
    config = GetProxiesGetterMethods()
    methods = config.proxies_getter_functions()
    print(methods)
    #print([k for k in parser.keys() if k !='DEFAULT' and k!='ConfigurationEnable'])
    from Util.getConfig import GetProConfig
    config = GetProConfig()
    parser = config.getConfigParse()
    print([k for k in parser.keys() if k !='DEFAULT' and k!='ConfigurationEnable'])

    from Util.getConfig import GetServerConfig
    
    from Util.getConfig import GetProConfig
    config = GetProConfig()
    #test = config.relive
    #print(test)
    
    print(config.relive().get('192.168.1.2'))
    #print(config.proxies_getter_functions)
    while True:
        try:
            sleep(2)
            print(config.relive().get('192.168.1.1'))
        except KeyboardInterrupt:
            break


    #print(config.proxies_getter_functions)
    for ProxiesGetter in config.proxies_getter_functions:

        iter_ = getattr(GetFreeProxies,ProxiesGetter)()
        for t in iter_:
            print(t)
        print(type(t))
    '''