from Global import GLOBAL
from time import sleep
#from multiprocessing import Queue
#from queue import Emp
from queue import Empty as QueueEmpty
class Get(object):
    def __init__(self):
        pass
        #self.run()

    def run(self):
        while GLOBAL.GLOBAL_VARIABLE['RUNNING']:
            #if GLOBAL.PRIORITY_QUEUE and not GLOBAL.PRIORITY_QUEUE.empty():
            #    print('[*]GET : {0}',GLOBAL.PRIORITY_QUEUE.get())
            #sleep(1)
           try:
            if not GLOBAL.PRIORITY_QUEUE_1.empty():
                food = GLOBAL.PRIORITY_QUEUE_1.get_nowait()
            elif not GLOBAL.PRIORITY_QUEUE_2.empty():
                food = GLOBAL.PRIORITY_QUEUE_2.get_nowait()
            else:
                food = GLOBAL.PRIORITY_QUEUE_3.get_nowait()
           except QueueEmpty:
               pass
           else:
               print(food)
                #print(GLOBAL.PRIORITY_QUEUE)