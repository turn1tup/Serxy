#!-*-coding:utf-8-*-
from multiprocessing import Manager
from Util.getConfig import GetServerConfig
from multiprocessing import Queue
manager = Manager()
GLOBAL_VARIABLE  = manager.dict({'RUNNING' : True
                                 , 'CONFIRMER_THREADS_NUM' : 10 , 'CONFIRM_TIMEOUT' : 10
                                 ,'DB_PROXIES_WORKOUT':False
                                 ,'SERVER_CONFIG':GetServerConfig()
                                 #,'HOST_TO_QUEUEDICT' : {}
                                 #,'PRO_CONFIG' : GetProConfig().get_section2dict()
                              })
PRIORITY_QUEUE_1 = Queue()
PRIORITY_QUEUE_2 = Queue()
PRIORITY_QUEUE_3 = Queue()
