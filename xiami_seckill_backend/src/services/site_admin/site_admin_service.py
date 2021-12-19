#!/usr/bin/env python
# -*- coding: utf-8 -*-
from daos.db.common.login_user_dao import LoginUserDao
from config.error_dict import error_dict
from exception.restful_exception import RestfulException
from daos.cache.redis import CacheDao
from services.public.common.login_user_service import LoginUserService
from services.public.jd.jd_order_service import JDOrderService

from utils.util import (
    get_sys_info,
    get_server_uptime,
    reboot_server
)

from config.constants import (
    SYS_INFO_CACHE_KEY
)

jd_order_service = JDOrderService()
login_user_service = LoginUserService()

class SiteAdminService(object):
    def __init__(self):
        self.login_user_dao = LoginUserDao()
        self.cache_dao = CacheDao()

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

    def check_sys_info_result(self):
        return self.cache_dao.get(SYS_INFO_CACHE_KEY)

    def reboot_server(self):
        return reboot_server()

    def find_all_users(self, username=None, with_order=False):
        if not username:
            login_user_list = login_user_service.find_all_users()
        else:
            login_user_list = []
            login_user = login_user_service.find_user_by_username(username)
            login_user_list.append(login_user)
        if with_order:
            for login_user in login_user_list:
                order_list = jd_order_service.find_jd_orders_by_username(login_user['username'])
                login_user['order_list'] = order_list

        return login_user_list
