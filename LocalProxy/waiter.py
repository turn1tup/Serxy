from Global import GLOBAL
from DataAccess.mongodb import MongodbConnector
import logging
#from multiprocessing import Queue
from multiprocessing import Manager

class Waiter(object):
    def __init__(self):
        self._g = GLOBAL.GLOBAL_VARIABLE
        #self._using_q = GLOBAL.USING_QUEUE
        #self._used_q = GLOBAL.USED_QUEUE
        self._db_connector = MongodbConnector()
        self._limit = 50
        self.run()

    def run(self):
        while self._g['RUNNING']:
            qd = GLOBAL.HOST_TO_QUEUEDICT
            #print('waiter start')
            for k in qd.keys():
                #print('k:{0},v{1}:'.fromat(k,qd.get))
                if qd.get(k) == 'WAITTING':
                    logging.warn('{0} proxy queue was None'.format(k))
                    #using_q = Manager().Queue()
                    #used_q = Manager().Queue()
                    proxies = self._db_connector.get_all({'score':{'$gt':-1}} ,limit=self._limit)

                    #for p in proxies:
                    #    using_q.put(p)
                        # using , used
                    GLOBAL.HOST_TO_QUEUEDICT[k] = [proxies,{}]
                    logging.info('{0} has been provided {1}'.format(k, len(proxies)))

                    exit()
