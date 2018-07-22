#!-*-encoding:utf-8-*-
from pymongo import MongoClient
from Global import GLOBAL
#from multiprocessing import Lock
class MongodbConnector(object):
    #lock = Lock()

    def __init__(self):
        self.dbname  = GLOBAL.GLOBAL_VARIABLE['SERVER_CONFIG'].db_name
        self.connector = MongoClient(GLOBAL.GLOBAL_VARIABLE['SERVER_CONFIG'].db_address,GLOBAL.GLOBAL_VARIABLE['SERVER_CONFIG'].db_port,connect=False)
        self.database = self.connector[self.dbname]
        self.collection = GLOBAL.GLOBAL_VARIABLE['SERVER_CONFIG'].collection
        self
    #def collection(self,collection):
    #    self.collection=collection
    def remove(self, find_dict ,collection=None ):
        collection = self.collection if collection is None else collection
        return self.database[collection].remove(find_dict)

    def get_all(self, find_dict,collection=None,limit=0):
        #with self.lock:
        collection = self.collection if collection is None else collection
        return [item for item in self.database[collection].find(find_dict).limit(limit)]

    def get_one(self, find_dict,collection=None):
        #with self.lock:
        collection = self.collection if collection is None else collection
        return self.database[collection].find_one(find_dict)

    def put(self, find_dict ,put_dict ,collection=None ,is_set=True):
        #with self.lock:
        collection = self.collection if collection is None else collection
        if not self.database[collection].find_one(find_dict):
            return self.database[collection].insert(put_dict)
        elif is_set:
            return self.database[collection].update(find_dict,{'$set':put_dict})

    def update(self, find_dict ,update_dict ,collection=None):

        #with self.lock:
        collection = self.collection if collection is None else collection
        return self.database[collection].update(find_dict,update_dict)

    def clone_collecion(self):
        pass
        ##client.db.proxy_test3.insert(client.db.proxy_test.find())

class MongodbClient(object):
    def __init__(self ,host ,port ,dbname='proxy' ,collection='proxy_test'):
        self.collecion = collection
        self.client = MongoClient(host, port)
        self.db = self.client[dbname]


    def changeCollection(self, collecion):
        self.collecion = collecion

    def get(self, proxy):
        data = self.db[self.collecion].find_one({'proxy': proxy})
        return data['num'] if data != None else None

    def put(self, proxy, num=1):
        if self.db[self.collecion].find_one({'proxy': proxy}):
            return None
        else:
            self.db[self.collecion].insert({'proxy': proxy, 'num': num})

    def pop(self):
        data = list(self.db[self.collecion].aggregate([{'$sample': {'size': 1}}]))
        if data:
            data = data[0]
            value = data['proxy']
            self.delete(value)
            return {'proxy': value, 'value': data['num']}
        return None

    def delete(self, value):
        self.db[self.collecion].remove({'proxy': value})

    def getAll(self):
        return {p['proxy']: p['num'] for p in self.db[self.collecion].find()}

    def clean(self):
        self.client.drop_database('proxy')

    def delete_all(self):
        self.db[self.collecion].remove()

    def update(self, proxy, num):
        self.db[self.collecion].update({'proxy': proxy}, {'$set': {'num': num}})
        #self.db[self.collecion].update({'proxy': proxy}, {'$inc': {'num': num}})

    def exists(self, key):
        return True if self.db[self.collecion].find_one({'proxy': key}) != None else False

    def getNumber(self):
        return self.db[self.collecion].count()

    def cloneCollection(self,target_collection):
        try:
            collection_data = self.db[self.collecion].find()
            self.db[target_collection].insert(collection_data)
            return True
        except:
            return False
    def dropCollection(self,target_collection):
        try:
            self.db[target_collection].drop()
            return True
        except:
            return False

if __name__ == "__main__":


    client = MongodbClient( '127.0.0.1', 27017,dbname='proxy',collection='common_proxy')
    client.db.common_proxy.insert( {
                        'proxy': '192.168.1.1',
                        'forbidden': {
                            'www.test.com': {
                                'retrive_time': 3600,
                                'mtime': 1531921592.237
                            },
                            'www.test22.com': {
                                'retrive_time': 7200,
                                'mtime': 1531922592.111
                            }
                        }
                    })
    # client.db.common_proxy.update({'proxy':'101.236.35.98:8866'},
    #                               {'$set':{'forbidden': {
    #                                             'www.test.com': { 'retrive_time': 3600,'mtime': 1531921592.237}
    #                                         }
    #                               }
    #                               })


    #client.db.proxy_test.find()
    #client.db.proxy_test3.insert(client.db.proxy_test.find())
    #client.db.proxy_test.map_reduce(mapper,reducer,out)
    #client.db.proxy_test.find().forEach(function(x){db.proxy_test3.insert(x)})
    #for i in client.db['proxy_test'].find():
     #   print(i)
    # db.put('127.0.0.1:1')
    # db2 = MongodbClient('second', 'localhost', 27017)
    # db2.put('127.0.0.1:2')
    #print(db.pop())
'''


class ConnectorProcesses(object):
    def __init__(self,address='127.0.0.1', port=27017, dbname='proxy', collection_name='common_proxy',start_run=True):
        self.connector = MongodbConnector(address, port, dbname, collection_name,)
        self.queue = GLOBAL.DB_BUSINESS_QUEUE
        start_run and self.run()

    def run(self):
        while GLOBAL.GLOBAL_VARIABLE['RUNNING']:
            try:
                food = self.queue.get()
                self.connector.collection_name = food.get('collection') if food.get('collection') is not None else self.connector.collection_name
                if food['operation'] == 'put':
                    self.connector.put(food['find_dict'],food['put_dict'])
                elif food['operation'] == 'update':
                    self.connector.update(food['find_dict'],food['update_dict'])
            except KeyError:
                pass
            except Exception as e:
                #GLOBAL.LOGGING.debug(e)
                print(e)
    def get(self,find_dict):
        self.connector.get(find_dict)
    def remove_unuse_kv(self,dict_):
        unse_keys = ['']
        for k in dict_:
            if k in unse_keys:
                dict_.remove(k)
    #def set_connector(self):
    #    self.connector
'''