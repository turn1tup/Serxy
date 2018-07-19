#-*-coding:utf-8-*-
import requests
url='http://www.dedecms.com'
proxies = {'http':'http://192.168.219.130:1000'}
resp = requests.get(url,proxies=proxies,timeout=60)
print(len(resp.text))
#print(resp.text.encode('utf-8').decode('gbk'))
#with open('r.txt','bw') as f:
#    f.write(resp.text)
