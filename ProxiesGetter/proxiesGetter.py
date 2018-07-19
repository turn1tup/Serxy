#!/user/bin/python3
#!-*-coding:utf-8-*-
import re
import sys
import os
try:
    from importlib import reload
except:
    pass
sys.path.append('..')
#from Util.utilFunction import robustCrawl, getHtmlTree
#from Util.getConfig import GetProxiesGetterMethods
from ProxiesGetter.methods import Methods
from DataAccess.mongodb import MongodbConnector
from Global import GLOBAL
#import Global.GLOBAL
from time import sleep
from time import time
from threading import Thread
import logging
#import asyncio

def dbProxiesWorkout():
    '''
    仅当队列3中的，来自数据库的数据消耗光的前提前下，才能采集数据库中的代理数据来进行验证
    '''
    while GLOBAL.GLOBAL_VARIABLE['RUNNING']:
        GLOBAL.GLOBAL_VARIABLE['DB_PROXIES_WORKOUT'] = False if not GLOBAL.PRIORITY_QUEUE_3.empty() else True
        sleep(60)


class DBProxiesGetterProcess(object):
    def __init__(self,start_run=True):
        #while not GLOBAL.GLOBAL_VARIABLE['RUNNING']:
        #    sleep(5)
        self._mtime = time()
        self._interval = GLOBAL.GLOBAL_VARIABLE['SERVER_CONFIG'].db_proxies_getter_process_interval
        self._db_connector= MongodbConnector()
        start_run and self.run()


    def run(self):
        #延迟启动
        sleep(120)
        t = Thread(target=dbProxiesWorkout)
        t.daemon = True
        t.start()
        while True:
        #while GLOBAL.GLOBAL_VARIABLE['RUNNING']:
            # print(GLOBAL.GLOBAL_VARIABLE['DB_PROXIES_WORKOUT'])
            if not GLOBAL.GLOBAL_VARIABLE['DB_PROXIES_WORKOUT']:
                sleep(10)
                continue

            #print('test')
            #print([d for d in GLOBAL.DB_CONNECTOR_OBJECT.get_all({'anonymous':False})])
            # print('DBProxiesGetterProcess')
            #
            for dict_ in self._db_connector.get_all({}):
                dict_['from_db']=True
                GLOBAL.PRIORITY_QUEUE_3.put(dict_)
            GLOBAL.GLOBAL_VARIABLE['DB_PROXIES_WORKOUT'] = False

            itime = time() - self._mtime
            if itime<0:
                self._mtime = time()
                logging.warn('DBProxiesGetterProcess time error')
                continue
            interval = self._interval - itime
            if interval > 0:
                logging.info('DBProxiesGetterProcess need sleep times:{}'.format(interval))
                sleep(interval)
            self._mtime = time()

class RowProxiesGetterProcesses(object):
    def __init__(self,start_run=True):

        self.GLOBAL_VARIABLE = GLOBAL.GLOBAL_VARIABLE

        self._mtime = time()
        self._interval = GLOBAL.GLOBAL_VARIABLE['SERVER_CONFIG'].row_proxies_getter_process_interval
        self.method_list = [k for k in Methods.__dict__.keys() if k.startswith('method')]
        self.last_end_time = -1
        self.pwd = os.path.split(os.path.realpath(__file__))[0]
        self.methods_path = os.path.join(self.pwd,'methods.py')
        self.mtime = os.path.getmtime(self.methods_path)

        start_run and self.run()

    def run(self):
        #loop = asyncio.get_event_loop()
        while True:
        #while self.GLOBAL_VARIABLE['RUNNING']:

            try:

                for method in self.method_list:
                    getattr(Methods, method)()
                #tasks = [getattr(Methods,method)() for method in self.method_list]
                #loop.run_until_complete(asyncio.wait(tasks))
                #print('proxiesGetter end')
            except Exception as e:
                #print('proxiesGetter : %r'%e)
                logging.warn('RowProxiesGetterProcesses:%s'%e)

            itime = time() - self._mtime
            if itime < 0:
                self._mtime = time()
                logging.warn('RowProxiesGetterProcesses time error')
                continue
            interval = self._interval - itime
            if interval > 0 :

                logging.info('RowProxiesGetterProcesses need sleep times:{}'.format(interval))
                sleep(interval)
            self._mtime = time()


 #proxy_iter = [_ for _ in getattr(GetFreeProxy, proxyGetter.strip())()]