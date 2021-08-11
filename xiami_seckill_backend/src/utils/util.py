#!/usr/bin/env python
# -*- coding:utf-8 -*-
import functools
import json
import os
import random
import re
import warnings
import time
import random
import math
import time
from functools import wraps
from itertools import chain
from datetime import datetime
from datetime import timedelta
from base64 import b64encode
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from daos.cache.redis import CacheDao
from config.constants import (
    RSA_PUBLIC_KEY,
    DATETIME_STR_PATTERN
)
from utils.log import Logger

import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5

cacheIns = CacheDao()

def encrypt_pwd(password, public_key=RSA_PUBLIC_KEY):
    rsa_key = RSA.importKey(public_key)
    encryptor = Cipher_pkcs1_v1_5.new(rsa_key)
    cipher = b64encode(encryptor.encrypt(password.encode('utf-8')))
    return cipher.decode('utf-8')


def encrypt_payment_pwd(payment_pwd):
    return ''.join(['u3' + x for x in payment_pwd])


def response_status(resp):
    if resp.status_code != requests.codes.OK:
        print('Status: %u, Url: %s' % (resp.status_code, resp.url))
        return False
    return True


def open_image(image_file):
    if os.name == "nt":
        os.system('start ' + image_file)  # for Windows
    else:
        if os.uname()[0] == "Linux":
            if "deepin" in os.uname()[2]:
                os.system("deepin-image-viewer " + image_file)  # for deepin
            else:
                os.system("eog " + image_file)  # for Linux
        else:
            os.system("open " + image_file)  # for Mac


def save_image(resp, image_file):
    with open(image_file, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=1024):
            f.write(chunk)


def parse_json(s):
    begin = s.find('{')
    end = s.rfind('}') + 1
    return json.loads(s[begin:end])

def parse_original_json(s):
    return json.loads(s)

def json_to_str(json_obj):
    return json.dumps(json_obj,ensure_ascii=False)

def get_tag_value(tag, key='', index=0):
    if len(tag) == 0:
        return ''
    if key:
        value = tag[index].get(key)
    else:
        value = tag[index].text
    return value.strip(' \t\r\n')

def parse_items_dict(d):
    result = ''
    for index, key in enumerate(d):
        if index < len(d) - 1:
            result = result + '{0} x {1}, '.format(key, d[key])
        else:
            result = result + '{0} x {1}'.format(key, d[key])
    return result

def parse_callback_str(original):
    begin = original.find('(') + 1
    end = original.rfind(')')
    original = original[begin:end]
    
    if ')}' in original:
        begin = 0
        end = original.rfind(')}')
        original = original[begin:end]
    
    if ');}' in original:
        begin = 0
        end = original.rfind(');}')
        original = original[begin:end]
        
    original = original.replace(',}','}')
    return original

def gen_int_with_len(len_bit):
    s = ''
    for count in range(0, len_bit):
        s+= str(random.randint(1, 9))
    return s

def parse_cart_item_array(original):
    item_array = original.split(',')

    id_array = []

    for item in item_array:
        if item.startswith('"id":'):
            begin = item.find(':') + 1
            end = len(item)
            item_parsed = item[begin:end]
            id_array.append(item_parsed)

    return id_array

def str_remove_newline(original):
    return original.replace('\\r\\n', '')

def parse_sku_id(sku_ids):
    """将商品id字符串解析为字典

    商品id字符串采用英文逗号进行分割。
    可以在每个id后面用冒号加上数字，代表该商品的数量，如果不加数量则默认为1。

    例如：
    输入  -->  解析结果
    '123456' --> {'123456': '1'}
    '123456,123789' --> {'123456': '1', '123789': '1'}
    '123456:1,123789:3' --> {'123456': '1', '123789': '3'}
    '123456:2,123789' --> {'123456': '2', '123789': '1'}

    :param sku_ids: 商品id字符串
    :return: dict
    """
    if isinstance(sku_ids, dict):  # 防止重复解析
        return sku_ids

    sku_id_list = list(filter(bool, map(lambda x: x.strip(), sku_ids.split(','))))
    result = dict()
    for item in sku_id_list:
        if ':' in item:
            sku_id, count = map(lambda x: x.strip(), item.split(':'))
            result[sku_id] = count
        else:
            result[item] = '1'
    return result

def remove_last_char(original, last_char):
    end = original.rfind(last_char)
    return original[0:end]
    
def build_target_sku_id_list(target_sku_id_list):
    sku_id_list = ''
    for sku_id in target_sku_id_list:
        sku_id_list += sku_id + ','
        
    sku_id_list = remove_last_char(sku_id_list, ',')
    return sku_id_list

def str_to_datetime(t_str, format_pattern=DATETIME_STR_PATTERN):
    return datetime.strptime(t_str, format_pattern)

def datetime_to_str(t_datetime, format_pattern=DATETIME_STR_PATTERN):
    return t_datetime.strftime(format_pattern)

def parse_area_id(area):
    """解析地区id字符串：将分隔符替换为下划线 _
    :param area: 地区id字符串（使用 _ 或 - 进行分割），如 12_904_3375 或 12-904-3375
    :return: 解析后字符串
    """
    area_id_list = list(map(lambda x: x.strip(), re.split('_|-', area)))
    area_id_list.extend((4 - len(area_id_list)) * ['0'])
    return '_'.join(area_id_list)


def split_area_id(area):
    """将地区id字符串按照下划线进行切割，构成数组。数组长度不满4位则用'0'进行填充。
    :param area: 地区id字符串（使用 _ 或 - 进行分割），如 12_904_3375 或 12-904-3375
    :return: list
    """
    area_id_list = list(map(lambda x: x.strip(), re.split('_|-', area)))
    area_id_list.extend((4 - len(area_id_list)) * ['0'])
    return area_id_list


def deprecated(func):
    """This decorator is used to mark functions as deprecated.
    It will result in a warning being emitted when the function is used.
    """

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn(
            "Call to deprecated function {}.".format(func.__name__),
            category=DeprecationWarning,
            stacklevel=2
        )
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)

    return new_func


def check_login(func):
    """用户登陆态校验装饰器。若用户未登陆，则调用扫码登陆"""

    @functools.wraps(func)
    def new_func(self, *args, **kwargs):
        logger = Logger(self.login_username).set_logger()
        if not self.is_login:
            logger.info("{0} 需登陆后调用，开始扫码登陆".format(func.__name__))
            self.login_by_QRcode()
        return func(self, *args, **kwargs)

    return new_func

def fetch_latency(func):
    """打印当前方法调用时间"""
    
    @functools.wraps(func)
    def new_func(self, *args, **kwargs):
        # logger = Logger(self.login_username).set_logger()
        t_before = datetime.now()
        ret = func(self, *args, **kwargs)
        t_after = datetime.now()
        t_network = get_timestamp_in_milli_sec(t_after) - get_timestamp_in_milli_sec(t_before)
        self.last_func_cost = t_network
        self.log_stream_info('%s用时%sms', func.__name__, self.last_func_cost)
        return ret

    return new_func

def get_random_useragent():
    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]   
    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)

    # Get Random User Agent String.
    user_agent = user_agent_rotator.get_random_user_agent()

    return user_agent

def to_millieseconds(dt_obj):
    return time.mktime(dt_obj.timetuple()) + dt_obj.timestamp() / 1e7

def datetime_offset_in_milliesec(dt, offset_in_milliesec):
    return dt + timedelta(milliseconds=offset_in_milliesec)

def get_now_datetime():
    return datetime.now()

def get_debug_target_time(leading_in_sec=10):
    debug_target_datetime = datetime.now() + timedelta(seconds=leading_in_sec)
    debug_target_str = debug_target_datetime.strftime(DATETIME_STR_PATTERN)

    return debug_target_str

def get_timestamp_in_milli_sec(dt_obj):
    return int(time.mktime(dt_obj.utctimetuple()) * 1000 + dt_obj.microsecond / float(1000) + dt_obj.microsecond / float(1000) / float(1000))

def get_ts_diff_with_floor(dt_after, dt_before):
    return math.floor(get_timestamp_in_milli_sec(dt_after) - get_timestamp_in_milli_sec(dt_before))

def get_next_in_sec(offset_in_sec):
    dt = datetime.now()
    delta = timedelta(seconds=offset_in_sec)
    target_dt = dt + (datetime.min - dt) % delta
    target_str = target_dt.strftime(DATETIME_STR_PATTERN)
    return target_str

def contains_reserve_product(target_product):
    if target_product['is_reserve_product']:
        return True
    else:
        return False

def contains_presale_product(target_product):
    if target_product['is_presale_product']:
        return True
    else:
        return False

def is_all_jd_delivery(target_product):
    if target_product['is_jd_delivery']:
        return True
    else:
        return True

def select_random_item_from_array(array):
    return random.choice(array)

def get_floor_int_from_float(float_obj):
    return math.modf(float_obj)[1]

def cookie_dict_to_str(cookies_dict):
    cookie_string = "; ".join([str(x)+"="+str(y) for x,y in cookies_dict.items()])
    return cookie_string

def build_item_info(item_info_array):
    built_str = ''
    for item in item_info_array:
        built_str += '<div>商品数量:{}</div></br>商品名称:{}</br><img src="{}"/>'.format(item['quantity'], item['name'].replace('%',''), item['image'])
    return built_str

def build_order_message(nick_name, order_info_item):
    built_item_str = build_item_info(order_info_item['item_info_array'])
    subject = nick_name + '订单成功, 收件人:{}'.format(order_info_item['addr_name'])
    content = '<html><body><h1>订单号: {}</h1><div>订单价格:{}</div><div>收货地址:{}</div><div>商品明细</div></br>{}</body></html>'.format(order_info_item['order_id'], order_info_item['sum_price'], order_info_item['addr'], built_item_str)
    return subject, content

def is_class_type_of(instance, class_name):
    return type(instance).__name__ == class_name

def str_to_json(str):
    if not str:
        return {}
    else:
        return json.loads(str)

def sleep_with_check(sleep_interval, cache_key):
    if cache_key:
        cache_ret = cacheIns.get(cache_key)
        if cache_ret and cache_ret['cancelled']:
            return False
    time.sleep(sleep_interval)
    return True

def build_stream_message(message, level, *args):
    if args and len(args[0])!=0:
        return {'content': '[' + level + '][' + datetime_to_str(datetime.now()) + ']' + message.replace('%s','{}').format(*args[0])}
    return {'content': '[' + level + '][' + datetime_to_str(datetime.now()) + ']' +  message}

def model_to_dict(instance):
    opts = instance._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields):
        data[f.name] = f.value_from_object(instance)
    for f in opts.many_to_many:
        data[f.name] = [i.id for i in f.value_from_object(instance)]
    return data