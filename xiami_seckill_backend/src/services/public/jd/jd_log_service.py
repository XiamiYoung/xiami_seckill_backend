#!/usr/bin/env python
# -*- coding: utf-8 -*-
from daos.cache.redis import CacheDao

class JDLogService(object):

    def __init__(self):
        self.cache_dao = CacheDao()

    def read_execution_log(self, login_username, nick_name, last_id):
        # steam message
        logger_stream = login_username + '_' + nick_name
        
        # read log from cache
        message_list = self.cache_dao.read_from_stream(logger_stream, last_id)

        return message_list