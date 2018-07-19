#/user/bin/python3
#-*-encoding:utf-8-*-
import re
import sys
try:
    from importlib import reload
except:
    reload(sys)
sys.path.append('..')
from Util.utilFunction import getHtmlTree
from Global import GLOBAL
from time import sleep
#import asyncio
import logging
'''
put result to GLOBAL.PRIORITY_QUEUE_2
{'proxy':''}
'''
class Methods(object):
    def __init__(self):
        pass

    @staticmethod
    def _method_test():
        sleep(1)
        print('method test')
        GLOBAL.PRIORITY_QUEUE_2.put({'proxy': '118.114.77.47:8080', 'type': 'confirm','from_db':False})

    @staticmethod
    def method_4(page_count=30):
        """
        西刺代理 http://www.xicidaili.com
        :return:
        """
        url_list = [
            'http://www.xicidaili.com/nn/',  # 高匿
            'http://www.xicidaili.com/nt/',  # 透明
        ]
        for each_url in url_list:
            for i in range(1, page_count + 1):
                page_url = each_url + str(i)
                tree = getHtmlTree(page_url)
                proxy_list = tree.xpath('.//table[@id="ip_list"]//tr[position()>1]')
                for proxy in proxy_list:
                    try:
                        proxy = ':'.join(proxy.xpath('./td/text()')[0:2])
                        GLOBAL.PRIORITY_QUEUE_2.put({'proxy':proxy,'type':'confirm'})
                        #print(GLOBAL.PRIORITY_QUEUE_2.get())
                        #print('in methods : %r'%GLOBAL.PRIORITY_QUEUE_2)
                        #print('-------------------------------')
                        #print({'proxy':proxy,'type':'confirm'})
                        #yield ':'.join(proxy.xpath('./td/text()')[0:2])
                    except Exception as e:
                        logging.warn('method error :%s--%s'%('method_4',e))
                        #pass
    @staticmethod
    def method_7(page_count=30):
        """
        快代理 https://www.kuaidaili.com
        """

        url_list = [
            'https://www.kuaidaili.com/free/inha/{page}/',
            'https://www.kuaidaili.com/free/intr/{page}/'
        ]
        try:
            for url in url_list:
                for page in range(1, page_count):
                    page_url = url.format(page=page)
                    tree = getHtmlTree(page_url)
                    proxy_list = tree.xpath('.//table//tr')
                    for tr in proxy_list[1:]:
                        #yield ':'.join(tr.xpath('./td/text()')[0:2])
                        GLOBAL.PRIORITY_QUEUE_2.put({'proxy': ':'.join(tr.xpath('./td/text()')[0:2]), 'type': 'confirm'})
        except Exception as e:
            logging.warn('method error :%s--%s' % ('method_7', e))

