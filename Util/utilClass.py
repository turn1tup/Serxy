# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File Name：     utilClass.py  
   Description :  tool class
   Author :       JHao
   date：          2016/12/3
-------------------------------------------------
   Change Activity:
                   2016/12/3: Class LazyProperty
-------------------------------------------------
"""
__author__ = 'JHao'


class LazyProperty(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            value = self.func(instance)
            setattr(instance, self.func.__name__, value)
            return value


'''
class Singleton(type):
    """
    Singleton Metaclass
    """

    _inst = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._inst:
            cls._inst[cls] = super(Singleton, cls).__call__(*args)
        return cls._inst[cls]
'''

'''
仅仅适用多线程，不适用多进程
经过测试发现queue.Priority不存在线程安全问题
但是，在多线程测试中，发现在实际使用中可能有少数数据不是按等级出来的,但可以标记为无影响
'''
class Object2WaitforComfirm():
    def __init__(self,data,priority):
        self.data=data
        self.priority=priority

    def __lt__(self, other):  # operator <
        return self.priority < other.priority

    def __ge__(self, other):  # oprator >=
        return self.priority >= other.priority

    def __le__(self, other):  # oprator <=
        return self.priority <= other.priority

    def __str__(self):
        return '(' + str(self.priority) + ',\'' + self.data + '\')'
    def __cmp__(self, other):
        return self.priority >= other.priority
'''
由于python中没有多进程下的优先级队列，只好自己瞎编一个了。。。
'''
from multiprocessing import Queue
class PriorityQueue(object):
    def __init__(self):
        self.q1 = Queue()
        self.q2 = Queue()
        self.q3 = Queue()
    def put(self,object,priority):
        if not object:
            return
        if priority == 1:
            self.q1.put(object)
        elif priority == 2:
            self.q2.put(object)
        else:
            self.q3.put(object)
    def get(self, block=True, timeout=None):
        if not self.q1.empty():
            return self.q1.get(block=block, timeout=timeout)
        if not self.q2.empty():
            return self.q2.get(block=block, timeout=timeout)
        else:
            return self.q3.get(block=block, timeout=timeout)

    def get_nowait(self):
        return self.get(block=False)