# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File Name：     GetConfig.py  
   Description :  fetch config from config.ini
   Author :       JHao
   date：          2016/12/3
-------------------------------------------------
   Change Activity:
                   2016/12/3: get db property func
-------------------------------------------------
"""
__author__ = 'JHao'

import os
import sys
sys.path.append('..')
#from Util.utilClass import ConfigParse
from configparser import ConfigParser
from Util.utilClass import LazyProperty


class GetServerConfig(object):
    """
    to get config from config.ini
    """
    def __init__(self):
        #get absulte path
        self.pwd = os.path.split(os.path.realpath(__file__))[0]
        #setp into last directory
        self.config_path = os.path.join(os.path.join(os.path.split(self.pwd)[0],'Configuration'), 'ServerConfig.ini')
        self.config_file = ConfigParser()
        self.config_file.read(self.config_path)

    def get(self ,x , y):
        return self.config_file.get(x ,y)

    @LazyProperty
    def db_name(self):
        return self.config_file.get('DB', 'dbname')

    @LazyProperty
    def db_address(self):
        return self.config_file.get('DB', 'address')

    @LazyProperty
    def db_port(self):
        return int(self.config_file.get('DB', 'port'))

    @LazyProperty
    def collection(self):
        return self.config_file.get('DB', 'collection')

    @LazyProperty
    def db_proxies_getter_process_interval(self):
        return eval(self.config_file.get('ProxiesGetter', 'DBProxiesGetterProcessInterval'))

    @LazyProperty
    def row_proxies_getter_process_interval(self):
        return eval(self.config_file.get('ProxiesGetter','RowProxiesGetterProcessesInterval'))


class GetProConfig():
    def __init__(self):
        #get absulte path
        self.pwd = os.path.split(os.path.realpath(__file__))[0]
        #setp into last directory
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
            #print(section + '------')
            d[section] = {}
            for k in self.configParser[section].keys():
                d[section][k] = self.configParser[section].get(k)
                #d[section].append({k:self.configParser[section].get(k)})
                #print('{0}:{1}'.format(k, self.configParser[section].get(k)))
        return d




if __name__ == '__main__':
    gg = GetServerConfig()
    print(gg.db_name)
    print(gg.db_port)

    #print(eval(gg.get('ProxiesGetter','DBProxiesGetterProcessInterval')))

    c = GetProConfig()
    print(c.get_section2dict())
