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
'''
    from Util.getConfig import GetProConfig
    config = GetProConfig()
    parser = config.getConfigParser()
    print([k for k in parser.keys() if k !='DEFAULT' and k!='ConfigurationEnable'])
'''


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
        #for k in d :
        #    for k2 in k:
                #print(k2)
    #def getConfigParser(self):
    #    return self.configParser




if __name__ == '__main__':
    gg = GetServerConfig()
    print(gg.db_name)
    print(gg.db_port)

    #print(eval(gg.get('ProxiesGetter','DBProxiesGetterProcessInterval')))

    c = GetProConfig()
    print(c.get_section2dict())
    #for i in c.relive_config().items():
    #    print(type(i))
        #for ii in c.relive_config().get(i):
        #    print(ii)
    #print(dir(c.relive_config()))
    #print
'''
    from Util.getConfig import GetProxiesGetterMethods
    config = GetProxiesGetterMethods()
    methods = config.proxies_getter_functions()
    print(methods)
'''
'''
['BOOLEAN_STATES', 'NONSPACECRE', 'OPTCRE', 'OPTCRE_NV', 'SECTCRE', '_DEFAULT_INTERPOLATION', '_MutableMapping__marker', '_OPT_NV_TMPL', '_OPT_TMPL', '_SECT_TMPL', '__abstractmethods__', '__class__', '__contains__', '__delattr__', '__delitem__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__gt__', '__hash__', '__init__', '__iter__', '__le__', '__len__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setitem__', '__sizeof__', '__slots__', '__str__', '__subclasshook__', '__weakref__', '_abc_cache', '_abc_negative_cache', '_abc_negative_cache_version', '_abc_registry', '_allow_no_value', '_comment_prefixes', '_convert_to_boolean', '_converters', '_defaults', '_delimiters', '_dict', '_empty_lines_in_values', '_get', '_get_conv', '_handle_error', '_inline_comment_prefixes', '_interpolation', '_join_multiline_values', '_optcre', '_proxies', '_read', '_sections', '_strict', '_unify_values', '_validate_value_types', '_write_section', 'add_section', 'clear', 'converters', 'default_section', 'defaults', 'get', 'getboolean', 'getfloat', 'getint', 'has_option', 'has_section', 'items', 'keys', 'options', 'optionxform', 'pop', 'popitem', 'read', 'read_dict', 'read_file', 'read_string', 'readfp', 'remove_option', 'remove_section', 'sections', 'set', 'setdefault', 'update', 'values', 'write']


class GetProxiesGetterMethods(object):
    def __init__(self):
        #get absulte path
        self.pwd = os.path.split(os.path.realpath(__file__))[0]
        self.config_path = os.path.join(os.path.join(os.path.split(self.pwd)[0],'Configuration'), 'ProxiesGetterMethods.ini')
        self.configParse = ConfigParse()
        self.mtime = os.path.getmtime(self.config_path)
        self.configParse.read(self.config_path)

    def proxies_getter_functions(self):
        if self.mtime!=os.path.getmtime(self.config_path):
            self.__init__()
        #print( abs(self.mtime-os.path.getmtime(self.config_path)) is True)
        #print(self.mtime-os.path.getmtime(self.config_path))
        #print(os.path.getmtime(self.config_path))
        return self.configParse.options('ProxiesGetterMethods')
    def getConfigParse(self):
        return self.configParse
'''