# -*- coding: utf-8 -*-
# !/usr/bin/env python3

import requests
import time
from lxml import etree
import logging
from Util.WebRequest import WebRequest
import json
import re

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
        #if rsp.status_code == 400:
        #    logging.warn('[!] 400 : %s' %proxy)
        if rsp.status_code != 200: return False
        represent_addr_list = [i.strip() for i in json.loads(rsp.content.decode()).get('origin').split(',')]
        proxy_addr=food['proxy'].split(':')[0]
        food['anonymous'] = not len(represent_addr_list) > 1
        return proxy_addr in represent_addr_list
    except Exception as e:
        return False

def verifyProxyFormat(proxy):
    """
    检查代理格式
    :param proxy:
    :return:
    """
    verify_regex = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}"
    _proxy = re.findall(verify_regex, proxy)
    return len(_proxy) == 1 and _proxy[0] == proxy