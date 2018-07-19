import requests
import urllib2
url = 'http://www.baidu.com'
#proxies = {'http':'http://92.114.61.21:80'}
#proxies = {'http':'http://127.0.0.1:18080'}
proxies = {'http':'http://97.64.107.180:1000'}
#resp = requests.get('http://www.baidu.com',proxies=proxies)


resp2 = requests.get(url ,proxies=proxies)
print('urllib2 status_code:%d'%resp2.status_code())



'''
proxy_handler = urllib2.ProxyHandler(proxies)
opener = urllib2.build_opener(proxy_handler)
urllib2.install_opener(opener)
req = urllib2.Request(url)
resp = urllib2.urlopen(req)
print('status_code:%d'%resp.getcode())
'''