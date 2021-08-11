#!/usr/bin/env python
# -*- coding:utf-8 -*-
import time
import os
if os.name == 'nt':
    import win32api
from datetime import datetime
from utils.log import Logger
from utils.util import (
    get_now_datetime
)

def adjust_server_time(func, login_username):
    logger = Logger(login_username).set_logger()
    logger.info('===============================更新本地时间==============================')
    t_diff, t_server_real_time, t_server_datetime, t_reach, t_reach_min, t_local, t_reach_server_leading_in_millie_sec = func(True)
    
    if os.name == "nt":
        _nt_set_time(t_server_real_time)
    else:
        _linux_set_time(t_server_real_time)
    
    t_local_adjusted = get_now_datetime()

    logger.info('本地时间                             %s', t_local)
    logger.info('本次服务器理论时间                   %s', t_server_real_time)
    logger.info('本地服务器差值                       %sms', t_diff)
    logger.info('更新后本地时间                       %s', t_local_adjusted)

    logger.info('===============================更新本地时间==============================')

def _linux_set_time(t_server_real_time):
    import ctypes
    import ctypes.util
    import time
    CLOCK_REALTIME = 0
    time_tuple = t_server_real_time.timetuple()

    class timespec(ctypes.Structure):
        _fields_ = [("tv_sec", ctypes.c_long),
                    ("tv_nsec", ctypes.c_long)]

    librt = ctypes.CDLL(ctypes.util.find_library("rt"))

    ts = timespec()
    ts.tv_sec = int( time.mktime(datetime(*time_tuple[:6]).timetuple()))
    ts.tv_nsec = time_tuple[6] * 1000000 # Millisecond to nanosecond

    # http://linux.die.net/man/3/clock_settime
    librt.clock_settime(CLOCK_REALTIME, ctypes.byref(ts))

def _nt_set_time(t_server_real_time):
    tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst = time.gmtime(time.mktime(t_server_real_time.timetuple()))
    msec = t_server_real_time.microsecond / 1000
    win32api.SetSystemTime(tm_year, tm_mon, tm_wday, tm_mday, tm_hour, tm_min, tm_sec, int(msec))