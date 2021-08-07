#!/usr/bin/env python
# -*- coding: utf-8 -*-

from daos.db.user_dao import UserDao
from daos.db.jd_user_dao import JDUserDao
from daos.db.jd_order_dao import JDOrderDao
from daos.db.jd_user_arrangement_dao import JDUserArrangementDao

from config.error_dict import error_dict
from exception.restful_exception import RestfulException

from utils.util import (
    str_to_json,
)

class UserService(object):
    def __init__(self):
        self.user_dao = UserDao()
        self.jd_user_dao = JDUserDao()
        self.jd_order_dao = JDOrderDao()
        self.jd_user_arrangement_dao = JDUserArrangementDao()

    def login_with_username_password(self, data, is_return_model=False):
        username = data.get('userName')
        password = data.get('password')
        login_user_qs = self.user_dao.find_by_username_password(username, password)
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
        user_qs = self.user_dao.find_by_username(user_name)
        user_count = user_qs.count()
        if user_count == 0:
            return {}
        if user_count > 1:
            exception = RestfulException(error_dict['USER']['USER_DUPLICATED'])
            raise exception
        if is_return_model:
            return user_qs.first()
        else:
            return user_qs.first().to_dict()

    def find_jd_user_by_nick_name(self, nick_name, is_return_model=False):
        jd_user_qs = self.jd_user_dao.find_by_nick_name(nick_name)
        user_count = jd_user_qs.count()
        if user_count == 0:
            return {}
        if user_count > 1:
            exception = RestfulException(error_dict['USER']['USER_DUPLICATED'])
            raise exception
        if is_return_model:
            return jd_user_qs.first()
        else:
            return jd_user_qs.first().to_dict()

    def find_jd_user_cookies_by_username_and_nick_name(self, user_name, nick_name):
        login_user_model = self.find_user_by_username(user_name, is_return_model=True)
        jd_user_list = list(login_user_model.jduser_set.all().values())
        for jd_user in jd_user_list:
            if jd_user['nick_name'] == nick_name:
                return jd_user['pc_cookie_str'], jd_user['mobile_cookie_str']

        return '', ''

    def save_or_update_jd_user(self, user_name, jd_user_data, is_return_model=False):
        user_model = self.find_user_by_username(user_name, is_return_model=True)
        jd_user_model = self.jd_user_dao.save_or_update_jd_enduser(jd_user_data, user_model)
        if is_return_model:
            return jd_user_model
        else:
            return jd_user_model.to_dict(exclude=['pc_cookie_str','mobile_cookie_str'])

    def delete_jd_user_by_nick_name(self, user_name, nick_name):
        login_user_model = self.find_user_by_username(user_name, is_return_model=True)
        jd_user_list = list(login_user_model.jduser_set.all().values())
        for jd_user in jd_user_list:
            if jd_user['nick_name'] == nick_name:
                # delete user arrangement
                jd_user_arrangement_model = self.find_jd_user_arrangement_by_username(user_name)
                if jd_user_arrangement_model and jd_user_arrangement_model['seckill_arrangement']:
                    json_seckill_arrangement = str_to_json(jd_user_arrangement_model['seckill_arrangement'])
                    if json_seckill_arrangement[nick_name]:
                        del json_seckill_arrangement[nick_name]
                        self.save_or_update_jd_user_arrangement(user_name, json_seckill_arrangement)
                self.jd_user_dao.delete_by_id(jd_user['id'])
        

    def save_jd_order(self, user_name, order_data, is_return_model=True):
        login_user_model = self.find_user_by_username(user_name, is_return_model=True)
        jd_order_model = self.jd_order_dao.save_jd_order(order_data, login_user_model)
        if is_return_model:
            return jd_order_model
        else:
            return jd_order_model.to_dict()

    def find_jd_orders_by_username(self, user_name):
        login_user_model = self.find_user_by_username(user_name, is_return_model=True)
        jd_order_list = list(login_user_model.jdorder_set.all().order_by('-created_ts').values())
        jd_order_data_list = []
        for order_item in jd_order_list:
            jd_order_data_list.append({
                'nick_name': order_item['nick_name'],
                'order_id': order_item['order_id'],
                'order_time': order_item['order_time'],
                'sum_price': order_item['sum_price'],
                'addr_name': order_item['addr_name'],
                'addr': order_item['addr'],
                'item_info_array': str_to_json(order_item['item_info_array']),
            })
        return jd_order_data_list

    def find_jd_user_arrangement_by_username(self, user_name, is_return_model=False):
        jd_user_arrangement_model = self.jd_user_arrangement_dao.find_jd_user_arrangement_by_username(user_name)
        if jd_user_arrangement_model:
            if is_return_model:
                return jd_user_arrangement_model
            else:
                return jd_user_arrangement_model.to_dict()
        else:
            return {}

    def save_or_update_jd_user_arrangement(self, user_name, jd_user_arrangement_data, is_return_model=False):
        user_model = self.find_user_by_username(user_name, is_return_model=True)
        jd_user_arrangement_model = self.jd_user_arrangement_dao.save_or_update_jd_user_arrangement(jd_user_arrangement_data, user_model)
        if is_return_model:
            return jd_user_arrangement_model
        else:
            return jd_user_arrangement_model.to_dict()

    def update_leading_time(self, nick_name, leading_time):
        self.jd_user_dao.update_leading_time(nick_name, leading_time)