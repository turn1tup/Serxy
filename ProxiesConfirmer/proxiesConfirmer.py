#-*-coding:utf-8-*-
from Global import GLOBAL
#import Global.GLOBAL
from queue import Empty as QueueEmpty
#from queue import Queue
#from multiprocessing import Queue
from threading import Thread
from multiprocessing import Process
from time import sleep
from time import time
from Util.utilFunction import proxy_is_avaiable
from Util.utilFunction import verifyProxyFormat
from DataAccess.mongodb import MongodbConnector
import logging
from base64 import b64encode
#logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class ConfirmerProcesses(object):
    '''
    处理3个队列中的事务
    PRIORITY_QUEUE_1 优先级最高，通常来自代理服务器的事务
    PRIORITY_QUEUE_2 中，最新爬取到的代理，需要验证
    PRIORITY_QUEUE_3 最低，通常来自数据库的代理，需要验证
    在保证优先级的前提下，又保证了不出现某一队列事务长期得不到处理的情况
    '''
    def __init__(self,start_run=True):
        self._db_connector = MongodbConnector()
        start_run and self.run()

    def run(self):
        threads =[]
        threads.append(Thread(target=remove_proxy))
        level_1_num = int(GLOBAL.GLOBAL_VARIABLE['CONFIRMER_THREADS_NUM']/2)
        level_2_num = int(GLOBAL.GLOBAL_VARIABLE['CONFIRMER_THREADS_NUM']/4)
        level_3_num = int(GLOBAL.GLOBAL_VARIABLE['CONFIRMER_THREADS_NUM'] - level_1_num - level_2_num)
        for i in range(level_1_num):
            #threads.append(Thread(target=confirm,args=(list_1,i)))
            threads.append(ConfirmThread([GLOBAL.PRIORITY_QUEUE_2,GLOBAL.PRIORITY_QUEUE_3,GLOBAL.PRIORITY_QUEUE_1] ,0 ,i+1))
        for i in range(level_2_num):
            #threads.append(Thread(target=confirm,args=(list_2,i*10)))
            threads.append(ConfirmThread([GLOBAL.PRIORITY_QUEUE_2,GLOBAL.PRIORITY_QUEUE_3,GLOBAL.PRIORITY_QUEUE_1] ,1 ,(i+1)*10))
        for i in range(level_3_num):
            #threads.append(Thread(target=confirm,args=(list_3,i*100)))
            threads.append(ConfirmThread([GLOBAL.PRIORITY_QUEUE_2,GLOBAL.PRIORITY_QUEUE_3,GLOBAL.PRIORITY_QUEUE_1] ,2 ,(i+1)*100))
        for t in threads:
            t.daemon = 1
            t.start()
        for t in threads:
            t.join()


def remove_proxy():
    '''
    定期删除长期不可用的代理
    :return:
    '''
    while True:
        GLOBAL.PRIORITY_QUEUE_2.put({'type':'remove_proxy','score':-5})
        sleep(300)


class ConfirmThread(Thread):
    def __init__(self ,list_ ,offset ,mark):
        Thread.__init__(self)
        self._db_connector = MongodbConnector()
        self.ring_shift_left(list_, offset)
        self.confirm_queue_list = list_
        #self.offset = offset
        self.mark = mark
        #self.
    def ring_shift_left(self ,list_ ,offset):
        for i in range(offset):
            list_.append(list_.pop(0))

    def run(self):
        while True:
        #while GLOBAL.GLOBAL_VARIABLE['RUNNING'] :
            food = None
            try:
                for q in self.confirm_queue_list:
                    food = q.get(timeout=0.1)
                    if food:
                        break

                if not food:
                    sleep(1)
                    continue
                #else:
                if type(food)!= dict or not food.get('type'):
                    logging.warn('bad food:%r'%food)
                    continue
                if food['type'] == 'confirm':
                    if not verifyProxyFormat(food['proxy']):
                        continue

                    #if not validUsefulProxy(food) :
                    #    continue
                    #如果代理不可用而且
                    #该代理数据是从数据库查询出来的就需要对其下降评分
                    #其实置为-1 也可以，下降分数对本项目没啥用..
                    if not proxy_is_avaiable(food) :
                        if food.get('from_db'):
                            self._db_connector.update({'proxy': food['proxy']},{'$inc': {'score':-1}})
                        continue
                    else:
                        food['score']=0
                        self._db_connector.put({'proxy': food['proxy']}, food)


                        logging.debug('[*]useful mark:{0} food: {1}'.format(self.mark,food))
                if food['type'] == 'timeout':
                    try:
                        score = int(food['score'])
                        self._db_connector.update({'proxy': food['proxy']}, {'$set': {'score': score}})
                        #测试使用
                        logging.info('set score successfully:%r'% food['proxy'])
                    except Exception as e:
                        logging.warn(e)
                if food['type'] == 'forbidden':
                    try:
                        host = 'host:'+b64encode(food['host'].encode()).decode()
                        proxy = food['proxy']
                        self._db_connector.update({'proxy':proxy},{'$set':{host:time()}})
                    except Exception as e:
                        logging.warn(e)

                if food['type'] == 'remove_proxy':
                    try:
                        score = food['score']
                        self._db_connector.remove({'score':{'$lt':score}})
                        logging.info('[*] Removed score lower than %r'%score)
                    except Exception as e:
                        logging.warn(e)

                if food['type'] == 'relive':
                    try:
                        proxy = food['proxy']
                        k = food['k']
                        v = food['v']
                        self._db_connector.update({'proxy':proxy},{'$unset':{k:""}})
                        logging.info('[*] Relive proxy %r'%proxy)
                    except Exception as e:
                        logging.warn(e)
            except QueueEmpty:
                pass

'''
def ring_shift_left(list_ ,offset):
    for i in range(offset):
        list_.append(list_.pop(0))


def confirm(confirm_queue_tuple,mark):
    while GLOBAL.GLOBAL_VARIABLE['RUNNING']:
        # print('thread run')
        food = None

        try:
            # print(food)
            if not confirm_queue_tuple[0].empty():
                food = confirm_queue_tuple[0].get_nowait()
            elif not confirm_queue_tuple[1].empty():
                food = confirm_queue_tuple[1].get_nowait()
            elif not confirm_queue_tuple[2].empty():
                food = confirm_queue_tuple[2].get_nowait()
            if not food:
                sleep(0.1)
                pass
                continue
            else:
                # print('321')
                print('mark:{0} food: {1}'.format(mark, food))
        except Exception as e:
            print(e)
'''