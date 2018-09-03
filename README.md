# Serxy

`Serxy`是一款用Python编写的`代理服务器`与`代理池`的结合体，它可以根据客户端的HTTP/HTTPS请求中的`Host`字段来为该种请求创建并维护一个代理池。代理池的功能参考`Configuration/ProConfig.ini`配置文件。

python3.5 +  

三方库 `requirements.txt`

数据库` mongodb`

### 说明

本地代理服务器作为 客户端 与 远程代理服务器的 中间人，本地代理服务器与双方都建立了TCP套接字,能否进行HTTPS通信主要取决于远程代理服务器是否支持`CONNECT`方法。
代理池会定期执行`ProxiesGetter/methods.py`中的方法，抓取新的代理。

#### 安装过程

`debian`下操作过程
apt-get install mongodb
service mongodb start
git clone git@github.com:turn1tup/Serxy.git
cd Serxy
python3 -m pip install requirements.txt
cd Run
python3 main.py

#### 特性

1. `黑白名单` 支持黑白名单，默认屏蔽谷歌站点
2. `多进程` 本地代理服务器进程数量可多个，仅支持 UNIX 系统
3. `独立代理池` 每个目标站点的代理池为分开的，目的是为了更好地进行“定制化服务”
4. `轮换` 代理池内的代理是伦换使用的
5. `代理池大小自定义 ` 可设置代理池的最小数量与最大数量，代理池降低至最低数量时将自动补充至最大数量
6. `屏蔽检测` 可根据用户配置识别目标站点是否被屏蔽，并自动切换IP
7. `匿名` 可配置选择的代理是否需要匿名，如果选择匿名的话代理数量可用的会比较少，如无必要则不应该开启。
8. `记录代理banner信息` 自动将爬取到的代理的 Server 关键字进行去重后保存，可用于 shodan 等等有意思的事情。
9. `代理分类` 自动验证代理是否支持隧道代理

#### 添加爬虫方法

如果需要添加新的方法，定时到网站去爬取代理，操作如下：在ProxiesGetter/methods.py的class Methods 中添加一个方法，并声明`staticmethod ` ,方法名以 *freeProxy* 关键字开头，爬取的结果需要是 *addresss:port* 即 *192.168.1.1:8080* 这种格式的，然后将其 yield 出来即可。

#### ServerConfig.ini

*DBProxiesGetterProcessInterval* 程序会定期对数据库中的代理进行可用性验证，这里设置该间隔的时间，单位秒

RowProxiesGetterProcessesInterval 程序会定期执行*Methods* 类中的以 *freeProxy* 开头的静态方法，该指令设置间隔时间.

#### ProConfig.ini

配置文件有全局配置和指定配置，如何某个目标站点，没有设置特定的配置，默认使用全局配置

### 注意事项：

1）不要更改系统时间

2）mongodb 匿名访问

3)第一次运行程序，数据库中没有代理IP数据，所以应先等待15分钟再使用代理服务

4) 如果目标网站不可访问，被墙/挂了 等，就不要通过本代理去访问了，否则会影响代理可用性统计情况

### 业务场景

1）爬虫使用，爬谷歌或是有一些IP反爬机制的网站

2）暴力破解，一些网站访问频率过高的就会对IP进行屏蔽


### 提示

免费代理爬得再多又如何，真正可用的少.

### 更新日志

20180830 代理入库时标记是否支持HTTPS，客户端请求为HTTPS类型时则不使用不支持CONNECT的代理

20180722 修改代理验证方法，尝试记录代理服务器的*Server*字段，为以后通过shodan抓取代理垫下基础。

