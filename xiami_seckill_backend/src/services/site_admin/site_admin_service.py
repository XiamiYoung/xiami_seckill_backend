#!/usr/bin/env python
# -*- coding: utf-8 -*-
from daos.db.user_dao import UserDao
from config.error_dict import error_dict
from exception.restful_exception import RestfulException

class SiteAdminService(object):
    def __init__(self):
        self.user_dao = UserDao()

    def create_enduser(self, data):
        username = data.get('userName')
        password = data.get('password')
        login_user_qs = self.user_dao.find_by_username_password(username, password)
        user_count = login_user_qs.count()
        if user_count > 0:
            exception = RestfulException(error_dict['ADMIN']['USER_EXISTS'])
            raise exception
        user_model = self.user_dao.create_enduser(username=username,password=password)
        return user_model.to_dict(exclude=['password'])