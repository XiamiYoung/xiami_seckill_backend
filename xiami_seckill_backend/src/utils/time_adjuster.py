#!/usr/bin/env python
# -*- coding:utf-8 -*-
import time
import win32api
from utils.log import logger
from utils.util import (
    get_now_datetime
)

def adjust_server_time(func):

    logger.info('===============================更新本地时间==============================')
    t_diff, t_server_real_time, t_server_datetime, t_reach, t_reach_min, t_local, t_reach_server_leading_in_millie_sec = func(True)

    tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst = time.gmtime(time.mktime(t_server_real_time.timetuple()))
    msec = t_server_real_time.microsecond / 1000
    win32api.SetSystemTime(tm_year, tm_mon, tm_wday, tm_mday, tm_hour, tm_min, tm_sec, int(msec))
    t_local_adjusted = get_now_datetime()

    logger.info('本地时间                             %s', t_local)
    logger.info('本次服务器理论时间                   %s', t_server_real_time)
    logger.info('本地服务器差值                       %sms', t_diff)
    logger.info('更新后本地时间                       %s', t_local_adjusted)

    logger.info('===============================更新本地时间==============================')