from gevent import monkey; monkey.patch_socket()
import gevent

def f(n):
    for i in range(n):
        print(gevent.getcurrent(), i)
try:
	while True:
		g = gevent.spawn(f, 3)
		g.join()
	
except KeyboardInterrupt:
	exit(1)
except Exception as e:
	print(e)
'''
def f(url):
    print('GET: %s' % url)
    resp = urllib2.urlopen(url)
    data = resp.read()
    print('%d bytes received from %s.' % (len(data), url))

gevent.joinall([
        gevent.spawn(f, 'https://www.python.org/'),
        gevent.spawn(f, 'https://www.yahoo.com/'),
        gevent.spawn(f, 'https://github.com/'),
])
'''