#from queue import PriorityQueue
#import logging as LOGGING # 引入logging模块
#LOGGING.basicConfig(level=LOGGING.DEBUG,format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
#from DataAccess.mongodb import MongodbConnector
#DB_CONNECTOR_OBJECT= MongodbConnector()
from multiprocessing import Manager, Value, Array

from Util.getConfig import GetServerConfig ,GetProConfig
from multiprocessing import Queue
manager = Manager()
GLOBAL_VARIABLE  = manager.dict({'RUNNING' : True
                                 , 'CONFIRMER_THREADS_NUM' : 10 , 'CONFIRM_TIMEOUT' : 10
                                 ,'DB_PROXIES_WORKOUT':False
                                 ,'SERVER_CONFIG':GetServerConfig()
                                 #,'HOST_TO_QUEUEDICT' : {}
                                 #,'PRO_CONFIG' : GetProConfig().get_section2dict()
                              })
#DB_CONNECTOR_OBJECT= MongodbConnector()

##HOST_TO_QUEUEDICT {'www.test.com':[using,used]}
HOST_TO_QUEUEDICT = manager.dict()

PRIORITY_QUEUE_1 = Queue()
PRIORITY_QUEUE_2 = Queue()
PRIORITY_QUEUE_3 = Queue()
#USING_QUEUE = Queue()
#USED_QUEUE = Queue()
#DB_BUSINESS_QUEUE=None
#CONFIRMER_THREADS_NUM=20