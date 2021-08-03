# -*- coding:utf-8 -*-
import time
from datetime import datetime
from utils.log import logger
from config.constants import (
    DATETIME_STR_PATTERN
)

from utils.util import (
    sleep_with_check
)

class Timer(object):

    def __init__(self, service_ins, target_time, cache_key, sleep_interval=0.0001):

        # '2018-09-28 22:45:50.000'
        self.target_time = datetime.strptime(target_time, DATETIME_STR_PATTERN)
        self.sleep_interval = sleep_interval
        self.cache_key = cache_key
        self.service_ins = service_ins

    def start(self, title=''):
        self.service_ins.log_stream_info('=========================================================================')
        if not title:
            self.service_ins.log_stream_info('正在等待到达设定时间:%s', self.target_time)
        else:
            self.service_ins.log_stream_info('准备执行%s, 开始时间:%s', title, self.target_time)
        self.service_ins.log_stream_info('=========================================================================')
        now_time = datetime.now
        while True:
            if now_time() >= self.target_time:
                self.service_ins.log_stream_info('时间到达，开始执行……')
                return True
            else:
                if not sleep_with_check(self.sleep_interval, self.cache_key):
                    return False