#!/usr/bin/env python
# -*- coding: utf-8 -*-

from daos.db.jd_order_dao import JDOrderDao
from services.public.common.login_user_service import LoginUserService

from utils.util import (
    str_to_json,
)

class JDOrderService(object):
    def __init__(self):
        self.jd_order_dao = JDOrderDao()
        self.login_user_service = LoginUserService()

    def save_jd_order(self, user_name, order_data, is_return_model=True):
        login_user_model = self.login_user_service.find_user_by_username(user_name, is_return_model=True)
        jd_order_model = self.jd_order_dao.save_jd_order(order_data, login_user_model)
        if is_return_model:
            return jd_order_model
        else:
            return jd_order_model.to_dict()

    def find_jd_orders_by_username(self, user_name):
        login_user_model = self.login_user_service.find_user_by_username(user_name, is_return_model=True)
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
                'is_reserve': order_item['is_reserve'],
                'is_seckill': order_item['is_seckill'],
                'leading_time': order_item['leading_time'],
                'stock_count': order_item['stock_count'],
                'current_price': order_item['current_price'],
                'original_price': order_item['original_price'],
                'saved_price': order_item['saved_price'],
                'item_info_array': str_to_json(order_item['item_info_array']),
            })
        return jd_order_data_list