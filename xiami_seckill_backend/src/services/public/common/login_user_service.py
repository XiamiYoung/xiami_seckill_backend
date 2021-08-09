#!/usr/bin/env python
# -*- coding: utf-8 -*-

from daos.db.common.login_user_dao import LoginUserDao

from config.error_dict import error_dict
from exception.restful_exception import RestfulException

class LoginUserService(object):
    def __init__(self):
        self.login_user_dao = LoginUserDao()

    def login_with_username_password(self, data, is_return_model=False):
        username = data.get('userName')
        password = data.get('password')
        login_user_qs = self.login_user_dao.find_by_username_password(username, password)
        user_count = login_user_qs.count()
        if user_count == 0:
            return {}
        if user_count > 1:
            exception = RestfulException(error_dict['USER']['LOGIN_CRED_DUPLICATED'])
            raise exception

        if is_return_model:
            return login_user_qs.first()
        else:
            return login_user_qs.first().to_dict(exclude=['password'])
        
    def find_user_by_username(self, user_name, is_return_model=False):
        user_qs = self.login_user_dao.find_by_username(user_name)
        user_count = user_qs.count()
        if user_count == 0:
            return {}
        if user_count > 1:
            exception = RestfulException(error_dict['USER']['USER_DUPLICATED'])
            raise exception
        if is_return_model:
            return user_qs.first()
        else:
            return user_qs.first().to_dict(exclude=['password'])
    