# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
-------------------------------------------------
   File Name：     utilFunction.py
   Description :  tool function
   Author :       JHao
   date：          2016/11/25
-------------------------------------------------
   Change Activity:
                   2016/11/25: 添加robustCrawl、verifyProxy、getHtmlTree
-------------------------------------------------
"""
import requests
import time
from lxml import etree
from Global import GLOBAL
from Util.LogHandler import LogHandler
from Util.WebRequest import WebRequest
import json
# logger = LogHandler(__name__, stream=False)


# noinspection PyPep8Naming
def robustCrawl(func):
    def decorate(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            pass
            # logger.info(u"sorry, 抓取出错。错误原因:")
            # logger.info(e)

    return decorate





# noinspection PyPep8Naming
def getHtmlTree(url, **kwargs):
    """
    获取html树
    :param url:
    :param kwargs:
    :return:
    """

    header = {'Connection': 'keep-alive',
              'Cache-Control': 'max-age=0',
              'Upgrade-Insecure-Requests': '1',
              'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko)',
              'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
              'Accept-Encoding': 'gzip, deflate, sdch',
              'Accept-Language': 'zh-CN,zh;q=0.8',
              }
    # TODO 取代理服务器用代理服务器访问
    wr = WebRequest()

    # delay 2s for per request
    time.sleep(2)

    html = wr.get(url=url, header=header).content
    return etree.HTML(html)


def tcpConnect(proxy):
    """
    TCP 三次握手
    :param proxy:
    :return:
    """
    from socket import socket, AF_INET, SOCK_STREAM
    s = socket(AF_INET, SOCK_STREAM)
    ip, port = proxy.split(':')
    result = s.connect_ex((ip, int(port)))
    return True if result == 0 else False


# noinspection PyPep8Naming
def proxy_is_avaiable(food,dst_url='http://httpbin.org/ip'):
    """
    检验代理是否可用
    :param food:
    :param dst_url:
    :return:
    """
    proxy = food['proxy']
    if isinstance(proxy, bytes):
        proxy = proxy.decode('utf-8')
    proxies = {"http": "http://{0}".format(proxy)}
    try:
        rsp = requests.get(dst_url, proxies=proxies, timeout=10, verify=False)
        if rsp.status_code == 400:
            print('[!] 400 : %s' %proxy)
        if rsp.status_code != 200: return False
        represent_addr_list = [i.strip() for i in json.loads(rsp.content.decode()).get('origin').split(',')]
        #print(represent_addr_list)
        proxy_addr=food['proxy'].split(':')[0]
        food['anonymous'] = not len(represent_addr_list) > 1
        return proxy_addr in represent_addr_list
        #return False
    except Exception as e:
        # logger.error(str(e))
        #print(e)
        return False

# noinspection PyPep8Naming
def verifyProxyFormat(proxy):
    """
    检查代理格式
    :param proxy:
    :return:
    """
    import re
    verify_regex = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}"
    _proxy = re.findall(verify_regex, proxy)
    return len(_proxy)==1 and _proxy[0]==proxy