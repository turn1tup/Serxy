import os
import sys
sys.path.append('..')
from configparser import ConfigParser


class GetServerConfig(object):
    def __init__(self):
        #get absulte path
        self.pwd = os.path.split(os.path.realpath(__file__))[0]
        #setp into last directory
        self.config_path = os.path.join(os.path.join(os.path.split(self.pwd)[0],'Configuration'), 'ServerConfig.ini')
        self.config_file = ConfigParser()
        self.config_file.read(self.config_path)

    def get(self ,x , y):
        return self.config_file.get(x ,y)

    @property
    def db_name(self):
        return self.config_file.get('DB', 'dbname')

    @property
    def db_address(self):
        return self.config_file.get('DB', 'address')

    @property
    def db_port(self):
        return int(self.config_file.get('DB', 'port'))

    @property
    def collection(self):
        return self.config_file.get('DB', 'collection')

    @property
    def db_proxies_getter_process_interval(self):
        return eval(self.config_file.get('ProxiesGetter', 'DBProxiesGetterProcessInterval'))

    @property
    def row_proxies_getter_process_interval(self):
        return eval(self.config_file.get('ProxiesGetter','RowProxiesGetterProcessesInterval'))

    @property
    def record_server(self):
        return eval(self.config_file.get('ProxiesGetter','RecordServer'))


class GetProConfig():
    def __init__(self):
        self.pwd = os.path.split(os.path.realpath(__file__))[0]
        self.config_path = os.path.join(os.path.join(os.path.split(self.pwd)[0],'Configuration'), 'ProConfig.ini')
        self.mtime=os.path.getmtime(self.config_path)
        self.configParser = ConfigParser()
        self.configParser.read(self.config_path)

    def relive_config(self):
        if self.mtime!=os.path.getmtime(self.config_path):
            self.__init__()
        return self.configParser

    def get_section2dict(self):
        d = {}
        for section in self.configParser:
            d[section] = {}
            for k in self.configParser[section].keys():
                d[section][k] = self.configParser[section].get(k)
        return d
