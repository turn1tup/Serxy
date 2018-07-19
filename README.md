# Serxy

`Serxy`是一款用Python编写的`代理服务器`与`代理池`的结合体，它可以根据客户端的HTTP/HTTPS请求中的`Host`字段来为该种请求创建并维护一个代理池。代理池的功能参考`Configuration/ProConfig.ini`配置文件。

python3.4+  

三方库 `requirement.txt`

数据库` mongodb`


### 注意事项：

1）不要更改系统时间

2）mongodb 匿名访问



## 业务场景

1）爬虫使用，爬谷歌或是有一些IP反爬机制的网站

2）暴力破解，一些网站访问频率过高的就会对IP进行屏蔽



### 待解决或是无法解决的问题

1）
本地代理服务器作为 客户端 与 远程代理服务器的 中间人，本地代理服务器与双方都建立了TCP套接字,在其 读取了客户端的请求数据后，会立即把数据发给远程代理服务器。在这期间，一旦获取到远程套接字的数据，就写回给客户端。但是，这期间很可能发生超时timeout的情况，也就是说客户端访问到的web界面是不完整的。

 这个情况在本地代理服务器这里，笔者认为是无法处理的，因为代理服务器无法知道一个HTTP Response的大小（HTTPS连接无法解决），所以针对这种超时后仅仅返回部分界面的情况，只能在客户端处理，客户端需要检查获取到的HTTP Response消息中的Content-Length 字段声明的长度是否与接收到的返回包的长度一致，如果不一致或是没有找到该字段，则考虑把包丢弃。

上面这种行为让我一开始写这个项目的一些想法无法实现，起初是想让sqlmap/burpsuit可以直接使用的，看来是不行了。sqlmap 假如需要使用该代理服务器，最好需要处理这种情况。当然，假如你的代理都是十分稳定的，不会发生建立套接字传输数据过程中超时中断的情况，上面这种情况可以不处理。

2）
验证代理可用性的界面太简单了，数据只有几十个字节，但是我们通常访问的网页数据实际上达到了上万字节，所以表面上可用的代理，
实际下来可用性十分底，所以这里考虑自己搭建一个验证代理的界面。


### License
Copyright 2018 trun1tup

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

`http://www.apache.org/licenses/LICENSE-2.0`

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
