#!/usr/bin/env python
# -*- coding: utf-8 -*-
from daos.db.common.login_user_dao import LoginUserDao
from config.error_dict import error_dict
from exception.restful_exception import RestfulException

from utils.util import (
    get_sys_info,
    get_server_uptime,
    reboot_server
)

class SiteAdminService(object):
    def __init__(self):
        self.login_user_dao = LoginUserDao()

    def create_enduser(self, data):
        username = data.get('userName')
        password = data.get('password')
        login_user_qs = self.login_user_dao.find_by_username_password(username, password)
        user_count = login_user_qs.count()
        if user_count > 0:
            exception = RestfulException(error_dict['ADMIN']['USER_EXISTS'])
            raise exception
        user_model = self.login_user_dao.create_enduser(username=username,password=password)
        return user_model.to_dict(exclude=['password'])

    def get_sys_info(self):
        return get_sys_info()

    def reboot_server(self):
        return reboot_server()

    def check_sys_status(self):
        return get_server_uptime()
