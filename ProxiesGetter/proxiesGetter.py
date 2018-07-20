#!/user/bin/python3
#!-*-coding:utf-8-*-
import re
import sys
import os
sys.path.append('..')
from ProxiesGetter.methods import Methods
from DataAccess.mongodb import MongodbConnector
from Global import GLOBAL
from time import sleep
from time import time
from threading import Thread
import logging
from Util.getConfig import GetProConfig
from base64 import b64decode

def dbProxiesWorkout():
    '''
    仅当队列3中的，来自数据库的数据消耗光的前提前下，才能采集数据库中的代理数据来进行验证
    '''
    while GLOBAL.GLOBAL_VARIABLE['RUNNING']:
        GLOBAL.GLOBAL_VARIABLE['DB_PROXIES_WORKOUT'] = False if not GLOBAL.PRIORITY_QUEUE_3.empty() else True
        sleep(60)


class DBProxiesGetterProcess(object):
    def __init__(self,start_run=True):
        self._mtime = time()
        self._interval = GLOBAL.GLOBAL_VARIABLE['SERVER_CONFIG'].db_proxies_getter_process_interval
        self._db_connector= MongodbConnector()

        pro_config = GetProConfig().get_section2dict()
        #self._pro_config_keys = pro_config.keys()
        self._relive_time = {
        k: eval(pro_config.get(k).get('relive_time') or pro_config['Global'].get('relive_time') or '60*60*1') for k in
        pro_config.keys()}
        self._retrlive_host = self._relive_time.keys()
        #logging.info(self._relive_time)
        start_run and self.run()
    def run(self):
        #延迟启动
        sleep(30)

        t = Thread(target=dbProxiesWorkout)
        t.daemon = True
        t.start()
        while True:
            if not GLOBAL.GLOBAL_VARIABLE['DB_PROXIES_WORKOUT']:
                sleep(10)
                continue

            for dict_ in self._db_connector.get_all({}):
                for k,v in dict_.items():
                    # 如果该代理存在被禁止的host，则获取其retrive time 复活时间，如果时间到了则让其复活
                    if k.startswith('host:') and b64decode(k[5:]).decode() in self._retrlive_host:
                        #测试使用
                        #host = b64decode(k[5:])
                        #logging.info('k:v - %r:%r'%(k,v))
                        relive_time = self._relive_time[b64decode(k[5:]).decode()]
                        #logging.info(relive_time)
                        if time() - v >= relive_time:
                            GLOBAL.PRIORITY_QUEUE_2.put({'type':'relive','proxy':dict_['proxy'],'k':k,'v':v})
                            logging.info({'type':'relive','proxy':dict_['proxy'],'k':k,'v':v})
                            break
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

        while True:
        #while self.GLOBAL_VARIABLE['RUNNING']:
            try:

                for method in self.method_list:
                    getattr(Methods, method)()
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