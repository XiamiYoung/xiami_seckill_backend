#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import pickle
import random
import time
import traceback
from datetime import datetime
import requests
import os
from bs4 import BeautifulSoup
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from utils.time_adjuster import adjust_server_time
from config.config import global_config
from config.error_dict import error_dict
from exception.restful_exception import RestfulException
from utils.log import Logger
from utils.emailer import Emailer
from utils.timer import Timer
import logging
from services.public.common.login_user_service import LoginUserService
from services.public.jd.jd_order_service import JDOrderService
from services.public.jd.jd_user_service import JDUserService

from daos.cache.redis import CacheDao
import redis_lock
from config.constants import (
    DEFAULT_TIMEOUT,
    DEFAULT_PC_USER_AGENT,
    DEFAULT_MOBILE_USER_AGENT,
    ARRANGEMENT_EXEC_STATUS_PLANNED,
    ARRANGEMENT_EXEC_STATUS_RUNNING,
    ARRANGEMENT_EXEC_STATUS_CANCELLED,
    ARRANGEMENT_EXEC_STATUS_SUCCEEDED,
    ARRANGEMENT_EXEC_STATUS_FAILED,
    ARRANGEMENT_EXEC_STATUS_ERROR,
    DATETIME_STR_PATTERN_SHORT,
    DEFAULT_CACHE_TTL,
    DEFAULT_CACHE_STATUS_TTL,
    DEFAULT_CACHE_SECKILL_INFO_TTL,
    DEFAULT_CACHE_MOBILE_CODE,
    SECKILL_INFO_CACHE_KEY,
    LOCK_KEY_SECKILL_ARRANGEMENT,
    LOCK_KEY_CANCEL_SECKILL_ARRANGEMENT,
    LOCK_KEY_ADJUST_SERVER_TIME
)
from utils.util import (
    fetch_latency,
    encrypt_pwd,
    encrypt_payment_pwd,
    get_tag_value,
    get_random_useragent,
    open_image,
    parse_area_id,
    parse_json,
    parse_original_json,
    parse_callback_str,
    parse_cart_item_array,
    str_remove_newline,
    json_to_str,
    str_to_json,
    parse_sku_id,
    response_status,
    save_image,
    str_to_datetime,
    datetime_to_str,
    contains_reserve_product,
    contains_presale_product,
    is_all_jd_delivery,
    select_random_item_from_array,
    datetime_offset_in_milliesec,
    get_now_datetime,
    get_ts_diff_with_floor,
    gen_int_with_len,
    build_target_sku_id_list,
    build_order_message,
    sleep_with_check,
    build_stream_message,
    get_timestamp_in_milli_sec
)

from utils.token_util import (
    decrypt_token
)

class JDSeckillService(object):

    def __init__(self, login_username=''):
        # self.user_agent = get_random_useragent()
        self.user_agent = DEFAULT_PC_USER_AGENT
        self.mobile_user_agent = DEFAULT_MOBILE_USER_AGENT
        self.try_post_failure_in_mins = float(global_config.get('config', 'try_post_failure_in_mins'))
        self.try_post_failure_count = int(global_config.get('config', 'try_post_failure_count'))
        self.try_post_failure_interval = float(global_config.get('config', 'try_post_failure_interval'))
        self.check_stock_reduced_interval = float(global_config.get('config', 'check_stock_reduced_interval'))
        self.is_seckill_sold_out_total_count_threshold = int(global_config.get('config', 'is_seckill_sold_out_total_count_threshold'))
        self.is_seckill_sold_out_interval = float(global_config.get('config', 'is_seckill_sold_out_interval'))
        self.try_post_failure_not_sold_out_interval = float(global_config.get('config', 'try_post_failure_not_sold_out_interval'))
        self.random_stock_check_threshold = int(global_config.get('config', 'random_stock_check_threshold'))
        self.single_stock_check_interval = float(global_config.get('config', 'single_stock_check_interval'))
        if os.name == "nt":
            self.google_chrome_driver_name = global_config.get('config', 'google_chrome_driver_name_win')
        else:
            self.google_chrome_driver_name = global_config.get('config', 'google_chrome_driver_name_linux')
        self.marathon_sk = global_config.get('config', 'marathon_sk')
        self.is_debug_mode = global_config.getboolean('config', 'is_debug_mode')
        self.qr_scan_retry = int(global_config.get('config', 'qr_scan_retry'))
        self.seckill_skus_limit = int(global_config.get('config', 'seckill_skus_limit'))
        self.order_leading_in_millis = float(global_config.get('config', 'default_order_leading_in_millis'))
        self.eid = global_config.get('config', 'eid')
        self.fp = global_config.get('config', 'fp')
        self.track_id = global_config.get('config', 'track_id')
        self.db_prop_secret = global_config.get('config', 'db_prop_secret')
        self.default_system_emailer_address = global_config.get('config', 'default_system_emailer_address')
        self.default_system_emailer_token = global_config.get('config', 'default_system_emailer_token')
        self.most_delivery_fee = 20
        self.order_price_threshold = 0
        self.random_sku_price = 0
        self.create_order_round = random.randint(0, 10)
        self.is_ready_place_order = False
        self.headers = {'User-Agent': self.user_agent}
        self.risk_control = '' # 默认空字符串
        self.execution_cache_key = ''
        self.execution_status_cache_key = ''
        self.execution_keep_running = True
        self.execution_failure = False
        self.logger_stream = ''
        self.logger_group = ''
        self.logger_consumer = ''
        self.stream_enabled = False
        self.temp_order_traditional = False
        self.login_username = ''
        self.payment_pwd = ''

        self.timeout = float(DEFAULT_TIMEOUT)
        self.send_message = True
        self.emailer = None
        self.system_emailer = Emailer(self, self.default_system_emailer_address, self.default_system_emailer_token)

        self.item_cat = dict()
        self.item_vender_ids = dict()  # 记录商家id

        self.seckill_init_info = dict()
        self.seckill_order_data = dict()
        self.seckill_url = dict()
        self.target_product = {}	
        self.target_sku_id = ''	
        self.target_sku_num = 1
        self.failure_msg = ''

        self.addr_obj = []
        self.default_addr = []

        self.username = ''
        self.nick_name = ''
        self.area_id = ''
        self.user_id = ''
        self.jxsid = ''
        self.area_ref_id = ''
        self.is_login = False
        self.price_resumed = False
        self.sess = requests.session()
        self.is_reserve_finished = False
        self.has_presale_product = False
        self.has_reserve_product = False
        self.has_oversea_product = False
        self.is_multiple_addr = True
        self.is_marathon_mode = False
        self.is_post_submit_order_failure = False
        self.random_sku = ''
        self.last_func_cost = 0
        self.t_reach_min = 0
        self.order_id = ''
        self.executed_thread_count = 0
        self.bool_map = {
            'True': '是',
            'False': '否'
        }
        self.stock_state_map = {
            '33': '现货',
            '0': '无货',
            '34': '无货',
            '36': '采购中',
            '39': '采购中',
            '40': '可配货'
        }
        self.cache_dao = CacheDao()
        self.login_user_service = LoginUserService()
        self.jd_user_service = JDUserService()
        self.jd_order_service = JDOrderService()
        self._load_cookies()
        self.logger = Logger(login_username).set_logger()

    def _assign_cookies_from_remote(self, cookies):
        cookies = cookies.replace("'","\"")
        remote_cookies = requests.utils.cookiejar_from_dict(json.loads(cookies), cookiejar=None, overwrite=True)
        self.sess.cookies.update(remote_cookies)
        self.is_login = True

    def set_user_props(self, jd_user):
        if 'jd_pwd' in jd_user:
            self.payment_pwd = jd_user['jd_pwd']
        if 'push_token'in jd_user and jd_user['push_email']:
            self.emailer = Emailer(self, jd_user['push_email'], jd_user['push_token'])

    def check_qr_scan_result(self, cookie_token):
        return self.cache_dao.get(cookie_token)

    def cancel_qr_scan(self, cookie_token):
        ret = self.cache_dao.delete(cookie_token+"_running")
        self.log_stream_info('二维码扫描已取消:%s', ret)

    def load_login_cookie(self, login_username, cookie_token):
         # get QR code ticket
        ticket = None
        retry_times = 50
        self.cache_dao.put(cookie_token+"_running", 1)
        try:
            for _ in range(retry_times):
                if self.cache_dao.get(cookie_token+"_running"):
                    ticket = self._get_QRcode_ticket(cookie_token)
                    if ticket:
                        break
                    time.sleep(2)
                else:
                    self.log_stream_info('二维码扫描已取消')
                    return False
            else:
                cache_value_dict = {
                    'success': False,
                    'msg': error_dict['SERVICE']['JD']['QR_EXPIRED']['msg']
                }
                self.cache_dao.put(cookie_token, cache_value_dict)
                return
        except Exception as e:
                self.cache_dao.delete(cookie_token+"_running")
                cache_value_dict = {
                    'success': False,
                    'reasonCode': error_dict['SERVICE']['JD']['QR_INVALID']['reasonCode']
                }
                self.cache_dao.put(cookie_token, cache_value_dict)
                return

        # validate QR code ticket
        if not self._validate_QRcode_ticket(ticket):
            cache_value_dict = {
                'success': False,
                'msg': error_dict['SERVICE']['JD']['QR_INVALID']['msg']
            }
            self.cache_dao.put(cookie_token, cache_value_dict)
            return

        self.is_login = True
        self.nick_name = self.get_user_info()
        self.log_stream_info('二维码登录成功, 用户名:%s', self.nick_name)

        jd_user_data = self.jd_user_service.find_jd_user_by_username_and_nick_name(login_username, self.nick_name, is_mask_jd_pwd=True)

        addr_obj = self.get_user_addr()
        default_addr = self.get_default_addr(addr_obj)

        # update pc login status
        jd_user_data['nick_name'] = self.nick_name
        jd_user_data['recipient_name'] = self.get_recipient_by_default_addr(default_addr)
        jd_user_data['full_addr'] = self.get_full_addr_by_default_addr(default_addr)
        jd_user_data['pc_cookie_status'] = True
        jd_user_data['pc_cookie_str'] =  json_to_str(requests.utils.dict_from_cookiejar(self.sess.cookies))
        jd_user_data['pc_cookie_ts'] =  get_timestamp_in_milli_sec(get_now_datetime())
        jd_user_data['pc_cookie_ts_label'] =  datetime_to_str(get_now_datetime(), format_pattern=DATETIME_STR_PATTERN_SHORT)
        jd_user_data['pc_cookie_expire_ts'] =  get_timestamp_in_milli_sec(datetime_offset_in_milliesec(get_now_datetime(), 24 * 60 * 60 * 1000)) # 24 hours
        jd_user_data['pc_cookie_expire_ts_label'] =  datetime_to_str(datetime_offset_in_milliesec(get_now_datetime(), 24 * 60 * 60 * 1000), format_pattern=DATETIME_STR_PATTERN_SHORT)

        jd_user_data = self.jd_user_service.save_or_update_jd_user(login_username, jd_user_data, is_return_model=False)
        if 'jd_pwd' in jd_user_data and jd_user_data['jd_pwd']:
            jd_user_data['jd_pwd'] = '******'

        cache_value_dict = {
            'success': True,
            'jd_user_data': jd_user_data
        }

        self.cache_dao.put(cookie_token, cache_value_dict)

    def _load_cookies(self):
        try:
            cookies_file = ''
            for name in os.listdir('./cookies'):
                if name.startswith('pc_') and name.endswith('.cookies'):
                    cookies_file = './cookies/{0}'.format(name)
                    break
            with open(cookies_file, 'rb') as f:
                local_cookies = pickle.load(f)
            self.sess.cookies.update(local_cookies)
            self.is_login = self._validate_cookies()
        except Exception as e:
            pass

    def _load_mobile_cookies(self):
        try:
            cookies_file = ''
            for name in os.listdir('./cookies'):
                if name.startswith('m_') and name.endswith('.cookies'):
                    cookies_file = './cookies/{0}'.format(name)
                    break
            with open(cookies_file, 'rb') as f:
                local_cookies = pickle.load(f)
            self.sess.cookies.update(local_cookies)
        except Exception as e:
            pass

    def _save_cookies(self):
        cookies_file = './cookies/pc_{0}.cookies'.format(self.nick_name)
        directory = os.path.dirname(cookies_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(cookies_file, 'wb') as f:
            pickle.dump(self.sess.cookies, f)

    def _save_mobile_cookies(self, mobile_cookies):
        cookies_file = './cookies/m_{0}.cookies'.format(self.nick_name)
        directory = os.path.dirname(cookies_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(cookies_file, 'wb') as f:
            pickle.dump(mobile_cookies, f)

    def _get_user_info_from_cookie(self):
        cookies = self.sess.cookies.get_dict()
        return cookies['user-key'], cookies['jxsid']

    def _validate_cookies(self):
        """验证cookies是否有效（是否登陆）
        通过访问用户订单列表页进行判断：若未登录，将会重定向到登陆页面。
        :return: cookies是否有效 True/False
        """
        url = 'https://order.jd.com/center/list.action'
        payload = {
            'rid': str(int(time.time() * 1000)),
        }
        try:
            resp = self.sess.get(url=url, params=payload, allow_redirects=False)
            if resp.status_code == requests.codes.OK:
                return True
        except Exception as e:
            self.log_stream_error(e)

        return False

    def _get_login_page(self):
        url = "https://passport.jd.com/new/login.aspx"
        page = self.sess.get(url, headers=self.headers)
        return page

    def _get_QRcode(self):
        url = 'https://qr.m.jd.com/show'
        payload = {
            'appid': 133,
            'size': 147,
            't': '',
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://passport.jd.com/new/login.aspx',
        }
        resp = self.sess.get(url=url, headers=headers, params=payload)

        if not response_status(resp):
            self.log_stream_info('获取二维码失败')
            return False

        self.log_stream_info('二维码获取成功，请打开京东APP扫描')

        return resp, self.sess.cookies.get('wlfstk_smdl'), requests.utils.dict_from_cookiejar(self.sess.cookies)

    def _get_QRcode_ticket(self, cookie_token):
        url = 'https://qr.m.jd.com/check'
        payload = {
            'appid': '133',
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            'token': cookie_token,
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://passport.jd.com/new/login.aspx',
        }

        resp = self.sess.get(url=url, headers=headers, params=payload)

        if not response_status(resp):
            self.log_stream_error('获取二维码扫描结果异常')
            return False

        resp_json = parse_json(resp.text)
        if resp_json['code'] != 200:
            self.log_stream_info('Code: %s, Message: %s', resp_json['code'], resp_json['msg'])
            if resp_json['code'] == 257:
                raise RestfulException(error_dict['SERVICE']['JD']['QR_DOWNLOAD_FAILURE'])
            return None
        else:
            self.log_stream_info('已完成手机客户端确认')
            return resp_json['ticket']

    def _validate_QRcode_ticket(self, ticket):
        url = 'https://passport.jd.com/uc/qrCodeTicketValidation'
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://passport.jd.com/uc/login?ltype=logout',
        }
        resp = self.sess.get(url=url, headers=headers, params={'t': ticket})

        if not response_status(resp):
            return False

        resp_json = json.loads(resp.text)
        if resp_json['returnCode'] == 0:
            return True
        else:
            self.log_stream_info(resp_json)
            return False

    def load_QRcode(self):
        self._get_login_page()
        QRcode_resp = self._get_QRcode()
        if not QRcode_resp:
            raise RestfulException(error_dict['SERVICE']['JD']['QR_DOWNLOAD_FAILURE'])

        return QRcode_resp

    def _get_reserve_url(self, sku_id):
        url = 'https://yushou.jd.com/youshouinfo.action'
        payload = {
            'callback': 'fetchJSON',
            'sku': sku_id,
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://item.jd.com/{}.html'.format(sku_id),
        }
        resp = self.sess.get(url=url, params=payload, headers=headers)
        resp_json = parse_json(resp.text)
        # {"type":"1","hasAddress":false,"riskCheck":"0","flag":false,"num":941723,"stime":"2018-10-12 12:40:00","plusEtime":"","qiangEtime":"","showPromoPrice":"0","qiangStime":"","state":2,"sku":100000287121,"info":"\u9884\u7ea6\u8fdb\u884c\u4e2d","isJ":0,"address":"","d":48824,"hidePrice":"0","yueEtime":"2018-10-19 15:01:00","plusStime":"","isBefore":0,"url":"//yushou.jd.com/toYuyue.action?sku=100000287121&key=237af0174f1cffffd227a2f98481a338","etime":"2018-10-19 15:01:00","plusD":48824,"category":"4","plusType":0,"yueStime":"2018-10-12 12:40:00"};
        reserve_url = resp_json.get('url')
        return 'https:' + reserve_url if reserve_url else None

    def make_reserve(self, sku_id):
        """商品预约
        :param sku_id: 商品id
        :return:
        """
        reserve_url = self._get_reserve_url(sku_id)
        if not reserve_url:
            self.log_stream_info('%s 为非预约商品，跳过预约', sku_id)
            return True
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://item.jd.com/{}.html'.format(sku_id),
        }
        resp = self.sess.get(url=reserve_url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        p_tag = soup.find('p', {'class': 'bd-right-result'})
        h3_tag = soup.find('h3', {'class': 'ftx-02'})
        if p_tag:
            reserve_result = soup.find('p', {'class': 'bd-right-result'}).text.strip(' \t\r\n')
            # 预约成功，已获得抢购资格 / 您已成功预约过了，无需重复预约
            self.log_stream_info(reserve_result)
            return True
        elif h3_tag:
            self.log_stream_info('商品已过预约期，继续下单')
            self.is_reserve_finished = True
            return True
        else:
            self.log_stream_info("商品预约失败，需要在app商品页面手动预约后再试")
            if not self.failure_msg:
                self.failure_msg = '商品预约失败，需要在app商品页面手动预约后再试'
                if self.emailer:
                    self.emailer.send(subject='用户' + self.nick_name + '需要手动预约商品再试', content='请在app商品页面手动预约')
            return False

    def get_user_info(self):
        """获取用户信息
        :return: 用户名
        """
        url = 'https://passport.jd.com/user/petName/getUserInfoForMiniJd.action'
        payload = {
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://order.jd.com/center/list.action',
        }
        resp = self.sess.get(url=url, params=payload, headers=headers)
        resp_json = parse_json(resp.text)
        if not resp_json:
            self.is_login = False
            raise RestfulException(error_dict['SERVICE']['JD']['PC_NOT_LOGIN'])
        return resp_json.get('nickName')

    def get_user_info_mobile(self):
        """获取用户信息
        :return: 用户名
        """
        url = 'https://wq.jd.com/pinbind/accountInfo?sceneval=2&g_login_type=1&callback=jsonpCBKA&g_ty=ls'
        headers = {
            'User-Agent': self.mobile_user_agent,
            'referer': 'https://wqs.jd.com/'
        }
        try:
            resp = self.sess.get(url=url, headers=headers)
            resp_json = parse_json(parse_callback_str(resp.text))
            if not resp_json.get('currPinInfo'):
                return False
            return resp_json.get('currPinInfo').get('pin')
        except Exception as e:
            return False

    def check_qq_qr_url_result(self, login_username, nick_name):
        qq_qr_url_result_cache_key = login_username + '_' + nick_name + "_qq_qr_url_result"
        return self.cache_dao.get(qq_qr_url_result_cache_key)

    def check_mobile_qr_result(self, login_username, nick_name):
        qq_qr_scan_result_cache_key = login_username + '_' + nick_name + "_qq_qr_scan_result"
        return self.cache_dao.get(qq_qr_scan_result_cache_key)

    def cancel_qq_qr_result(self, login_username, nick_name):
        mobile_qr_running_cache_key = login_username + '_' + nick_name + "_mobile_qr_running"
        ret = self.cache_dao.delete(mobile_qr_running_cache_key)
        self.log_stream_info('QQ扫码已取消:%s', ret)

    def put_user_input_security(self, login_username, nick_name, security_code):
        mobile_security_input_cache_key = login_username + '_' + nick_name + "_mobile_security_input"
        self.cache_dao.put(mobile_security_input_cache_key, security_code)

    def mobile_login(self, login_username, nick_name):
        driver = None
        qq_qr_url_result_cache_key = login_username + '_' + nick_name + "_qq_qr_url_result"
        qq_qr_scan_result_cache_key = login_username + '_' + nick_name + "_qq_qr_scan_result"
        mobile_qr_running_cache_key = login_username + '_' + nick_name + "_mobile_qr_running"
        mobile_security_input_cache_key = login_username + '_' + nick_name + "_mobile_security_input"
        try:
            self.cache_dao.delete(qq_qr_url_result_cache_key)
            self.cache_dao.delete(qq_qr_scan_result_cache_key)
            self.cache_dao.delete(mobile_qr_running_cache_key)
            self.cache_dao.delete(mobile_security_input_cache_key)
            self.cache_dao.put(mobile_qr_running_cache_key, 1, DEFAULT_CACHE_MOBILE_CODE)
            user_agent = 'Mozilla/5.0 (Windows NT 10.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'
            # user_agent = 'Mozilla/5.0 (Windows NT 8.0; WOW64) AppleWebKit/536.23.38 (KHTML, like Gecko) Chrome/57.0.2740.20 Safari/536.23.38'
            print(user_agent)
            mobile_emulation = {
                                "userAgent": user_agent
                                }
            chrome_options = Options()
            chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_argument("--no-sandbox"); # Bypass OS security model
            if os.name != "nt":
                chrome_options.add_argument('--headless')
            chrome_options.add_argument("--disable-extensions"); #disabling extensions
            chrome_options.add_argument("--disable-gpu"); #applicable to windows os only
            chrome_options.add_argument("--disable-dev-shm-usage"); #overcome limited resource problems
            # chrome_options.add_argument('blink-settings=imagesEnabled=false')
            try:
                driver = webdriver.Chrome(executable_path=os.path.join(os.path.abspath(os.path.dirname(__name__)), self.google_chrome_driver_name), chrome_options=chrome_options)
                self.log_stream_info("chrome driver 加载成功")
            except Exception as e:
                self.log_stream_error(e)
                # retry
                retry_chrome_count = 3
                count = 0
                while True:
                    if driver or (count > retry_chrome_count):
                        self.log_stream_info("chrome driver 加载成功")
                        break
                    else:
                        self.log_stream_info("chrome driver 加载失败, 重试")
                        if driver:
                            driver.quit()
                        time.sleep(3)
                        driver = webdriver.Chrome(executable_path=os.path.join(os.path.abspath(os.path.dirname(__name__)), self.google_chrome_driver_name), chrome_options=chrome_options)
                        count += 1

            if not driver:
                cache_value_dict = {
                    'success': False,
                    'msg': '系统错误'
                }
                self.cache_dao.put(qq_qr_url_result_cache_key, cache_value_dict)
                raise RestfulException(error_dict['SERVICE']['JD']['MOBILE_LOGIN_FAILURE'])
                
            url = 'https://plogin.m.jd.com/login/login?appid=300&returnurl=https%3A%2F%2Fwq.jd.com%2Fpassport%2FLoginRedirect%3Fstate%3D1101471000236%26returnurl%3Dhttps%253A%252F%252Fhome.m.jd.com%252FmyJd%252Fnewhome.action%253Fsceneval%253D2%2526ufc%253D%2526&source=wq_passport'
            driver.get(url)

            policy_checkbox = driver.find_element_by_class_name('policy_tip-checkbox')
            policy_checkbox.click()

            qq_btn = driver.find_element_by_css_selector("a[report-eventid='MLoginRegister_SMSQQLogin']")
            qq_btn.click()

            time.sleep(1)

            driver.switch_to.frame('ptlogin_iframe')
            qr_image = driver.find_element_by_css_selector("img[id='qrlogin_img']")
            encoded = qr_image.screenshot_as_base64

            cache_value_dict = {
                'success': True,
                'src': encoded
            }

            self.cache_dao.put(qq_qr_url_result_cache_key, cache_value_dict, DEFAULT_CACHE_MOBILE_CODE)

            retry_times = 200

            for _ in range(retry_times):
                if self.cache_dao.get(mobile_qr_running_cache_key):
                    current_url = driver.current_url
                    if current_url.startswith('https://wqs.jd.com/') or current_url.startswith('https://m.jd.com/'):
                        break
                    elif current_url.startswith('https://plogin.m.jd.com/'):
                        time.sleep(1)

                        input_retry_times = 50

                        page_title = driver.title

                        if '联合登录' == page_title:
                            try:
                                span_bind_table = driver.find_element_by_css_selector("span[class='bind-lable']")
                                if span_bind_table:
                                    # need bind qq num
                                    self.log_stream_error('QQ账号没有绑定京东，点击关联QQ按钮绑定京东账号')
                                    cache_value_dict = {
                                        'success': False,
                                        'msg': 'QQ账号没有绑定京东，点击关联QQ按钮绑定京东账号'
                                    }
                                    self.cache_dao.put(qq_qr_scan_result_cache_key, cache_value_dict)
                                    self.cache_dao.delete(mobile_security_input_cache_key)
                                    return False
                            except Exception as e:
                                # wait for JD Login PWD input
                                for _ in range(input_retry_times):
                                    # need JD login pwd
                                    cache_value_dict = {
                                        'success': False,
                                        'msg': 'NEED_SECURITY_CODE_PWD'
                                    }
                                    self.cache_dao.put(qq_qr_scan_result_cache_key, cache_value_dict)

                                    if self.cache_dao.get(mobile_qr_running_cache_key):
                                        user_input_security_code = self.cache_dao.get(mobile_security_input_cache_key)
                                        if user_input_security_code:
                                            pwd_input = driver.find_element_by_css_selector("input[id='password']")
                                            pwd_input.send_keys(user_input_security_code)

                                            login_btn = driver.find_element_by_css_selector("a[class='btn active']")
                                            login_btn.click()

                                            time.sleep(1)

                                            error_diag = driver.find_elements_by_class_name("dialog-des")
                                            if error_diag:
                                                msg = error_diag[0].text
                                                self.log_stream_error("获取移动端cookie失败:%s", msg)
                                                cache_value_dict = {
                                                    'success': False,
                                                    'msg': msg
                                                }
                                                self.cache_dao.put(qq_qr_scan_result_cache_key, cache_value_dict)
                                                return False

                                            page_title = driver.title
                                            if '联合登录' == page_title:
                                                cache_value_dict = {
                                                    'success': False,
                                                    'msg': 'SECURITY_CODE_INCORRECT'
                                                }
                                                self.cache_dao.put(qq_qr_scan_result_cache_key, cache_value_dict)
                                                self.cache_dao.delete(mobile_security_input_cache_key)
                                            else:
                                                break
                                    else:
                                        time.sleep(1)
                        elif '认证方式' == page_title:

                            # need mobile code
                            cache_value_dict = {
                                'success': False,
                                'msg': 'NEED_SECURITY_CODE_MOBILE'
                            }
                            self.cache_dao.put(qq_qr_scan_result_cache_key, cache_value_dict)

                            mobile_code_btn = driver.find_element_by_css_selector("a[class='mode-btn voice-mode']")
                            mobile_code_btn.click()

                            time.sleep(1)

                            error_diag = driver.find_elements_by_class_name("dialog-des")
                            if error_diag:
                                msg = error_diag[0].text
                                self.log_stream_error("获取移动端cookie失败:%s", msg)
                                cache_value_dict = {
                                    'success': False,
                                    'msg': msg
                                }
                                self.cache_dao.put(qq_qr_scan_result_cache_key, cache_value_dict)
                                return False
                    
                            try:
                                mobile_code_send_btn = driver.find_element_by_css_selector("button[class='getMsg-btn timer active']")
                                mobile_code_send_btn.click()
                            except Exception as e:
                                self.log_stream_error("获取移动端cookie失败:%s", '获取发送验证码按钮失败')
                                cache_value_dict = {
                                    'success': False,
                                    'msg': '获取发送验证码按钮失败'
                                }
                                print(user_agent)
                                print(driver.page_source)
                                self.cache_dao.put(qq_qr_scan_result_cache_key, cache_value_dict)
                                return False

                            # wait for mobile code input
                            for _ in range(input_retry_times):
                                if self.cache_dao.get(mobile_qr_running_cache_key):
                                    user_input_security_code = self.cache_dao.get(mobile_security_input_cache_key)
                                    if user_input_security_code:
                                        mobile_code_input = driver.find_element_by_css_selector("input[type='tel']")
                                        mobile_code_input.send_keys(user_input_security_code)

                                        login_btn = driver.find_element_by_css_selector("a[class='btn active']")
                                        login_btn.click()

                                        time.sleep(1)

                                        error_diag = driver.find_elements_by_class_name("dialog-des")
                                        if error_diag:
                                            msg = error_diag[0].text
                                            self.log_stream_error("获取移动端cookie失败:%s", msg)
                                            cache_value_dict = {
                                                'success': False,
                                                'msg': msg
                                            }
                                            self.cache_dao.put(qq_qr_scan_result_cache_key, cache_value_dict)
                                            return False

                                        page_title = driver.title
                                        if '认证方式' == page_title:
                                            cache_value_dict = {
                                                'success': False,
                                                'msg': 'SECURITY_CODE_INCORRECT'
                                            }
                                            self.cache_dao.put(qq_qr_scan_result_cache_key, cache_value_dict)
                                            self.cache_dao.delete(mobile_security_input_cache_key)
                                        else:
                                            break
                                    else:
                                        time.sleep(1)
                                else:
                                    self.log_stream_info('手机短信验证码输入已取消')
                                    return False
                            else:
                                self.log_stream_info('手机短信验证码输入已取消')
                                return False
                    time.sleep(1)
                else:
                    self.log_stream_info('QQ扫码已取消')
                    return False
            else:
                self.log_stream_info('QQ扫码已取消')
                return False

            driver.get('https://home.m.jd.com/myJd/newhome.action')

            cookies = driver.get_cookies()

            cookies_dict = []
            for cookie in cookies:
                cookies_dict.append([cookie['name'],cookie['value']])
            cookies_dict = dict(cookies_dict)
            cookie_dict_str = json.dumps(cookies_dict)

            mobile_cookies = requests.utils.cookiejar_from_dict(json.loads(cookie_dict_str), cookiejar=None, overwrite=True)
            self.sess.cookies.update(mobile_cookies)
            
            mobile_nick_name = self.get_user_info_mobile()

            if mobile_nick_name:
                self.log_stream_info("移动端登录成功:%s", mobile_nick_name)
                jd_user_data = self.jd_user_service.find_jd_user_by_username_and_nick_name(login_username, nick_name, is_mask_jd_pwd=True)

                # update pc login status
                jd_user_data['mobile_cookie_status'] = True
                jd_user_data['mobile_cookie_str'] =  json_to_str(requests.utils.dict_from_cookiejar(self.sess.cookies))
                jd_user_data['mobile_cookie_ts'] =  get_timestamp_in_milli_sec(get_now_datetime())
                jd_user_data['mobile_cookie_ts_label'] =  datetime_to_str(get_now_datetime(), format_pattern=DATETIME_STR_PATTERN_SHORT)
                jd_user_data['mobile_cookie_expire_ts'] =  get_timestamp_in_milli_sec(datetime_offset_in_milliesec(get_now_datetime(), 30 * 24 * 60 * 60 * 1000)) # 30 days
                jd_user_data['mobile_cookie_expire_ts_label'] =  datetime_to_str(datetime_offset_in_milliesec(get_now_datetime(), 30 * 24 * 60 * 60 * 1000), format_pattern=DATETIME_STR_PATTERN_SHORT)

                jd_user_data = self.jd_user_service.save_or_update_jd_user(login_username, jd_user_data, is_return_model=False)
                if 'jd_pwd' in jd_user_data and jd_user_data['jd_pwd']:
                    jd_user_data['jd_pwd'] = '******'

                cache_value_dict = {
                    'success': True,
                    'jd_user_data': jd_user_data
                }
                self.cache_dao.put(qq_qr_scan_result_cache_key, cache_value_dict)
            else:
                self.log_stream_info("移动端登录失败")
                cache_value_dict = {
                    'success': False,
                    'msg': error_dict['SERVICE']['JD']['MOBILE_QR_ERROR']['msg']
                }
                self.cache_dao.put(qq_qr_scan_result_cache_key, cache_value_dict)
        except Exception as e:
            self.log_stream_error(e)
            cache_value_dict = {
                'success': False,
                'msg': '系统错误'
            }
            self.cache_dao.put(qq_qr_url_result_cache_key, cache_value_dict)
            raise RestfulException(error_dict['SERVICE']['JD']['MOBILE_LOGIN_FAILURE'])
        finally:
            self.cache_dao.delete(mobile_qr_running_cache_key)
            if driver:
                driver.quit()

    def _get_item_detail_page(self, sku_id):
        """访问商品详情页
        :param sku_id: 商品id
        :return: 响应
        """
        url = 'https://item.jd.com/{}.html'.format(sku_id)
        page = requests.get(url=url, headers=self.headers)
        return page

    def get_single_item_stock(self, sku_id):
        """获取单个商品库存状态
        :param sku_id: 商品id
        :param num: 商品数量
        :return: 商品是否有货 True/False
        """

        self.log_stream_info('查询库存公共接口')

        url = 'http://c0.3.cn/stocks'
        payload = {
            'type': 'getstocks',
            'skuIds': sku_id,
            'area': self.area_id,
            '_': str(int(time.time() * 1000))
        }

        headers = {
            'User-Agent': self.user_agent,
            'Host': 'c0.3.cn'
        }
        
        resp_text = ''
        try:
            resp_text = self.sess.get(url=url, params=payload, headers=headers).text
            resp_json = parse_json(resp_text)

            if 'err' in resp_json[sku_id] and resp_json[sku_id]['err']:
                self.log_stream_error('查询 %s 库存信息发生异常, resp: %s', sku_id, resp_text)
                raise RestfulException(error_dict['SERVICE']['JD']['STOCK_API_LIMITED'])

            sku_state = resp_json[sku_id].get('skuState')  # 商品是否上架
            stock_state = resp_json[sku_id].get('StockState')  # 商品库存状态：33 -- 现货  0,34 -- 无货  36 -- 采购中  40 -- 可配货
            if stock_state == 33 or stock_state == 36 or stock_state == 40:
                self.log_stream_info('===============================发现库存===========================================')
            self.log_stream_info('库存状态: %s', self.stock_state_map[str(stock_state)])
            return sku_state == 1 and stock_state in (33, 36, 40)
        except requests.exceptions.Timeout:
            self.log_stream_error('查询 %s 库存信息超时(%ss)', sku_id, self.timeout)
            return False
        except requests.exceptions.RequestException as request_exception:
            self.log_stream_error('查询 %s 库存信息发生网络请求异常：%s', sku_id, request_exception)
            return False
        except Exception as e:
            self.log_stream_error('查询 %s 库存信息发生异常, resp: %s, exception: %s', sku_id, resp_text, e)
            raise e

    def get_single_item_stock_type_one(self, sku_id):
        """获取单个商品库存状态
        :param sku_id: 商品id
        :param num: 商品数量
        :return: 商品是否有货 True/False
        """

        self.log_stream_info('查询库存type one')

        url = 'https://cd.jd.com/stocks'
        payload = {
            'type': 'getstocks',
            'skuIds': sku_id,
            'area': self.area_id,
            '_': str(int(time.time() * 1000))
        }

        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://item.jd.com/',
            'Host': 'cd.jd.com'
        }
        
        resp_text = ''
        try:
            resp_text = self.sess.get(url=url, params=payload, headers=headers).text
            resp_json = parse_json(resp_text)

            if 'err' in resp_json[sku_id] and resp_json[sku_id]['err']:
                self.log_stream_error('查询 %s 库存信息发生异常, resp: %s', sku_id, resp_text)
                raise RestfulException(error_dict['SERVICE']['JD']['STOCK_API_LIMITED'])

            sku_state = resp_json[sku_id].get('skuState')  # 商品是否上架
            stock_state = resp_json[sku_id].get('StockState')  # 商品库存状态：33 -- 现货  0,34 -- 无货  36 -- 采购中  40 -- 可配货
            if sku_state == 1 and stock_state in (33, 36, 40):
                self.log_stream_info('===============================发现库存===========================================')
            self.log_stream_info('库存状态: %s', self.stock_state_map[str(stock_state)])
            return sku_state == 1 and stock_state in (33, 36, 40)
        except requests.exceptions.Timeout:
            self.log_stream_error('查询 %s 库存信息超时(%ss)', sku_id, self.timeout)
            return False
        except requests.exceptions.RequestException as request_exception:
            self.log_stream_error('查询 %s 库存信息发生网络请求异常：%s', sku_id, request_exception)
            return False
        except Exception as e:
            self.log_stream_error('查询 %s 库存信息发生异常, resp: %s, exception: %s', sku_id, resp_text, e)
            raise e
    
    def get_single_item_stock_type_two(self, sku_id):
        """获取单个商品库存状态
        :param sku_id: 商品id
        :param num: 商品数量
        :return: 商品是否有货 True/False
        """

        self.log_stream_info('查询库存type two')

        url = 'https://api.m.jd.com/api'
        payload = {
            'callback': '',
            'appid': 'JDC_mall_cart',
            'functionId': 'pcCart_jc_getCurrentCart',
            'body': json_to_str({"serInfo":{"area":self.area_id,"user-key":self.user_id},"cartExt":{"specialId":1}})
        }

        headers = {
            'User-Agent': self.user_agent,
            'origin': 'https://cart.jd.com/',
            'Referer': 'https://cart.jd.com/'
        }
        
        resp_text = ''
        try:
            resp_text = self.sess.post(url=url, data=payload, headers=headers).text
            resp_json = parse_json(resp_text)

            stock_info = {}

            if not 'cartInfo' in resp_json['resultData'] or not resp_json['resultData']['cartInfo'] or 'vendors' not in resp_json['resultData']['cartInfo']:
                return False
            elif 'unusableSkus' in resp_json['resultData']['cartInfo'] and resp_json['resultData']['cartInfo']['unusableSkus']:
                return False

            for vendor in resp_json['resultData']['cartInfo']['vendors']:
                for sorted in vendor['sorted']:
                    if 'items' in sorted['item'] and len(sorted['item']['items']) > 0:
                        items = sorted['item']['items']
                        for item in items:
                            if item['item']['Id'] == str(sku_id):
                                stock_info = item['item']['stock']
                                break
                    else:
                        item = sorted['item']
                        if item['Id'] == str(sku_id):
                                stock_info = item['stock']
                                break

            sku_state = stock_info.get('stockCode')  # 商品是否上架
            stock_state = stock_info.get('stockStateId')  # 商品库存状态：33 -- 现货  0,34 -- 无货  36 -- 采购中  40 -- 可配货
            flag = sku_state == 0 and stock_state in (33, 36, 40)
            if flag:
                self.log_stream_info('===============================发现库存===========================================')
            else:
                self.create_temp_order()
            self.log_stream_info('库存状态: %s', self.stock_state_map[str(stock_state)])
            return flag
        except requests.exceptions.Timeout:
            self.log_stream_error('查询 %s 库存信息超时(%ss)', sku_id, self.timeout)
            return False
        except requests.exceptions.RequestException as request_exception:
            self.log_stream_error('查询 %s 库存信息发生网络请求异常：%s', sku_id, request_exception)
            return False
        except Exception as e:
            self.log_stream_error('查询 %s 库存信息发生异常, resp: %s, exception: %s', sku_id, resp_text, e)
            raise RestfulException(error_dict['SERVICE']['JD']['STOCK_API_LIMITED'])

    def _if_item_removed(self, sku_id):
        """判断商品是否下架
        :param sku_id: 商品id
        :return: 商品是否下架 True/False
        """
        detail_page = self._get_item_detail_page(sku_id=sku_id)
        return '该商品已下柜' in detail_page.text

    def if_item_can_be_ordered(self, round, is_random_check_stock):
        sku_id = self.target_sku_id
        flag = False
        should_reduce_interval = False

        # try:
        #     flag = self.get_single_item_stock(sku_id)
        #     return flag
        # except Exception as e:
        #     self.log_stream_error(e)
        #     self.log_stream_info('公共查询库存api触发流量限制')

        if is_random_check_stock:
            if round % 2 == 0:
                flag = self.get_single_item_stock_type_one(sku_id)
            else:
                flag = self.get_single_item_stock_type_two(sku_id)
                if not flag:
                    should_reduce_interval = True
        else:
            flag = self.get_single_item_stock_type_one(sku_id)

        return flag, should_reduce_interval

    def get_item_price(self, sku_id):
        """获取商品价格
        :param sku_id: 商品id
        :return: 价格
        """
        url = 'http://p.3.cn/prices/mgets'
        payload = {
            'type': 1,
            'pduid': int(time.time() * 1000),
            'skuIds': 'J_' + sku_id,
        }
        resp = self.sess.get(url=url, params=payload)
        return parse_json(resp.text).get('p')

    @fetch_latency
    def add_item_to_cart(self, sku_id, num):
        """添加商品到购物车

        重要：
        1.商品添加到购物车后将会自动被勾选✓中。
        2.在提交订单时会对勾选的商品进行结算。
        3.部分商品（如预售、下架等）无法添加到购物车

        京东购物车可容纳的最大商品种数约为118-120种，超过数量会加入购物车失败。

        :param sku_id: 商品id
        :return:
        """
        url = 'https://cart.jd.com/gate.action'
        headers = {
            'User-Agent': self.user_agent,
            'referer': 'https://item.jd.com/'
        }

        payload = {
            'pid': sku_id,
            'pcount': num,
            'ptype': 1,
        }

        result = False

        resp = self.sess.get(url=url, params=payload, headers=headers)
        if 'https://cart.jd.com/cart.action' in resp.url:  # 套装商品加入购物车后直接跳转到购物车页面
            result = True
        else:  # 普通商品成功加入购物车后会跳转到提示 "商品已成功加入购物车！" 页面
            soup = BeautifulSoup(resp.text, "html.parser")
            if '京东购物车-加购成功页' == soup.title.string:
                result = True
            else:
                result = bool(soup.select('h3.ftx-02'))  # [<h3 class="ftx-02">商品已成功加入购物车！</h3>]

        if result:
            self.log_stream_info('%s x %s 已成功加入购物车', sku_id, num)
            return True
        else:
            self.log_stream_error('%s 添加到购物车失败', sku_id)
            return False

    def clear_cart(self):
        """清空购物车 

        :return: 清空购物车结果 True/False
        """
        # 1.select product  2.remove product 
        url = 'https://cart.jd.com/quickDel.action'
        data_select = {
            'method': 'get',
            '_': str(int(time.time() * 1000)),
        }

        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://cart.jd.com/cart_index',
        }

        try:
            select_resp = self.sess.get(url=url, params=data_select, headers=headers)

            del_body = []
            id_array = parse_cart_item_array(select_resp.text)

            if 'cart' in select_resp.text:
                for item in id_array:
                    del_body.append('{id:sku_id,s:false,vs:false}'.replace("sku_id",item))
                
                del_body = str(del_body).replace("'","")

                data_delete = {
                    'method': 'del',
                    'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
                    '_': str(int(time.time() * 1000)),
                    'delParam': del_body
                }
                
                remove_resp = self.sess.get(url=url, params=data_delete, headers=headers)
                if (not response_status(select_resp)) or (not response_status(remove_resp)):
                    self.log_stream_error('购物车清空失败')
                    return False
                self.log_stream_info('购物车清空成功, 清除商品%s', str(id_array))
            else:
                self.log_stream_info('购物车没有商品，不需要清空')
            return True
        except Exception as e:
            logging.exception("error")
            self.log_stream_error(e)
            return False

    @fetch_latency
    def remove_sku_from_cart(self, sku_id):

        url = 'https://cart.jd.com/quickDel.action'

        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://cart.jd.com/cart_index',
        }

        try:
            del_body = []
            del_body.append('{id:sku_id,s:false,vs:false}'.replace("sku_id",sku_id))

            del_body = str(del_body).replace("'","")

            data_delete = {
                'method': 'del',
                'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
                '_': str(int(time.time() * 1000)),
                'delParam': del_body
            }
            remove_resp = self.sess.get(url=url, params=data_delete, headers=headers)
            if not response_status(remove_resp):
                self.log_stream_error('购物车清空失败')
                return False
            self.log_stream_info('购物车清空成功, 清除商品%s', sku_id)
            return True
        except Exception as e:
            logging.exception("error")
            self.log_stream_error(e)
            return False

    def get_cart_detail(self):
        """获取购物车商品详情
        :return: 购物车商品信息 dict
        """
        url = 'https://cart.jd.com/cart.action'
        resp = self.sess.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        cart_detail = dict()
        for item in soup.find_all(class_='item-item'):
            try:
                sku_id = item['skuid']  # 商品id
                # 例如：['increment', '8888', '100001071956', '1', '13', '0', '50067652554']
                # ['increment', '8888', '100002404322', '2', '1', '0']
                item_attr_list = item.find(class_='increment')['id'].split('_')
                p_type = item_attr_list[4]
                promo_id = target_id = item_attr_list[-1] if len(item_attr_list) == 7 else 0

                cart_detail[sku_id] = {
                    'name': get_tag_value(item.select('div.p-name a')),  # 商品名称
                    'verder_id': item['venderid'],  # 商家id
                    'count': int(item['num']),  # 数量
                    'unit_price': get_tag_value(item.select('div.p-price strong'))[1:],  # 单价
                    'total_price': get_tag_value(item.select('div.p-sum strong'))[1:],  # 总价
                    'is_selected': 'item-selected' in item['class'],  # 商品是否被勾选
                    'p_type': p_type,
                    'target_id': target_id,
                    'promo_id': promo_id
                }
            except Exception as e:
                self.log_stream_error("某商品在购物车中的信息无法解析，报错信息: %s，该商品自动忽略。 %s", e, item)

        self.log_stream_info('购物车信息：%s', cart_detail)
        return cart_detail
    
    def get_third_party_vendor_random_sku_uuid(self, sku_id):
        area_id = parse_area_id(self.area_id)

        url = 'https://api.m.jd.com/api'
        payload = {
            'callback': '',
            'appid': 'JDC_mall_cart',
            'functionId': 'pcCart_jc_getCurrentCart',
            'body': json_to_str({"serInfo":{"area":area_id,"user-key":self.user_id},"cartExt":{"specialId":1}})
        }

        headers = {
            'User-Agent': self.user_agent,
            'origin': 'https://cart.jd.com/',
            'Referer': 'https://cart.jd.com/'
        }
        
        resp_text = ''
        try:
            resp_text = self.sess.post(url=url, data=payload, headers=headers).text
            resp_json = parse_json(resp_text)

            if not 'cartInfo' in resp_json['resultData'] or not resp_json['resultData']['cartInfo'] or 'vendors' not in resp_json['resultData']['cartInfo']:
                return False
            elif 'unusableSkus' in resp_json['resultData']['cartInfo'] and resp_json['resultData']['cartInfo']['unusableSkus']:
                return False

            for vendor in resp_json['resultData']['cartInfo']['vendors']:
                for sorted in vendor['sorted']:
                    if 'items' in sorted['item'] and len(sorted['item']['items']) > 0:
                        items = sorted['item']['items']
                        for item in items:
                            if item['item']['Id'] == str(sku_id):
                                self.sku_uuid = item['item']['skuUuid']
                                return self.sku_uuid
                    else:
                        item = sorted['item']
                        if item['Id'] == str(sku_id):
                            self.sku_uuid = item['skuUuid']
                            return self.sku_uuid
        except Exception as e:
            self.log_stream_error('查询 %s sku_uuid发生异常, resp: %s, exception: %s', sku_id, resp_text, e)
            traceback.print_exc()

    @fetch_latency
    def cancel_select_sku(self, sku_id, num):
        area_id = parse_area_id(self.area_id)

        url = 'https://api.m.jd.com/api'
        payload = {
            'appid': 'JDC_mall_cart',
            'functionId': 'pcCart_jc_cartUnCheckSingle',
            'body': json_to_str({"operations":[{"TheSkus":[{"Id":sku_id,"num":num,"skuUuid":self.sku_uuid,"useUuid":'false'}]}],"serInfo":{"area":area_id,"user-key":self.user_id}})
        }

        headers = {
            'User-Agent': self.user_agent,
            'origin': 'https://cart.jd.com/',
            'Referer': 'https://cart.jd.com/'
        }
        
        resp_text = ''
        try:
            resp_text = self.sess.post(url=url, data=payload, headers=headers).text
            resp_json = parse_json(resp_text)
            return resp_json['success']
        except Exception as e:
            self.log_stream_error('取消勾选 %s 发生异常, resp: %s, exception: %s', sku_id, resp_text, e)
            traceback.print_exc()

    @fetch_latency
    def _cancel_select_all_cart_item(self):
        """取消勾选购物车中的所有商品
        :return: 取消勾选结果 True/False
        """
        url = "https://cart.jd.com/cancelAllItem.action"
        data = {
            't': 0,
            'outSkus': '',
            'random': random.random()
            # 'locationId' can be ignored
        }
        resp = self.sess.post(url, data=data)
        return response_status(resp)

    @fetch_latency
    def select_all_cart_item(self, is_multi_thread=False):
        try:
            url = "https://cart.jd.com/selectAllItem.action"
            data = {
                't': 0,
                'outSkus': '',
                'random': random.random()
                # 'locationId' can be ignored
            }
            resp_text = self.sess.post(url, data=data).text

            modifyResult = json.loads(resp_text)['sortedWebCartResult']['modifyResult']
            if 'allCount' not in modifyResult or 'selectedCount' not in modifyResult :
                self.log_stream_info('购物车信息出错')
                return False
            else:
                if modifyResult['allCount'] == 0:
                    self.log_stream_info('购物车商品已被删除，重新添加')
                    self.create_temp_order(is_add_cart_item=True)
                    return True
            self.is_ready_place_order = modifyResult['selectedCount'] == modifyResult['allCount']
            if self.is_ready_place_order:
                self.log_stream_info('完成购物车选中') 
            else:
                self.log_stream_info('购物车选中失败') 

            price_resumed = float(modifyResult['finalPrice']) > self.order_price_threshold
            if price_resumed:
                self.price_resumed = True
                self.log_stream_info('购物车价格已恢复原价, 当前价格:%s, 下单价格阈值: %s', float(modifyResult['finalPrice']), self.order_price_threshold) 

            return price_resumed
        except Exception as e:
            self.log_stream_error('选中购物车发生异常, resp: %s, exception: %s', resp_text, e)
            return False
        finally:
            if is_multi_thread:
                self.executed_thread_count += 1

    def wait_for_cart_operation(self):
        select_cart_count = 4
        count = 0
        while True:
            if self.is_ready_place_order or (count > select_cart_count):
                break
            else:
                self.select_all_cart_item()
                count += 1

    def _change_item_num_in_cart(self, sku_id, vender_id, num, p_type, target_id, promo_id):
        """修改购物车商品的数量
        修改购物车中商品数量后，该商品将会被自动勾选上。

        :param sku_id: 商品id
        :param vender_id: 商家id
        :param num: 目标数量
        :param p_type: 商品类型(可能)
        :param target_id: 参数用途未知，可能是用户判断优惠
        :param promo_id: 参数用途未知，可能是用户判断优惠
        :return: 商品数量修改结果 True/False
        """
        url = "https://cart.jd.com/changeNum.action"
        data = {
            't': 0,
            'venderId': vender_id,
            'pid': sku_id,
            'pcount': num,
            'ptype': p_type,
            'targetId': target_id,
            'promoID': promo_id,
            'outSkus': '',
            'random': random.random(),
            # 'locationId'
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://cart.jd.com/cart',
        }
        resp = self.sess.post(url, data=data, headers=headers)
        return json.loads(resp.text)['sortedWebCartResult']['achieveSevenState'] == 2

    def _add_or_change_cart_item(self, cart, sku_id, count):
        """添加商品到购物车，或修改购物车中商品数量

        如果购物车中存在该商品，会修改该商品的数量并勾选；否则，会添加该商品到购物车中并勾选。

        :param cart: 购物车信息 dict
        :param sku_id: 商品id
        :param count: 商品数量
        :return: 运行结果 True/False
        """
        if sku_id in cart:
            self.log_stream_info('%s 已在购物车中，调整数量为 %s', sku_id, count)
            cart_item = cart.get(sku_id)
            return self._change_item_num_in_cart(
                sku_id=sku_id,
                vender_id=cart_item.get('vender_id'),
                num=count,
                p_type=cart_item.get('p_type'),
                target_id=cart_item.get('target_id'),
                promo_id=cart_item.get('promo_id')
            )
        else:
            self.log_stream_info('%s 不在购物车中，开始加入购物车，数量 %s', sku_id, count)
            return self.add_item_to_cart(sku_id, count)

    @fetch_latency
    def get_checkout_page_detail(self):
        """获取订单结算页面信息

        该方法会返回订单结算页面的详细信息：商品名称、价格、数量、库存状态等。

        :return: 结算信息 dict
        """
        url = 'http://trade.jd.com/shopping/order/getOrderInfo.action'

        payload = {
            'rid': str(int(time.time() * 1000))
        }

        try:
            resp = self.sess.get(url=url, params=payload)

            if not response_status(resp):
                self.log_stream_error('获取订单结算页信息失败')
                return
            soup = BeautifulSoup(resp.text, "html.parser")

            self.risk_control = get_tag_value(soup.select('input#riskControl'), 'value')

            return self.risk_control
        except Exception as e:
            logging.exception("error")
            self.log_stream_error('订单结算页面数据解析异常（可以忽略），报错信息：%s', e)

    @fetch_latency
    def _save_invoice(self):
        """下单第三方商品时如果未设置发票，将从电子发票切换为普通发票

        http://jos.jd.com/api/complexTemplate.htm?webPamer=invoice&groupName=%E5%BC%80%E6%99%AE%E5%8B%92%E5%85%A5%E9%A9%BB%E6%A8%A1%E5%BC%8FAPI&id=566&restName=jd.kepler.trade.submit&isMulti=true

        :return:
        """
        url = 'https://trade.jd.com/shopping/dynamic/invoice/saveInvoice.action'
        data = {
            "invoiceParam.selectedInvoiceType": 1,
            "invoiceParam.companyName": "个人",
            "invoiceParam.invoicePutType": 0,
            "invoiceParam.selectInvoiceTitle": 4,
            "invoiceParam.selectBookInvoiceContent": "",
            "invoiceParam.selectNormalInvoiceContent": 1,
            "invoiceParam.vatCompanyName": "",
            "invoiceParam.code": "",
            "invoiceParam.regAddr": "",
            "invoiceParam.regPhone": "",
            "invoiceParam.regBank": "",
            "invoiceParam.regBankAccount": "",
            "invoiceParam.hasCommon": "true",
            "invoiceParam.hasBook": "false",
            "invoiceParam.consigneeName": "",
            "invoiceParam.consigneePhone": "",
            "invoiceParam.consigneeAddress": "",
            "invoiceParam.consigneeProvince": "请选择：",
            "invoiceParam.consigneeProvinceId": "NaN",
            "invoiceParam.consigneeCity": "请选择",
            "invoiceParam.consigneeCityId": "NaN",
            "invoiceParam.consigneeCounty": "请选择",
            "invoiceParam.consigneeCountyId": "NaN",
            "invoiceParam.consigneeTown": "请选择",
            "invoiceParam.consigneeTownId": 0,
            "invoiceParam.sendSeparate": "false",
            "invoiceParam.usualInvoiceId": "",
            "invoiceParam.selectElectroTitle": 4,
            "invoiceParam.electroCompanyName": "undefined",
            "invoiceParam.electroInvoiceEmail": "",
            "invoiceParam.electroInvoicePhone": "",
            "invokeInvoiceBasicService": "true",
            "invoice_ceshi1": "",
            "invoiceParam.showInvoiceSeparate": "false",
            "invoiceParam.invoiceSeparateSwitch": 1,
            "invoiceParam.invoiceCode": "",
            "invoiceParam.saveInvoiceFlag": 1
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://trade.jd.com/shopping/dynamic/invoice/saveInvoice.action',
        }

        self.sess.post(url=url, data=data, headers=headers)
        resp = self.sess.post(url=url, data=data, headers=headers)

    @fetch_latency
    def _update_order_invoice(self):
        """添加购物车后更新默认地址为订单发货地址
        """
        self.log_stream_info("更新默认地址为订单发货地址")
        try:
            url = 'https://trade.jd.com/shopping/dynamic/consignee/saveConsignee.action'
            data = {
                'consigneeParam.newId': self.area_ref_id,
                'consigneeParam.type': 'null',
                'consigneeParam.commonConsigneeSize': 13,
                'consigneeParam.isUpdateCommonAddress': 0,
                'consigneeParam.giftSenderConsigneeName': '',
                'consigneeParam.giftSendeConsigneeMobile': '',
                'consigneeParam.noteGiftSender': 'false',
                'consigneeParam.isSelfPick': 0,
                'consigneeParam.selfPickOptimize': 0,
                'consigneeParam.pickType': 0
            }

            headers = {
                'User-Agent': self.user_agent,
                'Referer': 'http://trade.jd.com/shopping/order/getOrderInfo.action',
                'content-type': 'application/x-www-form-urlencoded',
                'Host': 'trade.jd.com'
            }

            self.sess.post(url=url, data=data, headers=headers)
            resp = self.sess.post(url=url, data=data, headers=headers)
        except Exception as e:
            self.log_stream_error('更新默认地址为订单发货地址失败：%s', str(e))
            raise RestfulException(error_dict['SERVICE']['JD']['MOBILE_LOGIN_FAILURE'])

    def get_user_addr(self):

        url = 'https://cd.jd.com/usual/address'
        payload = {
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://item.jd.com/',
        }

        resp = self.sess.get(url=url, headers=headers, params=payload)
        resp_json = parse_original_json(str_remove_newline(parse_callback_str(resp.text)))
        return resp_json

    def set_user_default_address(self, address_id):

        url = 'https://easybuy.jd.com/address/setAddressAllDefaultById.action'
        data = {
            'addressId': address_id
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://easybuy.jd.com/address/getEasyBuyList.action',
            'Origin':'https://easybuy.jd.com'
        }

        resp = self.sess.post(url=url, headers=headers, data=data)
        if not response_status(resp):
            return False
        return True

    def is_has_multiple_addr(self, addr_json):
        if len(addr_json) > 1:
           return True
        else:
           return False

    def get_area_id_by_default_addr(self, default_addr):
       return str(default_addr['provinceId']) + "_" + str(default_addr['cityId']) + "_" + str(default_addr['countyId']) + "_" + str(default_addr['townId'])

    def get_area_ref_id_by_default_addr(self, default_addr):
       return default_addr['id']

    def get_full_addr_by_default_addr(self, default_addr):
       return default_addr['fullAddress']

    def get_mobile_by_default_addr(self, default_addr):
       return default_addr['mobile']

    def get_recipient_by_default_addr(self, default_addr):
       return default_addr['name']

    def get_default_addr(self, addr_json):
        for item in addr_json:
            if item['addressDefault']:
                return item
        return addr_json[0]

    @fetch_latency
    def cancel_order(self, order_id):

        """取消订单

        :return: True/False 订单取消结果
        """

        # 获取订单passkey
        url = 'https://orderop.jd.com/toolbar_showCancelButtonListNew'

        headers = {
            'User-Agent': self.user_agent
        }

        payload = {
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            'orderList': order_id,
            'orderid': order_id,
            '_': str(int(time.time() * 1000)),
        }

        resp = self.sess.get(url=url, params=payload, headers=headers)
        try:
            resp_json = parse_original_json(str_remove_newline(parse_callback_str(resp.text)))

            if not resp_json:
                self.log_stream_info('未发现订单%s或已取消', order_id)
                return False, "未发现订单或已取消"
            else:
                passkey = resp_json[0]['passKey']

                # 取消订单
                url = 'https://orderop.jd.com/toolbar_cancelOrder'

                headers = {
                    'User-Agent': self.user_agent
                }

                payload = {
                    'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
                    'action': 'cancelOrder',
                    'cancelData': '{"cancelReasonId":1013}',
                    'orderid': order_id,
                    'key': passkey,
                    '_': str(int(time.time() * 1000)),
                }

                resp = self.sess.get(url=url, params=payload, headers=headers)

                if not response_status(resp):
                    self.log_stream_error('订单取消失败')
                    return False, "订单取消失败"
                else:
                    self.log_stream_info('订单取消成功')
                    return True, "订单取消成功"
        except Exception as e:
            self.log_stream_info('未发现订单%s或已取消', order_id)
            return False, "未发现订单或已取消"

    def get_order_info(self, silent=False):
        """查询订单信息
        :param unpaid: 只显示未付款订单，可选参数，默认为True
        :return:
        """
        url = 'https://order.jd.com/center/list.action'
        payload = {
            'search': 0,
            'd': 1,
            's': 4096,
        }  # Orders for nearly three months
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://passport.jd.com/uc/login?ltype=logout',
        }

        try:
            resp = self.sess.get(url=url, params=payload, headers=headers)
            if not response_status(resp):
                self.log_stream_error('获取订单页信息失败')
                return
            soup = BeautifulSoup(resp.text, "html.parser")

            order_table = soup.find('table', {'class': 'order-tb'})
            table_bodies = order_table.select('tbody')
            exist_order = False
            order_list = []
            for table_body in table_bodies:
                # get order status
                order_status = get_tag_value(table_body.select('span.order-status')).replace("订单状态：", "")

                # check if order is waiting for payment
                # wait_payment = bool(table_body.select('a.btn-pay'))
                wait_payment = "等待付款" in order_status

                # only show unpaid orders if unpaid=True
                unpaid = True
                if unpaid and (not wait_payment):
                    continue

                exist_order = True

                # get order_time, order_id
                tr_th = table_body.select('tr.tr-th')[0]
                order_time = get_tag_value(tr_th.select('span.dealtime'))
                order_id = get_tag_value(tr_th.select('span.number a'))

                # get sum_price, pay_method
                sum_price = ''
                pay_method = ''
                amount_div = table_body.find('div', {'class': 'amount'})
                if amount_div:
                    spans = amount_div.select('span')
                    # pay_method = get_tag_value(spans, index=1)
                    # if the order is waiting for payment, the price after the discount is shown.
                    sum_price = get_tag_value(amount_div.select('strong'), index=1)[1:] if wait_payment \
                        else get_tag_value(spans, index=0)[4:]

                # get name and quantity of items in order
                item_info_array = [] 
                tr_bds = table_body.select('tr.tr-bd')
                for tr_bd in tr_bds:
                    item = tr_bd.find('div', {'class': 'goods-item'})
                    if not item:
                        break
                    item_id = item.get('class')[1][2:]
                    quantity = get_tag_value(tr_bd.select('div.goods-number'))[1:]


                    item_info = {}
                    item_info['sku_id'] = item_id
                    item_info['quantity'] = quantity

                    children_name = item.findChildren("a", {'class': 'a-link'} , recursive=True)
                    for child in children_name:
                        item_info['name'] = child.text

                    children_img = item.findChildren("img", {'class': 'err-product'} , recursive=True)
                    for child in children_img:
                        item_info['image'] = "https:"+child['data-lazy-img'].replace('s60x60','s240x240')

                    item_info_array.append(item_info)

                # get address
                address_element = list(soup.find('div', {'class': 'pc'}).children)
                addr_name = address_element[1].text
                addr = address_element[3].text

                if not silent:
                    self.log_stream_info('======================================================订单信息==================================================================')
                    order_info_format = '下单时间:{0}----订单号:{1}----订单状态:{2}----总金额:{3}元----地址:{4}--{5}'
                    self.log_stream_info(order_info_format.format(order_time, order_id, order_status,
                                                        sum_price, addr_name, addr))
                    for item_info in item_info_array:
                        item_info_format = '商品数量:{0}----商品名称:{1}'
                        self.log_stream_info(item_info_format.format(item_info['quantity'], item_info['name']))
                    self.log_stream_info('======================================================订单信息==================================================================')

                order_info = {
                    'order_time': order_time,
                    'order_id': order_id,
                    'order_status': order_status,
                    'sum_price':sum_price,
                    'addr_name':addr_name,
                    'addr':addr,
                    'item_info_array':item_info_array
                }
                order_list.append(order_info)

            if not exist_order:
                self.log_stream_info('订单查询为空')
            
            return order_list
        except Exception as e:
            logging.exception("error")
            self.log_stream_error(e)

    @fetch_latency
    def submit_order(self, is_multi_thread, ins, thread_index, is_fake=False):
        """提交订单

        重要：
        1.该方法只适用于普通商品的提交订单（即可以加入购物车，然后结算提交订单的商品）
        2.提交订单时，会对购物车中勾选✓的商品进行结算（如果勾选了多个商品，将会提交成一个订单）

        :return: True/False 订单提交结果
        """
        url = 'https://trade.jd.com/shopping/order/submitOrder.action?&presaleStockSign=1'
        # js function of submit order is included in https://trade.jd.com/shopping/misc/js/order.js?r=2018070403091

        data = {
            'overseaPurchaseCookies': '',
            'vendorRemarks': '[]',
            'submitOrderParam.sopNotPutInvoice': 'true',
            'submitOrderParam.trackID': self.track_id,
            'submitOrderParam.ignorePriceChange': 0,
            'submitOrderParam.btSupport': 0,
            'riskControl': self.risk_control,
            'submitOrderParam.isBestCoupon': 1,
            'submitOrderParam.jxj': 1,
            'submitOrderParam.eid': self.eid,
            'submitOrderParam.fp': self.fp,
            'submitOrderParam.needCheck': 1,
            'presaleStockSign': 1
        }

        if self.has_presale_product: 
            data['submitOrderParam.presalePayType'] = 2
            data['flowType'] = 15
            data['preSalePaymentTypeInOptional'] = 2
            data['submitOrderParam.payType4YuShou'] = 2

        if self.has_oversea_product:
            data['overseaMerge'] = 1

        # add payment password when necessary
        if self.payment_pwd:
            data['submitOrderParam.payPassword'] = encrypt_payment_pwd(self.payment_pwd)

        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action?rid=' + str(int(time.time() * 1000)),
            'Host': 'trade.jd.com',
            'origin': 'https://trade.jd.com'
        }

        try:
            should_stop = False
            if is_multi_thread:
                self.log_stream_info('线程[%s]开始提交订单',thread_index)

            resp = self.sess.post(url=url, data=data, headers=headers)
            resp_json = json.loads(resp.text)
                
            # 返回信息示例：
            # 下单失败
            # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60123, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '请输入支付密码！'}
            # {'overSea': False, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'orderXml': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60017, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '您多次提交过快，请稍后再试'}
            # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60077, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '获取用户订单信息失败'}
            # {"cartXml":null,"noStockSkuIds":"xxx","reqInfo":null,"hasJxj":false,"addedServiceList":null,"overSea":false,"orderXml":null,"sign":null,"pin":"xxx","needCheckCode":false,"success":false,"resultCode":600157,"orderId":0,"submitSkuNum":0,"deductMoneyFlag":0,"goJumpOrderCenter":false,"payInfo":null,"scaleSkuInfoListVO":null,"purchaseSkuInfoListVO":null,"noSupportHomeServiceSkuList":null,"msgMobile":null,"addressVO":{"pin":"xxx","areaName":"","provinceId":xx,"cityId":xx,"countyId":xx,"townId":xx,"paymentId":0,"selected":false,"addressDetail":"xx","mobile":"xx","idCard":"","phone":null,"email":null,"selfPickMobile":null,"selfPickPhone":null,"provinceName":null,"cityName":null,"countyName":null,"townName":null,"giftSenderConsigneeName":null,"giftSenderConsigneeMobile":null,"gcLat":0.0,"gcLng":0.0,"coord_type":0,"longitude":0.0,"latitude":0.0,"selfPickOptimize":0,"consigneeId":0,"selectedAddressType":0,"siteType":0,"helpMessage":null,"tipInfo":null,"cabinetAvailable":true,"limitKeyword":0,"specialRemark":null,"siteProvinceId":0,"siteCityId":0,"siteCountyId":0,"siteTownId":0,"skuSupported":false,"addressSupported":0,"isCod":0,"consigneeName":null,"pickVOname":null,"shipmentType":0,"retTag":0,"tagSource":0,"userDefinedTag":null,"newProvinceId":0,"newCityId":0,"newCountyId":0,"newTownId":0,"newProvinceName":null,"newCityName":null,"newCountyName":null,"newTownName":null,"checkLevel":0,"optimizePickID":0,"pickType":0,"dataSign":0,"overseas":0,"areaCode":null,"nameCode":null,"appSelfPickAddress":0,"associatePickId":0,"associateAddressId":0,"appId":null,"encryptText":null,"certNum":null,"used":false,"oldAddress":false,"mapping":false,"addressType":0,"fullAddress":"xxxx","postCode":null,"addressDefault":false,"addressName":null,"selfPickAddressShuntFlag":0,"pickId":0,"pickName":null,"pickVOselected":false,"mapUrl":null,"branchId":0,"canSelected":false,"address":null,"name":"xxx","message":null,"id":0},"msgUuid":null,"message":"xxxxxx商品无货"}
            # {'orderXml': None, 'overSea': False, 'noStockSkuIds': 'xxx', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'cartXml': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 600158, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': {'oldAddress': False, 'mapping': False, 'pin': 'xxx', 'areaName': '', 'provinceId': xx, 'cityId': xx, 'countyId': xx, 'townId': xx, 'paymentId': 0, 'selected': False, 'addressDetail': 'xxxx', 'mobile': 'xxxx', 'idCard': '', 'phone': None, 'email': None, 'selfPickMobile': None, 'selfPickPhone': None, 'provinceName': None, 'cityName': None, 'countyName': None, 'townName': None, 'giftSenderConsigneeName': None, 'giftSenderConsigneeMobile': None, 'gcLat': 0.0, 'gcLng': 0.0, 'coord_type': 0, 'longitude': 0.0, 'latitude': 0.0, 'selfPickOptimize': 0, 'consigneeId': 0, 'selectedAddressType': 0, 'newCityName': None, 'newCountyName': None, 'newTownName': None, 'checkLevel': 0, 'optimizePickID': 0, 'pickType': 0, 'dataSign': 0, 'overseas': 0, 'areaCode': None, 'nameCode': None, 'appSelfPickAddress': 0, 'associatePickId': 0, 'associateAddressId': 0, 'appId': None, 'encryptText': None, 'certNum': None, 'addressType': 0, 'fullAddress': 'xxxx', 'postCode': None, 'addressDefault': False, 'addressName': None, 'selfPickAddressShuntFlag': 0, 'pickId': 0, 'pickName': None, 'pickVOselected': False, 'mapUrl': None, 'branchId': 0, 'canSelected': False, 'siteType': 0, 'helpMessage': None, 'tipInfo': None, 'cabinetAvailable': True, 'limitKeyword': 0, 'specialRemark': None, 'siteProvinceId': 0, 'siteCityId': 0, 'siteCountyId': 0, 'siteTownId': 0, 'skuSupported': False, 'addressSupported': 0, 'isCod': 0, 'consigneeName': None, 'pickVOname': None, 'shipmentType': 0, 'retTag': 0, 'tagSource': 0, 'userDefinedTag': None, 'newProvinceId': 0, 'newCityId': 0, 'newCountyId': 0, 'newTownId': 0, 'newProvinceName': None, 'used': False, 'address': None, 'name': 'xx', 'message': None, 'id': 0}, 'msgUuid': None, 'message': 'xxxxxx商品无货'}
            # 下单成功
            # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': True, 'resultCode': 0, 'orderId': 8740xxxxx, 'submitSkuNum': 1, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': None}

            if resp_json.get('success'):
                order_id = resp_json.get('orderId')
                if is_multi_thread:
                    self.log_stream_info('线程[%s]订单提交成功! 订单号：%s',thread_index, order_id)
                else:
                    self.log_stream_info('订单提交成功! 订单号：%s', order_id)
                ins.order_id = order_id
                return order_id
            else:
                message, result_code = resp_json.get('message'), resp_json.get('resultCode')
                if is_multi_thread:
                    self.log_stream_info('线程[%s]订单提交失败, 错误码：%s, 返回信息：%s', thread_index, result_code, message)
                else:
                    self.log_stream_info('订单提交失败, 错误码：%s, 返回信息：%s', result_code, message)
                    if not self.failure_msg:
                        self.failure_msg = message
                        if '正在进行预约抢购活动，暂不支持购买' in message:
                            self.log_stream_info('预约商品不支持移动端有货下单模式，切换到PC端')
                            self.temp_order_traditional = True
                        elif '抱歉，您当前选择的' in message or '当前选择的地区无法购买' in message:
                            self.log_stream_info(message)
                            should_stop = True
                            if self.emailer:
                                self.emailer.send(subject=message, content=message)
                            raise RestfulException(error_dict['SERVICE']['JD']['ADDR_NO_STOCK'])
                return False
        except Exception as e:
            if not is_fake:
                self.log_stream_error(e)
                self.log_stream_error(resp.text)
                logging.exception("error")
                if should_stop:
                    raise RestfulException(error_dict['SERVICE']['JD']['ADDR_NO_STOCK'])
            return False
        finally:
            if is_multi_thread:
                ins.executed_thread_count = ins.executed_thread_count + 1
            

    @fetch_latency
    def submit_order_mobile(self, is_fake=False):
        """提交订单

        此提交相比于PC端，可以提交mobile端订单

        :return: True/False 订单提交结果
        """
        url = ' https://wqdeal.jd.com/deal/msubmit/confirm'
        headers = {
            "User-Agent": 'JD4iPhone/10.0.2 CFNetwork/1197 Darwin/20.0.0',
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Connection": "keep-alive",
            'Host': 'wqdeal.jd.com',
            'referer':'https://p.m.jd.com/norder/order.action'
        }

        payload = {
            'paytype':0,
            'paychannel':1,
            'action':1,
            'reg':1,
            'type':0,
            'platprice':0,
            'savepayship':0,
            'sceneval':2,
            'callback':'confirmCbA',
            'skulist':build_target_sku_id_list([self.target_sku_id]),
            'rtk': gen_int_with_len(32),
            'sceneval':2
        }

        if is_fake:
            payload = {
                'paytype':0,
            }

        # paytype=0
        # &paychannel=1
        # &action=1
        # &reg=1
        # &type=0&
        # token2=4135B46EBDED749B854042E2B051377D&
        # dpid=&
        # skulist=100006480569
        # &scan_orig=
        # &gpolicy=
        # &platprice=0
        # &ship=0|65||||0||||||||||||0||0||0
        # &pick=
        # &savepayship=0
        # &callback=cbConfirmA
        # &uuid=
        # &validatecode=
        # &valuableskus=100006480569,1,2680,9249
        # &commlist=100006480569,,1,100006480569,1,0,0
        # &r=0.856181334173505
        # &'=2
        # &rtk=33180002009247083952261031381315
        # &traceid=865822650877303889

        try:
            resp = self.sess.get(url=url, params=payload, headers=headers)
            resp_json = parse_original_json(parse_callback_str(resp.text))

            # 返回信息示例：
            # 下单失败
            # try {confirmCbA({"errId":"8970","errMsg":"很抱歉，您的订单中没有商品，请返回购物车或商品详情页面重新购买","nextUrl":"","idc":"","traceId":"1206616563374872352","outOfStock":[],"rmInvalidSku":[],"resultCode":"0","pin":"","appid":"","dealId":"","totalPrice":"","ordeType":"","callBackUrl":"","sucPopSrc":"","sucPopGray":"","limitedskuinfo":[],"riskResult":"0","phoneNumber":"","uuid":"","cancelscaleskus":[],"commonstocksku":[],"limitedbuyskus":[]})}catch (e){if (window.confirm_badJs) {window.confirm_badJs(e)}}
            # try {confirmCbA({"errId":"13","errMsg":"用户未登录","nextUrl":"//passport.m.jd.com/user/login.action?sid=&returnurl=","idc":"","traceId":"1206581628110871711","outOfStock":[],"rmInvalidSku":[],"resultCode":"0","pin":"","appid":"","dealId":"","totalPrice":"","ordeType":"","callBackUrl":"","sucPopSrc":"","sucPopGray":"","limitedskuinfo":[],"riskResult":"0","phoneNumber":"","uuid":"","cancelscaleskus":[],"commonstocksku":[],"limitedbuyskus":[]})}catch (e){if (window.confirm_badJs) {window.confirm_badJs(e)}}
            # 下单成功
            # try {confirmCbA({"errId":"0","errMsg":"","nextUrl":"","idc":"","traceId":"1206620720902695448","outOfStock":[],"rmInvalidSku":[],"resultCode":"","pin":"jd_571e372284809","appid":"wxae3e8056daea8727","dealId":"204142752376","totalPrice":"920","ordeType":"0","callBackUrl":"","sucPopSrc":"","sucPopGray":"","limitedskuinfo":[],"riskResult":"","phoneNumber":"","uuid":"","cancelscaleskus":[],"commonstocksku":[],"limitedbuyskus":[]})}catch (e){if (window.confirm_badJs) {window.confirm_badJs(e)}}

            if resp_json.get('dealId'):
                order_id = resp_json.get('dealId')
                self.log_stream_info('订单提交成功! 订单号：%s', order_id)
                self.order_id = order_id
                return order_id
            else:
                message, result_code = resp_json.get('errMsg'), resp_json.get('errId')
                if '正在进行预约抢购活动，暂不支持购买' in message:
                    self.temp_order_traditional = True
                self.log_stream_info('订单提交失败, 错误码：%s, 返回信息：%s', result_code, message)
                self.log_stream_info(json_to_str(resp_json))
                return False
        except Exception as e:
            if not is_fake:
                self.log_stream_error(e)
                self.log_stream_error(resp.text)
                logging.exception("error")
            return False

    def submit_order_with_retry(self, is_multi_thread, retry=10, interval=2):
        """提交订单，并且带有重试功能
        :param retry: 重试次数
        :param interval: 重试间隔
        :return: 订单提交结果 True/False
        """
        self.order_id = ''
        for i in range(1, retry + 1):
            if is_multi_thread:
                thread_count = 4

                for thread_index in range (1, thread_count):
                    t = threading.Thread(target=self.submit_order, args=(is_multi_thread, self,thread_index))
                    t.daemon = True
                    t.start()

                while not self.order_id and (self.executed_thread_count != thread_count-1):
                    time.sleep(0.01)
            else:
                thread_index = 0
                self.submit_order(is_multi_thread, self, thread_index)
            if self.order_id:
                client_label = 'PC端'
                self.log_stream_info('使用%s第%s次下单成功', client_label, i)
                return self.order_id
            else:
                if i <= retry:
                    self.log_stream_info('第%s次下单失败，%ss后重试', i, interval)
                    self.create_temp_order()
                    time.sleep(interval)
        else:
            self.log_stream_info('重试提交%s次结束', retry)
            return False

    def submit_order_with_retry_mobile(self, is_multi_thread, retry=10, interval=2):
        """提交订单，并且带有重试功能
        :param retry: 重试次数
        :param interval: 重试间隔
        :return: 订单提交结果 True/False
        """
        self.order_id = ''
        for i in range(1, retry + 1):
            if is_multi_thread:
                thread_count = 4

                for thread_index in range (1, thread_count):
                    t = threading.Thread(target=self.submit_order, args=(is_multi_thread, self,thread_index))
                    t.daemon = True
                    t.start()

                while not self.order_id and (self.executed_thread_count != thread_count-1):
                    time.sleep(0.01)
            else:
                thread_index = 0
                self.submit_order_mobile()
            if self.order_id:
                client_label = 'mobile端'
                self.log_stream_info('使用%s第%s次下单成功', client_label, i)
                return self.order_id
            else:
                if i <= retry:
                    self.log_stream_info('第%s次下单失败，%ss后重试', i, interval)
                    self.create_temp_order()
                    time.sleep(interval)
        else:
            self.log_stream_info('重试提交%s次结束', retry)
            return False

    def _get_seckill_url(self, sku_id):
        """获取商品的抢购链接
        点击"抢购"按钮后，会有两次302跳转，最后到达订单结算页面
        这里返回第一次跳转后的页面url，作为商品的抢购链接
        :param sku_id: 商品id
        :return: 商品的抢购链接
        """
        url = 'https://itemko.jd.com/itemShowBtn'
        payload = {
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            'skuId': sku_id,
            'from': 'pc',
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.user_agent,
            'Host': 'itemko.jd.com',
            'Referer': 'https://item.jd.com/{}.html'.format(sku_id),
        }
        retry_interval = 0.1
        count = 0

        while count < 200:
            resp = self.sess.get(url=url, headers=headers, params=payload)
            resp_json = parse_json(resp.text)
            if resp_json.get('url'):
                # https://divide.jd.com/user_routing?skuId=8654289&sn=c3f4ececd8461f0e4d7267e96a91e0e0&from=pc
                router_url = 'https:' + resp_json.get('url')
                # https://marathon.jd.com/captcha.html?skuId=8654289&sn=c3f4ececd8461f0e4d7267e96a91e0e0&from=pc
                seckill_url = router_url.replace('divide', 'marathon').replace('user_routing', 'captcha.html')
                self.log_stream_info("抢购链接获取成功: %s", seckill_url)
                return seckill_url
            else:
                count += 1
                self.log_stream_info("抢购链接获取失败，%s不是抢购商品或抢购页面暂未刷新，%s秒后重试", sku_id, retry_interval)
                # 设置取消检查点
                if not sleep_with_check(retry_interval, self.execution_cache_key):
                    self.execution_keep_running = False
                    return False

    def request_seckill_url(self, sku_id):
        """访问商品的抢购链接（用于设置cookie等）
        :param sku_id: 商品id
        :return:
        """
        if not self.seckill_url.get(sku_id):
            self.seckill_url[sku_id] = self._get_seckill_url(sku_id)
            if not self.execution_keep_running:
                return False
        headers = {
            'User-Agent': self.user_agent,
            'Host': 'marathon.jd.com',
            'Referer': 'https://item.jd.com/{}.html'.format(sku_id),
        }
        self.sess.get(url=self.seckill_url.get(sku_id), headers=headers, allow_redirects=False)

    def request_seckill_checkout_page(self, sku_id, num=1):
        """访问抢购订单结算页面
        :param sku_id: 商品id
        :param num: 购买数量，可选参数，默认1个
        :return:
        """
        url = 'https://marathon.jd.com/seckill/seckill.action'
        payload = {
            'skuId': sku_id,
            'num': num,
            'rid': int(time.time())
        }
        headers = {
            'User-Agent': self.user_agent,
            'Host': 'marathon.jd.com',
            'Referer': 'https://item.jd.com/{}.html'.format(sku_id),
        }
        self.sess.get(url=url, params=payload, headers=headers)

    def _get_seckill_init_info(self, sku_id, num=1):
        """获取秒杀初始化信息（包括：地址，发票，token）
        :param sku_id:
        :param num: 购买数量，可选参数，默认1个
        :return: 初始化信息组成的dict
        """
        url = 'https://marathon.jd.com/seckillnew/orderService/pc/init.action'
        data = {
            'sku': sku_id,
            'num': num,
            'isModifyAddress': 'false',
        }
        headers = {
            'User-Agent': self.user_agent,
            'Host': 'marathon.jd.com',
        }
        resp = self.sess.post(url=url, data=data, headers=headers)
        return parse_json(resp.text)

    def _gen_seckill_order_data(self, sku_id, num=1):
        """生成提交抢购订单所需的请求体参数
        :param sku_id: 商品id
        :param num: 购买数量，可选参数，默认1个
        :return: 请求体参数组成的dict
        """

        # 获取用户秒杀初始化信息
        if not self.seckill_init_info.get(sku_id):
            self.seckill_init_info[sku_id] = self._get_seckill_init_info(sku_id)

        init_info = self.seckill_init_info.get(sku_id)
        default_address = init_info['address']  # 默认地址dict
        invoice_info = init_info.get('invoiceInfo', {})  # 默认发票信息dict, 有可能不返回
        token = init_info['token']

        data = {
            'skuId': sku_id,
            'num': num,
            'addressId': default_address['id'],
            'yuShou': str(bool(int(init_info['seckillSkuVO']['extMap'].get('YuShou', '0')))).lower(),
            'isModifyAddress': 'false',
            'name': default_address['name'],
            'provinceId': default_address['provinceId'],
            'cityId': default_address['cityId'],
            'countyId': default_address['countyId'],
            'townId': default_address['townId'],
            'addressDetail': default_address['addressDetail'],
            'mobile': default_address['mobile'],
            'mobileKey': default_address['mobileKey'],
            'email': default_address.get('email', ''),
            'postCode': '',
            'invoiceTitle': invoice_info.get('invoiceTitle', -1),
            'invoiceCompanyName': '',
            'invoiceContent': invoice_info.get('invoiceContentType', 1),
            'invoiceTaxpayerNO': '',
            'invoiceEmail': '',
            'invoicePhone': invoice_info.get('invoicePhone', ''),
            'invoicePhoneKey': invoice_info.get('invoicePhoneKey', ''),
            'invoice': 'true' if invoice_info else 'false',
            'password': self.payment_pwd,
            'codTimeType': 3,
            'paymentType': 4,
            'areaCode': '',
            'overseas': 0,
            'phone': '',
            'eid': self.eid,
            'fp': self.fp,
            'token': token,
            'pru': '',
            'provinceName': default_address['provinceName'],
            'cityName': default_address['cityName'],
            'countyName': default_address['countyName'],
            'townName': default_address['townName'],
            'sk': self.marathon_sk
        }
        return data

    def submit_seckill_order(self, sku_id, num=1):
        """提交抢购（秒杀）订单
        :param sku_id: 商品id
        :param num: 购买数量，可选参数，默认1个
        :return: 抢购结果 True/False
        """
        url = 'https://marathon.jd.com/seckillnew/orderService/pc/submitOrder.action'
        payload = {
            'skuId': sku_id,
        }
        if not self.seckill_order_data.get(sku_id):
            self.seckill_order_data[sku_id] = self._gen_seckill_order_data(sku_id, num)

        headers = {
            'User-Agent': self.user_agent,
            'Host': 'marathon.jd.com',
            'Referer': 'https://marathon.jd.com/seckill/seckill.action?skuId={0}&num={1}&rid={2}'.format(
                sku_id, num, int(time.time())),
        }

        resp_json = None
        try:
            resp = self.sess.post(url=url, headers=headers, params=payload,
                                  data=self.seckill_order_data.get(sku_id), timeout=5)
            self.log_stream_info(resp.text)
            resp_json = parse_json(resp.text)
        except Exception as e:
            self.log_stream_error('秒杀请求出错：%s', str(e))
            return False
        # 返回信息
        # 抢购失败：
        # {'errorMessage': '很遗憾没有抢到，再接再厉哦。', 'orderId': 0, 'resultCode': 60074, 'skuId': 0, 'success': False}
        # {'errorMessage': '抱歉，您提交过快，请稍后再提交订单！', 'orderId': 0, 'resultCode': 60017, 'skuId': 0, 'success': False}
        # {'errorMessage': '系统正在开小差，请重试~~', 'orderId': 0, 'resultCode': 90013, 'skuId': 0, 'success': False}
        # 抢购成功：
        # {"appUrl":"xxxxx","orderId":820227xxxxx,"pcUrl":"xxxxx","resultCode":0,"skuId":0,"success":true,"totalMoney":"xxxxx"}

        if resp_json.get('success'):
            order_id = resp_json.get('orderId')
            total_money = resp_json.get('totalMoney')
            pay_url = 'https:' + resp_json.get('pcUrl')
            self.log_stream_info('抢购成功，订单号: %s, 总价: %s, 电脑端付款链接: %s', order_id, total_money, pay_url)
            return order_id
        else:
            self.log_stream_info('抢购失败，返回信息: %s', resp_json)
            return False

    def exec_marathon_seckill(self, sku_id, num, submit_retry_count, submit_interval):
        """立即抢购
        抢购商品的下单流程与普通商品不同，不支持加入购物车，可能需要提前预约，主要执行流程如下：
        1. 访问商品的抢购链接
        2. 访问抢购订单结算页面（好像可以省略这步，待测试）
        3. 提交抢购（秒杀）订单
        :param sku_id: 商品id
        :param submit_retry_count: 抢购重复执行次数，可选参数，默认4次
        :param submit_interval: 抢购执行间隔，可选参数，默认4秒
        :param num: 购买数量，可选参数，默认1个
        :return: 抢购结果 order_id/False
        """
        for count in range(1, submit_retry_count + 1):
            self.log_stream_info('第[%s/%s]次尝试抢购商品:%s', count, submit_retry_count, sku_id)

            ret = self.request_seckill_url(sku_id)
            if not ret and not self.execution_keep_running:
                return False

            order_id = self.submit_seckill_order(sku_id, num)
            if order_id:
                return order_id
            else:
                self.log_stream_info('休息%ss', submit_interval)
                if not sleep_with_check(submit_interval, self.execution_cache_key):
                    self.execution_keep_running = False
                    return False
        else:
            self.log_stream_info('执行结束，抢购%s失败！', sku_id)
            return False

    def get_item_from_page(self, sku_id):
        """获取商品名称
        :param sku_id: 商品id
        :return:
        """

        url = 'https://item.jd.com/{}.html'.format(sku_id)

        headers = {
            'User-Agent': self.user_agent
        }

        resp = self.sess.get(url=url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")

        sku_name = soup.find('div', {'class': 'sku-name'}).text.strip()
        return sku_name

    def get_item_info(self, sku_id):
        """获取商品名称
        :param sku_id: 商品id
        :return:
        """

        url = 'http://yx.3.cn/service/info.action?ids={}'.format(sku_id)

        headers = {
            'User-Agent': self.user_agent
        }

        resp = self.sess.get(url=url, headers=headers)
        resp_json = parse_json(resp.text)

        sku_name = resp_json[sku_id]['name']
        imageUrl = 'https://img13.360buyimg.com/n1/' + resp_json[sku_id]['imagePath']
        return sku_name, imageUrl

    def get_item_detail_info(self, sku_id, is_wait_for_limit=True, is_check_stock=True):
        """获取详细信息
        :param sku_id: 商品id
        :return:
        """
        sku_name, imageUrl = self.get_item_info(sku_id)

        url = ''

        if is_check_stock:
            url = 'https://item-soa.jd.com/getWareBusiness?skuId={}&area={}'.format(sku_id, self.area_id)
        else:
            url = 'https://item-soa.jd.com/getWareBusiness?skuId={}'.format(sku_id)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.4515.131 Safari/537.36'.format(str(random.randint(80, 90))),
            'Host': 'item-soa.jd.com'
        }

        try:
            resp = self.sess.get(url=url, headers=headers)
            resp_json = parse_json(resp.text)
        except Exception as e:
            # retry using random num as agent
            headers = {
                'User-Agent': str(int(time.time() * 1000)),
                'Host': 'item-soa.jd.com'
            }
            resp = self.sess.get(url=url, headers=headers)
            resp_json = parse_json(resp.text)

        sku_info = {}

        sku_info['sku_id'] = sku_id
        sku_info['sku_name'] = sku_name
        sku_info['imageUrl'] = imageUrl
        sku_info['stock_info'] = self.stock_state_map[str(resp_json['stockInfo']['stockState'])]

        # check if item available
        if is_check_stock:
            if 'stockDesc' in resp_json['stockInfo'] and '该商品在该地区暂不支持销售' in resp_json['stockInfo']['stockDesc']:
                if not self.failure_msg:
                    self.failure_msg = '该商品在该地区暂不支持销售'
                if self.emailer:
                    self.emailer.send(subject='商品在该地区暂不支持销售', content='该商品在该地区暂不支持销售')
                raise RestfulException(error_dict['SERVICE']['JD']['ADDR_NO_STOCK'])

        sku_info['list_price'] = resp_json['price']['m']
        sku_info['current_price'] = resp_json['price']['p']
        if 'op' in resp_json['price'] and resp_json['price']['op']:
            sku_info['original_price'] = resp_json['price']['op']
        else:
            sku_info['original_price'] = sku_info['current_price']
        sku_info['is_seckill_product'] = False
        sku_info['is_reserve_product'] = False
        sku_info['is_presale_product'] = False
        sku_info['is_oversea_product'] = False
        sku_info['is_free_delivery'] = False

        sku_info['price_discount'] = str(round(float(sku_info['current_price']) / float(sku_info['original_price']), 3) * 10)
        if len(sku_info['price_discount']) > 4:
            sku_info['price_discount'] = sku_info['price_discount'][0:4]
        sku_info['price_discount'] = sku_info['price_discount'] + '折'

        if '京东' in resp_json['servicesInfoUnited']['stockInfo']['serviceInfo'] or resp_json['servicesInfoUnited']['stockInfo']['serverIcon']['wlfwIcons']:
            sku_info['is_jd_delivery'] = True
        else:
            sku_info['is_jd_delivery'] = False

        if 'miaoshaInfo' in resp_json.keys():
            seckill_json = resp_json['miaoshaInfo']
            sku_info['seckill_info'] = {}
            sku_info['is_seckill_product'] = True
            sku_info['seckill_info']['seckill_state'] = seckill_json['state']
            if seckill_json['state'] == 1:
                sku_info['seckill_info']['seckill_state_str'] = '等待秒杀开始'
                sku_info['seckill_info']['promo_price'] = seckill_json['promoPrice']
            elif seckill_json['state'] == 2:
                sku_info['seckill_info']['seckill_state_str'] = '秒杀已经开始'
                sku_info['seckill_info']['promo_price'] = sku_info['current_price']
            else:
                sku_info['seckill_info']['seckill_state_str'] = '秒杀结束'
                sku_info['seckill_info']['promo_price'] = sku_info['current_price']

            sku_info['seckill_info']['seckill_discount'] = str(round(float(sku_info['seckill_info']['promo_price']) / float(sku_info['original_price']), 3) * 10)

            if len(sku_info['seckill_info']['seckill_discount']) > 4:
                sku_info['seckill_info']['seckill_discount'] = sku_info['seckill_info']['seckill_discount'][0:4]
            sku_info['seckill_info']['seckill_discount'] = sku_info['seckill_info']['seckill_discount'] + '折'

            sku_info['seckill_info']['seckill_start_time_ts'] = seckill_json['startTime']
            sku_info['seckill_info']['seckill_start_time_str'] = datetime_to_str(datetime.fromtimestamp(int(seckill_json['startTime'] / 1000 )), format_pattern=DATETIME_STR_PATTERN_SHORT)
            sku_info['seckill_info']['seckill_end_time_ts'] = seckill_json['endTime']
            sku_info['seckill_info']['seckill_end_time_str'] = datetime_to_str(datetime.fromtimestamp(int(seckill_json['endTime'] / 1000 )), format_pattern=DATETIME_STR_PATTERN_SHORT)

        if 'yuyueInfo' in resp_json.keys():
            reserve_json = resp_json['yuyueInfo']
            sku_info['reserve_info'] = {}
            sku_info['is_reserve_product'] = True
            sku_info['reserve_info']['reserve_state'] = reserve_json['state']
            if reserve_json['state'] == 1:
                sku_info['reserve_info']['reserve_state_str'] = '等待预约开始'
            elif reserve_json['state'] == 2:
                sku_info['reserve_info']['reserve_state_str'] = '正在预约'
            elif reserve_json['state'] == 3:
                sku_info['reserve_info']['reserve_state_str'] = '预约结束，等待抢购'
            else:
                sku_info['reserve_info']['reserve_state_str'] = '正在抢购'
            
            sku_info['reserve_info']['num'] = reserve_json['num']
            sku_info['reserve_info']['reserve_time'] = reserve_json['yuyueTime'].replace('~', '-')
            sku_info['reserve_info']['buy_time'] = reserve_json['buyTime']

        if 'YuShouInfo' in resp_json.keys():
            presale_json = resp_json['YuShouInfo']
            sku_info['presale_info'] = {}
            sku_info['is_presale_product'] = True
            sku_info['presale_info']['yuShouDeposit'] = presale_json['yuShouDeposit']
            sku_info['presale_info']['yuShouPrice'] = presale_json['yuShouPrice']
            sku_info['presale_info']['presaleStartTime'] = presale_json['presaleStartTime']
            sku_info['presale_info']['presaleEndTime'] = presale_json['presaleEndTime']
            sku_info['presale_info']['tailMoneyStartTime'] = presale_json['tailMoneyStartTime']
            sku_info['presale_info']['tailMoneyEndTime'] = presale_json['tailMoneyEndTime']
        
        if 'worldBuyInfo' in resp_json.keys():
            sku_info['is_oversea_product'] = True
            self.has_oversea_product = True

        # if sku_info['is_jd_delivery']:
        if 'servicesInfoUnited' in resp_json.keys():
            if 'serviceInfo' in resp_json['servicesInfoUnited']:
                for icon in resp_json['servicesInfoUnited']['serviceInfo']['basic']['iconList']:
                    if 'code' in icon and ( icon['code'] == 'free_baoyou' or icon['code'] == 'free_sxbaoyou'):
                        sku_info['is_free_delivery'] = True
                        break

        if 'stockInfo' in resp_json.keys():
            if 'dcashDesc' in resp_json['stockInfo'] and '免运费' in resp_json['stockInfo']['dcashDesc']:
                sku_info['is_free_delivery'] = True

        if is_wait_for_limit:
            api_limit_interval = 0.5
            time.sleep(api_limit_interval)

        return sku_info

    def print_product_info(self, item_info):
        self.log_stream_info('商品sku:               %s', item_info['sku_id'])
        self.log_stream_info('商品名称:              %s', item_info['sku_name'])
        self.log_stream_info('抢购数量:              %s', item_info['count'])
        self.log_stream_info('库存状态:              %s', item_info['stock_info'])
        self.log_stream_info('商品是否为京东配送     %s', self.bool_map[str(item_info['is_jd_delivery'])])
        self.log_stream_info('商品是否为预约类型     %s', self.bool_map[str(item_info['is_reserve_product'])])
        self.log_stream_info('商品是否为秒杀类型     %s', self.bool_map[str(item_info['is_seckill_product'])])
        self.log_stream_info('商品是否为预售类型     %s', self.bool_map[str(item_info['is_presale_product'])])
        self.log_stream_info('商品是否为海外类型     %s', self.bool_map[str(item_info['is_oversea_product'])])
        self.log_stream_info('商品是否为包邮类型     %s', self.bool_map[str(item_info['is_free_delivery'])])
        self.log_stream_info('原始价格               %s', item_info['list_price'])
        self.log_stream_info('京东价格               %s', item_info['original_price'])
        self.log_stream_info('当前价格               %s', item_info['current_price'])
        

        if item_info['is_reserve_product']:
            self.log_stream_info('==================================预约信息===============================')
            self.log_stream_info('预约状态               %s', item_info['reserve_info']['reserve_state_str'])
            self.log_stream_info('预约人数               %s', item_info['reserve_info']['num'])
            self.log_stream_info('预约时间               %s', item_info['reserve_info']['reserve_time'])
            self.log_stream_info('抢购时间               %s', item_info['reserve_info']['buy_time'])
            self.log_stream_info('==================================预约信息===============================')

        if item_info['is_seckill_product']:
            stock_count = self.get_seckill_item_stock(item_info['sku_id'])
            self.log_stream_info('==================================秒杀信息===============================')
            self.log_stream_info('秒杀状态               %s', item_info['seckill_info']['seckill_state_str'])
            self.log_stream_info('秒杀价格               %s', item_info['seckill_info']['promo_price'])
            self.log_stream_info('秒杀折扣               %s', item_info['seckill_info']['seckill_discount'])
            if stock_count:
                self.log_stream_info('特殊标签               %s', stock_count)
            else:
                self.log_stream_info('特殊标签               %s', '')
            self.log_stream_info('秒杀开始时间           %s', item_info['seckill_info']['seckill_start_time_str'])
            self.log_stream_info('秒杀结束时间           %s', item_info['seckill_info']['seckill_end_time_str'])
            self.log_stream_info('==================================秒杀信息===============================')

        if item_info['is_presale_product']:
            self.log_stream_info('==================================预售信息===============================')
            self.log_stream_info('预售定金               %s', item_info['presale_info']['yuShouDeposit'])
            self.log_stream_info('预售价格               %s', item_info['presale_info']['yuShouPrice'])
            self.log_stream_info('预售开始时间           %s', item_info['presale_info']['presaleStartTime'])
            self.log_stream_info('预售结束时间           %s', item_info['presale_info']['presaleEndTime'])
            self.log_stream_info('尾款开始时间           %s', item_info['presale_info']['tailMoneyStartTime'])
            self.log_stream_info('尾款结束时间           %s', item_info['presale_info']['tailMoneyEndTime'])
            self.log_stream_info('==================================预售信息===============================')

    def call_function_with_leading_time(self, title, sleep_interval, func, *args):
        target_time = args[0]
        leading_in_sec = args[1]
        # 在开始前leading_in_sec秒检查cookie有效性
        target_time_datetime = str_to_datetime(target_time)
        # 获取检查时间
        adjusted_target_time_datetime = datetime_offset_in_milliesec(target_time_datetime, -leading_in_sec * 1000)
        # 转换为string
        adjusted_target_time_str = datetime_to_str(adjusted_target_time_datetime)
        # 定时启动
        t = Timer(service_ins=self, target_time=adjusted_target_time_str, cache_key=self.execution_cache_key, sleep_interval=sleep_interval)
        running_flag = t.start(title)
        if not running_flag:
            self.execution_keep_running = False
            return func(*args)

        return func(*args)

    def check_individual_client_cookie(self):
        try:
            self.log_stream_info('正在检查电脑端cookie有效性')
            self.nick_name = self.get_user_info()
            self.log_stream_info('电脑端cookie有效, 登录用户名:%s', self.nick_name)
        except Exception as e:
            # retry 
            try:
                self.log_stream_info('上一次电脑端cookie测试失败，再次测试电脑端cookie测试有效性')
                self.nick_name = self.get_user_info()
                self.log_stream_info('电脑端cookie测试有效, 登录用户名:%s', self.nick_name)
            except Exception as e:
                self.is_login = False
                self.log_stream_error('测试电脑端cookie有效性失败：%s', str(e))
                if not self.failure_msg:
                        self.failure_msg = '重新扫码'
                if self.emailer:
                    self.emailer.send(subject='用户' + self.nick_name + '电脑端cookie测试有效性失败', content='请重新登录')
                raise RestfulException(error_dict['SERVICE']['JD']['PC_NOT_LOGIN'])

        # 验证手机端cookie
        self.log_stream_info('正在检查移动端cookie有效性')
        mobile_nick_name = self.get_user_info_mobile()
        if mobile_nick_name:
            self.log_stream_info('移动端cookie有效')
        else:
            self.log_stream_info('上一次测试移动端cookie失败，再次测试移动端cookie有效性')
            mobile_nick_name = self.get_user_info_mobile()
            if mobile_nick_name:
                self.log_stream_info('移动端cookie有效')
            else:
                self.is_login = False
                self.log_stream_error('测试移动端cookie有效性失败')
                if not self.failure_msg:
                        self.failure_msg = '重新发送验证码'
                if self.emailer:
                    self.emailer.send(subject='用户' + self.nick_name + '移动端cookie测试有效性失败', content='请重新登录')
                raise RestfulException(error_dict['SERVICE']['JD']['USER_MOBILE_COOKIE_FAILURE'])
                    
    @fetch_latency
    def check_cookie_valid(self, target_time, leading_in_sec):
        self.log_stream_info('抢购开始前%s分钟检查cookie有效性', leading_in_sec / float(60))
        self.check_individual_client_cookie()

        # 尝试再次预约，以避免类型变动
        sku_id = self.target_sku_id
        if not self.make_reserve(sku_id):
            raise RestfulException(error_dict['SERVICE']['JD']['MANUAL_RESERVE_REQUIRED'])

    @fetch_latency
    def update_sys_time(self, target_time, leading_in_sec):
        adjusted_server_time_in_cache = self.get_adjusted_server_time_from_cache(target_time)
        if not adjusted_server_time_in_cache:
            self.log_stream_info('抢购开始前%s秒更新系统时间', leading_in_sec)
            adjust_server_time(self.analyse_server_time, self.login_username)
        else:
            self.log_stream_info('忽略系统时间更新, 使用缓存时间%s', adjusted_server_time_in_cache)
            return adjusted_server_time_in_cache

    @fetch_latency
    def get_server_datetime(self):
        url = 'https://api.m.jd.com/client.action?functionId=queryMaterialProducts&client=wh5'
        js = json.loads(self.sess.get(url).text)
        t_server = float(js["currentTime2"]) / float(1000)
        t_server_datetime = datetime.fromtimestamp(t_server)
        return t_server_datetime

    @fetch_latency
    def get_server_datetime_gias(self):
        time_now = str(time.time()).replace('.','')
        url = 'https://gias.jd.com/js/td.js?t=${}'.format(time_now)
        headers = {
            'User-Agent': self.user_agent
        }
        resp = self.sess.get(url=url, headers=headers)
        x_trace = resp.headers['X-Trace']

        t_server = float(x_trace.split(';')[0].split('-')[1]) / float(1000)
        t_server_datetime = datetime.fromtimestamp(t_server)
        return t_server_datetime

    def analyse_server_time(self, is_warm_time_request=False):
        # 开始分析
        if is_warm_time_request:

            # 调用服务器时间接口计算最小延迟
            get_servertime_count = 10
            t_reach_array = []
            self.log_stream_info('调用服务器时间接口%s次计算最小延迟', get_servertime_count)
            
            for count in range(0, get_servertime_count):
                t_before = get_now_datetime()
                # 与下单服务器使用同一网段的api测试获取单向延迟
                self.get_server_datetime()
                # 添加请求到达服务器时间
                t_reach_array.append(self.last_func_cost / float(2))
                
            # 选出其中延迟最低的一次请求到达服务器时间
            self.t_reach_min = min(t_reach_array)

        t_before = get_now_datetime()
        t_server_datetime = self.get_server_datetime()
        t_after = get_now_datetime()
        t_reach = self.last_func_cost / float(2)

        t_server_real_time = datetime_offset_in_milliesec(t_server_datetime, t_reach)

        # 本地服务器差值
        t_diff = get_ts_diff_with_floor(t_server_datetime, t_before) - t_reach

        # 以最低到达服务器时间减1毫秒
        t_reach_server_leading_in_millie_sec = self.t_reach_min - 1

        # 返回结果
        return t_diff, t_server_real_time, t_server_datetime, t_reach, self.t_reach_min, t_after, t_reach_server_leading_in_millie_sec


    @fetch_latency
    def sync_target_time(self, target_time, leading_in_sec, is_adjust_time, is_warm_time_request):
        delay = 0
        target_time_datetime = None
        # 获取服务器时间
        t_diff, t_server_real_time, t_server_datetime, t_reach, t_reach_min, t_local, t_reach_server_leading_in_millie_sec = self.analyse_server_time(is_warm_time_request)
        
        if is_adjust_time:
            self.log_stream_info('请求到达服务器最低时间               %sms', t_reach_min)
            self.log_stream_info('估算本地请求到达服务器时间           %sms', t_reach_server_leading_in_millie_sec)
        self.log_stream_info('本地时间                             %s', t_local)
        self.log_stream_info('本次请求到达服务器时间               %sms', t_reach)
        self.log_stream_info('本次服务器api返回时间                %s', t_server_datetime)
        self.log_stream_info('本次服务器理论时间                   %s', t_server_real_time)
        self.log_stream_info('本地服务器差值                       %sms', t_diff)

        if is_adjust_time:

            # 如果服务器时间比本地快, 提前
            if t_diff > 0:
                if t_diff <= 1.5:
                    # 1.5毫秒以内，不做延迟更改
                    delay = 0
                else:
                    delay = t_diff - 1
                self.log_stream_info('服务器时间比本地快                   %sms', t_diff)
                self.log_stream_info('需提前                               %sms', delay)
                # 再次加上单个请求到达服务器的时间，以提前发送请求
                delay = delay + t_reach_server_leading_in_millie_sec
            else:
                # 如果服务器时间比本地慢, 等待
                delay = (0 - t_diff) + 1
                self.log_stream_info('本地时间比服务器晚                   %sms', (0 - t_diff))
                self.log_stream_info('需等待                               %sms', delay)
                # 再次加上单个请求到达服务器的时间，以提前发送请求
                delay = delay - t_reach_server_leading_in_millie_sec

            # 调整抢购时间
            target_time_datetime = str_to_datetime(target_time)
            if t_diff > 0:
                self.log_stream_info('减掉请求到达服务器最低时间后需提前   %sms', delay)
                target_time_datetime = datetime_offset_in_milliesec(target_time_datetime, -delay)
            else:
                if delay > 0:
                    self.log_stream_info('减掉请求到达服务器最低时间后需等待   %sms', delay)
                else:
                    self.log_stream_info('减掉请求到达服务器最低时间后需提前   %sms', -delay)
                target_time_datetime = datetime_offset_in_milliesec(target_time_datetime, delay)

        if target_time_datetime:
            return datetime_to_str(target_time_datetime), t_server_real_time, t_reach
        else:
            return None, t_server_real_time, t_reach

    def debug_after_order(self, target_time, t_order_start):
        is_adjust_time = False
        is_warm_time_request = False
        leading_in_sec = 0
        adjusted_target_time, t_server_real_time, t_reach = self.sync_target_time(target_time, leading_in_sec, is_adjust_time, is_warm_time_request)
        t_order_end = get_now_datetime()

        t_order_cost = get_timestamp_in_milli_sec(t_order_end) - get_timestamp_in_milli_sec(t_order_start)

        t_reach_to_server = datetime_offset_in_milliesec(t_server_real_time, (t_reach -t_order_cost))

        self.log_stream_info('理论上下单请求到达服务器的时间       %s', t_reach_to_server)

        return t_reach_to_server

    @fetch_latency
    def get_order_coupons(self):
        url = 'https://trade.jd.com/shopping/dynamic/coupon/getCoupons.action'
        data = {
            'presaleStockSign': 1
        }

        if self.has_oversea_product:
            data['overseaMerge'] = 1

        headers = {
            'User-Agent': self.user_agent,
            'referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action',
        }
        resp = self.sess.post(url, data=data, headers=headers)

    @fetch_latency
    def get_best_coupons(self):
        url = 'https://trade.jd.com/shopping/dynamic/coupon/getBestVertualCoupons.action'
        data = {
            'presaleStockSign': 1
        }
        if self.has_oversea_product:
            data['overseaMerge'] = 1
        headers = {
            'User-Agent': self.user_agent,
            'referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action',
        }
        resp = self.sess.post(url, data=data, headers=headers)

    @fetch_latency
    def get_addit_shipment_new(self):
        url = 'https://trade.jd.com/shopping/dynamic/payAndShip/getAdditShipmentNew.action'
        data = {
            'paymentId': '4',
            'shipParam.reset311': '0',
            'resetFlag': '1000000000',
            'shipParam.onlinePayType': '0',
            'typeFlag': '0',
            'promiseTagType': '',
            'presaleStockSign': 1
        }
        if self.has_oversea_product:
            data['overseaMerge'] = 1
        headers = {
            'User-Agent': self.user_agent,
            'referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action',
        }
        resp = self.sess.post(url, data=data, headers=headers)

    @fetch_latency
    def check_open_consignee(self):
        url = 'https://trade.jd.com/shopping/dynamic/payAndShip/getAdditShipmentNew.action'
        data = {
            'consigneeParam.provinceId': '8',
            'consigneeParam.cityId': '573',
            'consigneeParam.countyId': '3261',
            'consigneeParam.townId': '63172',
            'presaleStockSign': 1
        }
        if self.has_oversea_product:
            data['overseaMerge'] = 1
        headers = {
            'User-Agent': self.user_agent,
            'referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action',
        }
        resp = self.sess.post(url, data=data, headers=headers)

    @fetch_latency
    def save_pay_and_ship_new(self):
        url = 'https://trade.jd.com/shopping/dynamic/payAndShip/savePayAndShipNew.action'
        data = {
            'saveParam.paymentId': 4,
            'saveParam.onlinePayType': 0,
            'saveParam.jdShipTime': 3,
            'saveParam.jdCheckType': 2,
            'saveParam.sopShipment': '{"venderId":"104079","sopShipment":"67"}',
            'saveParam.pickSiteNum': 5,
            'saveParam.combine': 0,
            'saveParam.relationUuidMap': '%7B%22combinationBundle%22%3A%22CombinationBundleRelation_962122771982958596%22%2C%22order%22%3A%22-563251656%22%7D',
            'saveParam.venderUuidMap': '%7B%22104079%22%3A%7B%22EVERY_DATE%22%3A%7B%22THIRD_PARTY%22%3A%22101613_962122852382134272%2B%22%7D%2C%22OrderUuid%22%3A%22-563251656%22%2C%22ACCURATE%22%3A%7B%7D%2C%22BundleUuid%22%3A%22BundleRelation_962122772071038976%2B%22%2C%22CombinationBundleUuid%22%3A%22CombinationBundleRelation_962122771982958596%22%2C%22TOP_SPEED%22%3A%7B%7D%2C%22THIRD_PARTY%22%3A%22101612_962122852344385536%2B%22%2C%22STANDARD%22%3A%7B%7D%2C%22isOnlyisOnlyBigItem%22%3A0%7D%7D',
            'saveParam.promiseFormatZxjBzd': 0,
            'saveParam.promiseFormatZxjJzd': 0,
            'saveParam.promiseFormatZxjJsd': 0,
            'saveParam.promiseFormatDjBzd': 0,
            'saveParam.promiseFormatDjJzd': 0,
            'saveParam.promiseFormatDjJsd': 0,
            'saveParam.zyOrSop': 1,
            'presaleStockSign': 1
        }
        if self.has_oversea_product:
            data['overseaMerge'] = 1
        headers = {
            'User-Agent': self.user_agent,
            'referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action',
        }
        resp = self.sess.post(url, data=data, headers=headers)

    @fetch_latency
    def obtain_copy_info_config(self):
        url = 'https://trade.jd.com/shopping/async/obtainCopyInfoConfig.action'
        data = {
            'orderInfoParam.provinceId': '8',
            'orderInfoParam.cityId': '573',
            'presaleStockSign': 1
        }
        if self.has_oversea_product:
            data['overseaMerge'] = 1
        headers = {
            'User-Agent': self.user_agent,
            'referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action',
        }
        resp = self.sess.post(url, data=data, headers=headers)

    @fetch_latency
    def get_consignee_list(self):
        url = 'https://trade.jd.com/shopping/dynamic/consignee/consigneeList.action'
        data = {
            'consigneeParam.newId': '486115477',
            'consigneeParam.addType': '0',
            'consigneeParam.userSmark': '0000000000000100201000000000010900100100000000006300001000000080010000000000000000000000000000000000',
            'presaleStockSign': 1
        }
        if self.has_oversea_product:
            data['overseaMerge'] = 1
        headers = {
            'User-Agent': self.user_agent,
            'referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action',
        }
        resp = self.sess.post(url, data=data, headers=headers)
    
    @fetch_latency
    def save_address(self):
        url = 'https://trade.jd.com/shopping/dynamic/consignee/saveConsignee.action'
        data = {
            'consigneeParam.newId': self.area_ref_id,
            'consigneeParam.type':'null',
            'consigneeParam.commonConsigneeSize': 2,
            'consigneeParam.isUpdateCommonAddress': 0,
            'consigneeParam.giftSenderConsigneeName': '',
            'consigneeParam.giftSendeConsigneeMobile': '',
            'consigneeParam.noteGiftSender': 'false',
            'consigneeParam.isSelfPick': 0,
            'consigneeParam.selfPickOptimize': 0,
            'consigneeParam.pickType': 0,
            'presaleStockSign': 1
        }
        if self.has_oversea_product:
            data['overseaMerge'] = 1
        headers = {
            'User-Agent': self.user_agent,
            'referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action',
            'origin': 'https://trade.jd.com',
        }
        resp = self.sess.post(url, data=data, headers=headers)

    @fetch_latency
    def add_random_addtional_item_to_cart(self):
        self.log_stream_info('发现预约商品，且全部为京东配送,使用凑单商品减少下单时间，正在测试凑单商品有效性')
        random_sku = select_random_item_from_array(self.additional_skus)
        if not self.add_item_to_cart(random_sku, self.additional_num):
            self.log_stream_error('凑单商品%s已失效，请删除该商品然后重新执行程序', random_sku)
            return False
        else:
            item_info = self.get_item_detail_info(random_sku)

            self.log_stream_info('=================================================================')
            self.log_stream_info('凑单商品sku:               %s', random_sku)
            self.log_stream_info('凑单商品名称:              %s', item_info['sku_name'])
            self.log_stream_info('凑单商品数量:              %s', self.additional_num)
            self.log_stream_info('凑单商品是否为预约类型     %s', str(item_info['is_reserve_product']))
            self.log_stream_info('凑单商品是否为秒杀类型     %s', str(item_info['is_seckill_product']))
            self.log_stream_info('凑单当前价格               %s', item_info['current_price'])
            self.log_stream_info('=================================================================')
            self.random_sku = random_sku
            return item_info['current_price']

    def get_item_from_same_vendor(self, sku_id):
        url = 'https://item-soa.jd.com/getWareBusiness?skuId={}'.format(sku_id)

        headers = {
            'User-Agent': self.user_agent
        }

        resp = self.sess.get(url=url, headers=headers)
        resp_json = parse_json(resp.text)

        random_sku_id = resp_json['shopInfo']['shop']['hotcates'][0]['commendSkuId']
        return str(random_sku_id)

    def get_target_product_price_threshold(self):
        item_info = self.target_product
        # 获取下单价格阈值
        if item_info['is_seckill_product']:
            self.order_price_threshold  += float(item_info['seckill_info']['promo_price']) * float(item_info['count']) + self.most_delivery_fee
        else:
            self.order_price_threshold  += float(item_info['current_price']) * float(item_info['count']) + self.most_delivery_fee

        return self.order_price_threshold

    def pre_order_cart_action(self, is_before_start=False):
        # 无法添加购物车商品，抢购开始后再次尝试添加
        if not self.is_marathon_mode:
            # 等待随机秒添加目标商品到购物车，避免购物车错误
            if is_before_start:
                random_wait = random.randint(0, 10)
                self.log_stream_info('等待%s秒添加目标商品到购物车', random_wait)
                time.sleep(random_wait)
            # self.add_item_to_cart(self.target_sku_id, self.target_sku_num)
            is_select_cart = False
            self.create_temp_order(is_select_cart=is_select_cart)
        else:
            self.log_stream_info('marathon抢购模式, 等待开始')

    @fetch_latency
    def create_temp_order_type_one(self):
        sleep_interval = 1
        sku_id = self.target_sku_id
        num = self.target_sku_num

        url = 'https://p.m.jd.com/norder/order.action'
        headers = {
            'User-Agent': self.mobile_user_agent,
            'referer':'https://plogin.m.jd.com/'
        }

        payload = {
            'enterOrder': True,
            'scene': 'jd',
            'bid': '',
            'wdref': 'https://item.m.jd.com/product/{}.html?sceneval=2'.format(sku_id),
            'EncryptInfo': '',
            'Token': '',
            'sceneval': 2,
            'isCanEdit': 1,
            'lg': 0,
            'supm': 0,
            'commlist': '{},,{},{},1,0,0'.format(sku_id, num, sku_id),
            'type': 0,
            'locationid': self.area_id,
            'jxsid': self.jxsid
        }

        resp = self.sess.get(url, params=payload, headers=headers)
        try:
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.find("title")
            if not title or not title.getText() == '确认订单':
                self.log_stream_info('创建订单错误，可能是刷新频率过高，休息%ss', sleep_interval)
                time.sleep(sleep_interval)
                self.create_temp_order_type_two()
        except Exception as e:
            self.log_stream_info('创建订单错误，可能是刷新频率过高，休息%s', sleep_interval)
            time.sleep(sleep_interval)
            self.create_temp_order_type_two()
            
    @fetch_latency
    def create_temp_order_type_two(self):
        sleep_interval = 1
        sku_id = self.target_sku_id
        num = self.target_sku_num

        url = 'https://m.jingxi.com/deal/confirmorder/main'
        headers = {
            'User-Agent': self.mobile_user_agent
        }

        payload = {
            'scene': 'jd',
            'isCanEdit': 1,
            'lg': 0,
            'supm': 0,
            'bizkey': 'pingou',
            'commlist': '{},,{},{},1,0,0'.format(sku_id, num, sku_id),
            'type': 0,
            'locationid': self.area_id,
            'action': 3,
            'bizval': 0,
            'jxsid': self.jxsid
        }
        resp = self.sess.get(url, params=payload, headers=headers)
        try:
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.find("title")
            if not title or not title.getText() == '确认订单':
                self.log_stream_info('创建订单错误，可能是刷新频率过高，休息%ss', sleep_interval)
                time.sleep(sleep_interval)
                self.create_temp_order_type_one()
        except Exception as e:
            self.log_stream_info('创建订单错误，可能是刷新频率过高，休息%s', sleep_interval)
            time.sleep(sleep_interval)
            self.create_temp_order_type_one()

    @fetch_latency
    def create_temp_order_traditional(self, is_add_cart_item=False):
        if is_add_cart_item:
            self.add_item_to_cart(self.target_sku_id, self.target_sku_num)
        else:
            # 选中购物车
            self.select_all_cart_item()
        # 使用优惠券
        self.get_best_coupons()
        # 提前刷新订单
        self.get_order_coupons()
        # 保存默认地址
        self.save_address()

    def create_temp_order(self, is_select_cart=True, is_add_cart_item=False):
        if self.temp_order_traditional:
            self.create_temp_order_traditional(is_add_cart_item)
        elif self.create_order_round % 2 == 0:
            self.create_temp_order_type_one()
        else:
            self.create_temp_order_type_two()

        if not self.temp_order_traditional and is_select_cart:
            self.select_all_cart_item()
        self.create_order_round += 1
    
    def process_orders(self, order_id_list='', is_check_price=True, is_send_message=True):
        if order_id_list:
            # 打印订单信息
            is_silent = False
            if is_check_price:
                is_silent = True
            order_list = self.get_order_info(is_silent)

            # 推送信息
            for unpaid_order_item in order_list:
                unpaid_order_id = str(unpaid_order_item['order_id'])
                for submitted_order_id  in order_id_list:
                    if str(submitted_order_id) == unpaid_order_id:
                        submitted_price = float(unpaid_order_item['sum_price'])
                        if is_check_price and submitted_price > self.order_price_threshold:
                            self.log_stream_info("订单%s下单价格为非秒杀价，下单价格%s, 取消订单", submitted_order_id, submitted_price)
                            self.cancel_order(submitted_order_id)
                            order_id_list.remove(submitted_order_id)
                            if not self.failure_msg:
                                self.failure_msg = "下单价格为非秒杀价，取消订单"
                            # 购物车准备
                            self.pre_order_cart_action()
                        elif is_send_message and self.emailer:
                            subject, content = build_order_message(self.nick_name, unpaid_order_item)
                            self.emailer.send(subject=subject, content=content)

            return order_id_list

    def save_order(self, order_id):
        is_silent = True
        order_list = self.get_order_info(silent=is_silent)
        
        for unpaid_order_item in order_list:
            unpaid_order_id = str(unpaid_order_item['order_id'])
            if str(order_id) == unpaid_order_id:
                unpaid_order_item['nick_name'] = self.nick_name
                unpaid_order_item['target_price'] = self.target_product['current_price']
                unpaid_order_item['original_price'] = self.target_product['original_price']

                if self.target_product['is_reserve_product']:
                    unpaid_order_item['is_reserve'] = '预约'
                if self.target_product['is_seckill_product']:
                    unpaid_order_item['is_seckill'] = '秒杀'
                    unpaid_order_item['target_price'] = self.target_product['seckill_info']['promo_price']

                unpaid_order_item['saved_price'] = float(round(float(unpaid_order_item['original_price']) - float(unpaid_order_item['target_price']), 2))
                unpaid_order_item['leading_time'] = self.order_leading_in_millis
                stock_count = self.get_seckill_item_stock(self.target_sku_id)
                if not stock_count:
                    stock_count = ''
                unpaid_order_item['stock_count'] = str(stock_count)

                self.jd_order_service.save_jd_order(self.login_username, unpaid_order_item)
                self.log_stream_info('成功保存订单')

    @fetch_latency
    def check_is_marathon_before_start(self, target_time, leading_in_sec):
        # 获取商品信息
        sku_id = self.target_sku_id
        num = self.target_sku_num
        item_info = self.target_product
        
        # 尝试添加目标商品到购物车以测试是否可以添加成功
        if not item_info['is_presale_product'] and not self.add_item_to_cart(sku_id, num):
            self.log_stream_info('提前添加%s到购物车失败', item_info['sku_name'])
            self.log_stream_info('商品无法加入购物车，切换为marathon抢购模式')
            self.is_marathon_mode = True
        else:
            self.log_stream_info('商品为非marathon抢购模式, 正常下单')

        self.clear_cart()

    def actions_before_target_time(self, target_time):

        # 设置取消检查点
        if not self.execution_keep_running:
            return False

        # 开始前leading_in_sec检查cookie
        leading_in_sec = 20 * random.randint(50, 70)
        sleep_interval = 1
        title = '抢购前[{0}]分钟检查cookie'.format(leading_in_sec / 60)
        self.call_function_with_leading_time(title, sleep_interval, self.check_cookie_valid, target_time, leading_in_sec)

        # 设置取消检查点
        if not self.execution_keep_running:
            return False

        # 开始前leading_in_sec再次检查是否为marathon模式
        leading_in_sec = 120
        sleep_interval = 10
        title = '抢购前[{0}]秒检查商品是否为marathon模式'.format(leading_in_sec)
        self.call_function_with_leading_time(title, sleep_interval, self.check_is_marathon_before_start, target_time, leading_in_sec)

        # 设置取消检查点
        if not self.execution_keep_running:
            return False

        adjusted_target_time = ''
        
        # 开始前leading_in_sec更新系统时间
        leading_in_sec = 30
        sleep_interval = 0.1
        title = '抢购前[{0}]秒更新系统时间'.format(leading_in_sec)
        adjusted_server_time_in_cache = self.call_function_with_leading_time(title, sleep_interval, self.update_sys_time, target_time, leading_in_sec)
        if adjusted_server_time_in_cache:
            adjusted_target_time = adjusted_server_time_in_cache

        # 设置取消检查点
        if not self.execution_keep_running:
            return False

        if not adjusted_server_time_in_cache:
            # 开始前leading_in_sec分析服务器时间
            leading_in_sec = 20
            sleep_interval = 0.1
            is_adjust_time = True
            is_warm_time_request = True
            title = '抢购前[{}]秒分析服务器时间'.format(leading_in_sec)
            adjusted_target_time, t_server_real_time, t_network = self.call_function_with_leading_time(title, sleep_interval, self.sync_target_time, target_time, leading_in_sec, is_adjust_time, is_warm_time_request)
            self.put_adjusted_server_time_in_cache(target_time, adjusted_target_time, 'finished')

        adjusted_target_time = self.adjust_leading_time_once(adjusted_target_time)

        # 设置取消检查点
        if not self.execution_keep_running:
            return False

        # 购物车准备
        is_before_start = True
        self.pre_order_cart_action(is_before_start)

        # 设置取消检查点
        if not self.execution_keep_running:
            return False

        return adjusted_target_time

    def adjust_leading_time_once(self, adjusted_target_time):
        # 整体提前leading_in_millis毫秒
        adjusted_target_date_time = str_to_datetime(adjusted_target_time)
        self.log_stream_info('整体提前                             %sms', self.order_leading_in_millis)
        target_time_datetime = datetime_offset_in_milliesec(adjusted_target_date_time, -self.order_leading_in_millis)

        adjusted_target_time = datetime_to_str(target_time_datetime)
        self.log_stream_info('调整后的抢购时间                     %s', adjusted_target_time)
        return adjusted_target_time

    def actions_after_order_submit(self, order_id_list, target_time, t_order_start):
        
        # 下单效率debug信息
        self.debug_after_order(target_time, t_order_start)

        is_check_price = False # 继续下单模式会先取消订单
        is_send_message = True
        return self.process_orders(order_id_list, is_check_price, is_send_message)

    def validate_params(self, sku_id, num):
        self.log_stream_info('==========================检查传入参数=================================')
        if not sku_id or not num:
            self.log_stream_error('sku或数量为空, 传入参数: %s， %s',sku_id, num)
            raise AssertionError('sku或数量为空')

    @fetch_latency
    def prepare_on_init(self, target_time, sku_id, num):
        try:
            self.log_stream_info('==========================初始化抢购程序=================================')

            # 等待随机秒，避免cookie错误
            random_wait = random.randint(0, 10)
            self.log_stream_info('等待%s秒检查用户cookie', random_wait)
            time.sleep(random_wait)
            self.check_individual_client_cookie()
            
            # 基本信息
            self.log_stream_info('运行在debug模式:%s', self.bool_map[str(self.is_debug_mode)])

            # 重置错误信息
            self.failure_msg = ""
            # 重置temp订单模式
            self.temp_order_traditional = False

            # 检查传入参数
            self.validate_params(sku_id, num)

            # 获取商品信息
            self.log_stream_info('抢购时间               %s', target_time)
            self.log_stream_info('=========================商品信息========================================')

            # 获取默认发货地址
            addr_obj = self.get_user_addr()
            self.addr_obj = addr_obj
            self.default_addr = self.get_default_addr(addr_obj)
            self.is_multiple_addr = self.is_has_multiple_addr(self.default_addr)
            self.area_id = self.get_area_id_by_default_addr(self.default_addr)
            self.area_ref_id = self.get_area_ref_id_by_default_addr(self.default_addr)
            recipient_name = self.get_recipient_by_default_addr(self.default_addr)
            full_addr = self.get_full_addr_by_default_addr(self.default_addr)
            self.log_stream_info('默认收件人:        %s', recipient_name)
            self.log_stream_info('默认收件地址:      %s', full_addr)

            # 获取商品信息
            item_info = self.get_item_detail_info(sku_id)
            item_info['count'] = num
            self.target_product = item_info
            self.target_sku_id = sku_id
            self.target_sku_num = num
            
            # 打印商品信息
            self.print_product_info(item_info)

            self.log_stream_info('=========================================================================')

            # 检查是否无货
            if item_info['stock_info'] == '无货':
                self.log_stream_error(item_info['sku_name'] + '在该地区无货')
                if not self.failure_msg:
                    self.failure_msg = item_info['sku_name'] + '在该地区无货'
                if self.emailer:
                    self.emailer.send(subject=item_info['sku_name'] + '在该地区无货', content=item_info['sku_name'] + '在该地区无货')
                return False
            
            # 自动预约
            if item_info['is_reserve_product'] and item_info['reserve_info']['reserve_state_str'] == '正在预约':
                if not self.make_reserve(sku_id):
                    return False
            
            # 尝试添加目标商品到购物车以测试是否可以添加成功
            if not item_info['is_presale_product'] and not self.add_item_to_cart(sku_id, num):
                self.log_stream_info('提前添加%s到购物车失败', item_info['sku_name'])
                self.log_stream_info('商品无法加入购物车，切换为marathon抢购模式')
                self.is_marathon_mode = True

            self.log_stream_info('=========================================================================')

            # 检查是否有预约商品
            self.has_reserve_product = contains_reserve_product(self.target_product)

            # 检查是否有预售商品
            self.has_presale_product = contains_presale_product(self.target_product)
            # 检查是否全部为京东配送
            self.is_all_jd_delivery = is_all_jd_delivery(self.target_product)

            self.order_price_threshold = 0
            self.log_stream_info('下单价格阈值           %s元', self.get_target_product_price_threshold())
            self.log_stream_info('提前下单时间           %sms', self.order_leading_in_millis)

            #  清空购物车
            self.log_stream_info('清空购物车')
            self.clear_cart()

            self.log_stream_info('重要：抢购结束前不要再添加任何商品到购物车, 目标商品会被自动添加')

            # 获取cookie用户信息
            self.user_id, self.jxsid = self._get_user_info_from_cookie()

            self.log_stream_info('==========================初始化抢购完毕=================================')
        except Exception as e:
            traceback.print_exc()
            self.log_stream_error('初始化秒杀失败')
            self.execution_failure = True
            return False

        return True

    def exec_reserve_seckill_by_time(self, target_time):
        """定时抢购`预约抢购商品`

        预约抢购商品特点：
            1.需要提前点击预约
            2.大部分此类商品在预约后自动加入购物车，在购物车中可见但无法勾选✓，也无法进入到结算页面（重要特征）
            3.到了抢购的时间点后，才能勾选并结算下单
            4.需要提前更新地址以避免下单出现地址无法配送错误

        注意：
            1.请在抢购开始前手动清空购物车中此类无法勾选的商品！（因为脚本在执行清空购物车操作时，无法清空不能勾选的商品）

        :param target_time: 下单时间，例如：'2018-09-28 22:45:50.000'
        :return:
        """
        order_id_list = []

        try:
            if self.is_debug_mode:
                self.log_stream_info('=========================================================================')
                self.log_stream_info('                 注意当前为debug模式，不会下单                             ')
                self.log_stream_info('=========================================================================')

            self.log_stream_info('开始抢购前的准备')
            adjusted_target_time = self.actions_before_target_time(target_time)
            # 设置取消检查点
            if not adjusted_target_time and not self.execution_keep_running:
                return []
            
            # 等待到下单时间
            title = '抢购'
            t = Timer(service_ins=self, target_time=adjusted_target_time, cache_key=self.execution_cache_key)
            running_flag = t.start(title)
            if not running_flag:
                self.execution_keep_running = False
                return []

            self.log_stream_info('===============================提交订单===================================')

            # 开始下单时间
            t_order_start = get_now_datetime()

            order_id = ''
            if not self.is_debug_mode:
                if not self.is_marathon_mode:
                
                    # 下单参数
                    submit_retry_count = 1
                    submit_interval = 0.1
                    is_multi_thread = False
                    
                    # order_id = ''
                    order_id = self.submit_order_with_retry(is_multi_thread, submit_retry_count, submit_interval)

                    if order_id:
                        order_id_list.append(order_id)

                    # 秒杀商品检查首次下单价格
                    item = self.target_product
                    if item['is_seckill_product']:
                        is_check_price = True
                        is_send_message = False
                        order_id_list = self.process_orders(order_id_list, is_check_price, is_send_message)
                else:
                    # marathon模式
                    submit_retry_count = 10
                    submit_interval = 0.1
                    order_id = self.exec_marathon_seckill(self.target_sku_id, self.target_sku_num, submit_retry_count, submit_interval)
                    if not order_id and not self.execution_keep_running:
                        return []
                    if order_id:
                        order_id_list.append(order_id)

                # 下单失败，继续使用有货下单模式抢购
                if not order_id_list or len(order_id_list) == 0:
                    order_id_list = self.post_failure_try()
            
            # 结束后步骤
            order_id_list = self.actions_after_order_submit(order_id_list, target_time, t_order_start)

            if not order_id_list or len(order_id_list) == 0:
                return False
            else:
                order_id = order_id_list[0]
                self.save_order(order_id)

            self.log_stream_info('=====================抢购结束[时间提前:%sms][Debug模式:%s]============================', self.order_leading_in_millis, self.bool_map[str(self.is_debug_mode)])

            # for submitted_order_id in order_id_list:
            #     self.cancel_order(submitted_order_id)
        except Exception as e:
            self.log_stream_error('秒杀失败')
            traceback.print_exc()
            self.execution_failure = True
            return []

        return order_id_list

    @fetch_latency
    def post_failure_try(self):
        """秒杀失败后，继续使用有货下单模式抢购try_in_mins分钟
        :param try_in_mins: 继续刷新库错多少分钟
        :return:
        """

        if not self.is_marathon_mode:
            self.log_stream_info('商品抢购失败，将继续使用有货下单模式刷新库存%s次, 每次间隔%ss', int(self.try_post_failure_count), self.try_post_failure_interval)
            submit_interval=5
            stock_interval = self.try_post_failure_interval
            self.log_stream_info('====================等待下单间隔期间监控%s 库存情况====================', self.target_sku_id)

            try_until_datetime = datetime_offset_in_milliesec(get_now_datetime(), 5 * 1000)
            round = 0
            while True:
                now_time_with_offset = datetime_offset_in_milliesec(get_now_datetime(), stock_interval)
                if now_time_with_offset > try_until_datetime:
                    break
                else:
                    self.if_item_can_be_ordered(round=round, is_random_check_stock=True)
                    round += 1
                    if not sleep_with_check(stock_interval, self.execution_cache_key):
                        self.execution_keep_running = False
                        return []
        else:
            self.log_stream_info('商品抢购失败，将继续使用有货下单模式刷新库存%s分钟', self.try_post_failure_in_mins)
            submit_interval=0.1
            stock_interval=1

        self.is_post_submit_order_failure = True

        order_id_list = self.buy_item_in_stock(stock_interval, submit_retry=1, submit_interval=submit_interval, is_post_submit_order_failure=self.is_post_submit_order_failure, try_in_mins=self.try_post_failure_in_mins)
        return order_id_list


    def buy_item_in_stock(self, stock_interval=1, submit_retry=1, submit_interval=5, is_post_submit_order_failure=False, try_in_mins=5):
        """根据库存自动下单商品
        :param stock_interval: 查询库存时间间隔，可选参数，默认3秒
        :param submit_retry: 提交订单失败后重试次数，可选参数，默认3次
        :param submit_interval: 提交订单失败后重试时间间隔，可选参数，默认5秒
        :param is_post_submit_order_failure: 是否抢购失败后继续尝试下单
        :param try_in_mins: 抢购失败后继续尝试下单多少分钟
        :return:
        """
        refresh_order_interval = 1000
        refresh_order_count = 1

        # 每多少次库存检测之后测试是否秒杀售出率
        is_seckill_sold_out_interval = self.is_seckill_sold_out_interval
        is_seckill_sold_out_count = 0

        # 多少次秒杀售出率100%后退出检测
        is_seckill_sold_out_total_count = 1
        is_seckill_sold_out_total_count_threshold = self.is_seckill_sold_out_total_count_threshold
        total_check_stock_count = 1

        check_stock_reduced_interval = self.check_stock_reduced_interval
        original_stock_interval = stock_interval

        is_random_check_stock = True
        is_reduced_frequency = False

        order_id_list = []
        sku_id = self.target_sku_id
        num = self.target_sku_num

        if is_post_submit_order_failure:
            try_until_datetime = datetime_offset_in_milliesec(get_now_datetime(), try_in_mins * 60 * 1000)

        self.log_stream_info('====================开始有货下单模式：商品 %s 有货并且未下架会尝试下单====================', sku_id)
        should_countinue = True
        while should_countinue:
            # 非marathon模式, 判断时间是否继续
            if is_post_submit_order_failure and self.is_marathon_mode: 
                now_time = get_now_datetime()
                if now_time > try_until_datetime:
                    should_countinue = False
                    self.log_stream_info('抢购%s继续下单模式结束, 下次再努力', sku_id)
                    continue
            if not self.is_marathon_mode: 
                # 检查是否秒杀全部售出
                item = self.target_product
                if item['is_seckill_product']:
                    # 如果秒杀商品已恢复原价，退出
                    if self.price_resumed:
                        self.log_stream_info("商品%s已恢复非秒杀价，无需继续刷新，程序退出", sku_id)
                        should_countinue = False
                        self.price_resumed = False
                        return []
                    if is_seckill_sold_out_count == 0 or is_seckill_sold_out_count == is_seckill_sold_out_interval:
                        if is_seckill_sold_out_count == is_seckill_sold_out_interval:
                            is_seckill_sold_out_count = 0
                        is_seckill_item_sold_out = self.is_seckill_item_sold_out(sku_id)
                        if is_seckill_item_sold_out:
                            self.log_stream_info('商品%s 秒杀价售出率: [%s]', sku_id, str(is_seckill_item_sold_out))
                        else:
                            self.log_stream_info('商品%s 秒杀价售出率检测失败', sku_id)
                        if is_seckill_item_sold_out == 100 or not is_seckill_item_sold_out:
                            if is_seckill_sold_out_total_count != is_seckill_sold_out_total_count_threshold:
                                self.log_stream_info('第[%s/%s]次检测到商品%s 秒杀价全部售出或检测售出率失败, 继续刷新库存', is_seckill_sold_out_total_count, is_seckill_sold_out_total_count_threshold, sku_id)
                                is_seckill_sold_out_total_count += 1
                            else:
                                self.log_stream_info('第[%s/%s]次检测到商品%s 秒杀价全部售出或检测售出率失败, 退出继续下单模式', is_seckill_sold_out_total_count, is_seckill_sold_out_total_count_threshold, sku_id)
                                should_countinue = False
                                continue
                is_seckill_sold_out_count += 1      

                # 检查库存
                if total_check_stock_count != self.try_post_failure_count:
                    self.log_stream_info('[%s/%s]检测商品%s 库存', total_check_stock_count, self.try_post_failure_count, sku_id)
                    total_check_stock_count += 1
                else:
                    # 检查库存结束，如果秒杀商品没有全部售出，降低频率继续刷新
                    if item['is_seckill_product']:
                        is_seckill_item_sold_out = self.is_seckill_item_sold_out(sku_id)
                        if is_seckill_item_sold_out == 100:
                            self.log_stream_info('[%s/%s]检测商品%s 库存无货，秒杀商品全部售出, 退出继续下单模式', total_check_stock_count, self.try_post_failure_count, sku_id)
                            should_countinue = False
                            continue
                        else:
                            total_check_stock_count = 1
                            stock_interval = self.try_post_failure_not_sold_out_interval
                            is_reduced_frequency = True
                            self.log_stream_info('商品没有全部售出，重置库存刷新计数，每%s秒刷新一次库存', stock_interval)
                    else:
                        should_countinue = False
                        continue
                # 检查库存
                is_can_be_ordered = False
                try:
                    # 刷新库存大于阈值以后 切换为单接口模式
                    if total_check_stock_count > self.random_stock_check_threshold:
                        is_random_check_stock = False
                    is_can_be_ordered, should_reduce_interval = self.if_item_can_be_ordered(round=total_check_stock_count, is_random_check_stock=is_random_check_stock)
                except Exception as e:
                    self.log_stream_error(e)
                    self.log_stream_info('查询库存api触发流量限制，切换检查库存方式')
                    if not is_random_check_stock:
                        self.log_stream_error('单模式查询库存api触发流量限制，退出程序，考虑更换ip')
                        return False
                    is_random_check_stock = False
                    stock_interval = self.single_stock_check_interval
                if not is_can_be_ordered:
                    # 如果没有全部售出, 则使用高频率刷新库存
                    if not is_reduced_frequency:
                        if should_reduce_interval:
                            stock_interval = stock_interval - check_stock_reduced_interval
                            if stock_interval < 0:
                                stock_interval = 0
                        else:
                            stock_interval = original_stock_interval
                    
                    self.log_stream_info('%s 没有库存，%ss后重试 ', sku_id, stock_interval)
                    if not sleep_with_check(stock_interval, self.execution_cache_key):
                        self.execution_keep_running = False
                        return []

                    refresh_order_count = refresh_order_count + 1
                    if refresh_order_count == refresh_order_interval:
                        self.get_order_coupons()
                        refresh_order_count = 0
                else:
                    self.log_stream_info('%s 发现库存，开始下单', sku_id)

                    # 非活动商品直接下单
                    if not is_post_submit_order_failure:
                        self.log_stream_info('非抢购/秒杀模式，直接下单')
                        is_multi_thread = False
                        # order_id = ''
                        order_id = self.submit_order_with_retry(is_multi_thread, submit_retry, submit_interval)
                        if order_id:
                            should_countinue = False
                            order_id_list.append(order_id)
                            continue
                        else:
                            if not sleep_with_check(stock_interval, self.execution_cache_key):
                                self.execution_keep_running = False
                                return []
                    else:
                        # 检查是否仍为抢购价格
                        # 获取当前商品信息
                        item = self.target_product
                        if item['is_seckill_product']:
                            # 下单
                            is_multi_thread = False
                            # order_id = ''
                            order_id = self.submit_order_with_retry(is_multi_thread, submit_retry, submit_interval)
                            if order_id:
                                should_countinue = False
                                # 获取秒杀价格
                                seckill_price = float(item['seckill_info']['promo_price'])
                                # 如果不是秒杀价，取消订单
                                order_list = self.get_order_info(silent=True)
                                for order_info_item in order_list:
                                    if str(order_id) == str(order_info_item['order_id']):
                                        submitted_price = float(order_info_item['sum_price'])
                                        most_delivery_fee = self.most_delivery_fee
                                        if submitted_price > (seckill_price + most_delivery_fee):
                                            self.log_stream_info("商品%s已恢复非秒杀价，下单价格%s, 取消订单，无需继续刷新，程序退出", sku_id, submitted_price)
                                            self.cancel_order(order_id)
                                            break
                                        else:
                                            order_id_list.append(order_id)
                                            break
                            else:
                                if not sleep_with_check(stock_interval, self.execution_cache_key):
                                    self.execution_keep_running = False
                                    return []
                        else:
                            # 预约商品，有货直接下单
                            is_multi_thread = False
                            order_id = self.submit_order_with_retry(is_multi_thread, submit_retry, submit_interval)
                            if order_id:
                                should_countinue = False
                                order_id_list.append(order_id)
                                continue
                            else:
                                if not sleep_with_check(stock_interval, self.execution_cache_key):
                                    self.execution_keep_running = False
                                    return []
            else:
                # marathon模式
                submit_retry_count = 1
                submit_interval = 0.1
                order_id = self.exec_marathon_seckill(sku_id, num, submit_retry_count, submit_interval)
                if order_id:
                    should_countinue = False
                    order_id_list.append(order_id)
                    if not sleep_with_check(submit_interval, self.execution_cache_key):
                        self.execution_keep_running = False
                        return []
                    continue
                else:
                    if not self.execution_keep_running:
                        should_countinue = False
                        return []

        return order_id_list

    def is_seckill_item_sold_out(self, sku_id):
        try:
            resp_json = self.batch_load_seckill_gid()
            seckill_list = resp_json['miaoShaList']
            for seckill_item in seckill_list:
                if seckill_item['wareId'] == str(sku_id):
                    if 'soldRate' in seckill_item:
                        return seckill_item['soldRate']
                    elif 'soldRateText' in seckill_item:
                        return seckill_item['soldRateText']
                    else:
                        return False
            return False
        except Exception as e:
            self.log_stream_error('查询 %s 已售率发生异常, resp: %s, exception: %s', sku_id, resp_json, e)
            traceback.print_exc()
            return False

    def get_seckill_item_stock(self, sku_id):
        try:
            parsed_arrange_list = self.batch_load_seckill(is_force_refresh=True, is_ignore_limit=True)
            for gid_item in parsed_arrange_list:
                seckill_list = gid_item['seckill_items']
                for seckill_item in seckill_list:
                    if str(seckill_item['wareId']) == str(sku_id):
                        if 'specificationLabel' in seckill_item:
                            return seckill_item['specificationLabel']
                        else:
                            return ''
            return False
        except Exception as e:
            self.log_stream_error('查询 %s 秒杀数量发生异常, exception: %s', sku_id, e)
            traceback.print_exc()
            return False

    def should_read_from_cache(self, seckill_jd_cache_value):
        if not seckill_jd_cache_value:
            return False
        else:
            current_ts = get_now_datetime()
            current_day = current_ts.day
            current_hour = current_ts.hour
            try:
                cache_last_update_ts = str_to_datetime(seckill_jd_cache_value['last_update_ts'])
                cache_last_update_day = cache_last_update_ts.day
                cache_last_update_hour = cache_last_update_ts.hour

                if cache_last_update_day != current_day or (current_hour - cache_last_update_hour >= 2) or ((cache_last_update_hour + 1) % 2 == 0 and current_hour >= (cache_last_update_hour + 1)):
                    return False
                else:
                    return True

            except Exception as e:
                self.log_stream_error('获取缓存秒杀信息失败, exception: %s', e)
                return False

    def execute_arrangement(self, execution_arrangement_array, login_username, nick_name, leading_time, force_run=False):
        self.login_username = login_username
        self.nick_name = nick_name

        # steam message
        self.logger_stream = login_username + '_' + nick_name
        self.logger_group = login_username + '_' + nick_name
        self.logger_consumer = nick_name
        self.stream_enabled = True

        # 检查是否已有计划运行中
        if not force_run:
            if(self.jd_user_has_running_task(login_username, nick_name)):
                self.log_stream_info('=========================================================================')
                self.log_stream_info('用户%s已有运行计划，忽略此次运行', self.nick_name)
                self.log_stream_info('=========================================================================')
                return

        # 添加运行flag
        self.execution_cache_key = login_username + '_' + nick_name + '_arrangement_running'
        execution_cache_val = {
            'cancelled': False
        }
        self.cache_dao.put(self.execution_cache_key, execution_cache_val)

        # delete stream
        self.cache_dao.delete_stream(self.logger_stream)
        
        # create stream
        level = 'info'
        self.cache_dao.push_to_stream(self.logger_stream, build_stream_message('初始化运行日志', level))
        # self.cache_dao.create_stream_group(self.logger_stream, self.logger_group)

        if leading_time:
            self.order_leading_in_millis = float(leading_time)

        # 初始化状态
        for arrangement_item in execution_arrangement_array:
            target_time = arrangement_item.get('target_time').strip()
            
            # 更新分步状态
            self.update_arrangement_status(execution_arrangement_array, target_time, login_username, nick_name, ARRANGEMENT_EXEC_STATUS_PLANNED)

        # 开始分步执行
        for arrangement_item in execution_arrangement_array:
            sku_id = arrangement_item.get('sku_id').strip()
            num = arrangement_item.get('num')
            target_time = arrangement_item.get('target_time').strip()
            
            self.log_stream_info('=========================================================================')
            self.log_stream_info('准备执行抢购计划:时间%s, 商品id:%s', target_time, sku_id)
            self.log_stream_info('=========================================================================')
            self.update_arrangement_status(execution_arrangement_array, target_time, login_username, nick_name, ARRANGEMENT_EXEC_STATUS_RUNNING)
            if self.prepare_on_init(target_time, sku_id, num):
                order_id = self.exec_reserve_seckill_by_time(target_time)
            else:
                order_id = False 
            self.log_stream_info('=========================================================================')
            self.log_stream_info('完成抢购计划:时间%s, 商品id:%s', target_time, sku_id)
            self.log_stream_info('是否成功下单:%s', self.bool_map[str(bool(order_id))])
            self.log_stream_info('=========================================================================')

            if self.execution_failure:
                self.update_arrangement_status(execution_arrangement_array, target_time, login_username, nick_name, ARRANGEMENT_EXEC_STATUS_ERROR)
                self.log_stream_info('=========================================================================')
                self.log_stream_info('用户%s抢购计划失败，发现异常', self.nick_name)
                self.log_stream_info('=========================================================================')
                return

            if not self.execution_keep_running:
                self.update_arrangement_status(execution_arrangement_array, target_time, login_username, nick_name, ARRANGEMENT_EXEC_STATUS_CANCELLED)
                self.log_stream_info('=========================================================================')
                self.log_stream_info('用户%s抢购计划已终止', self.nick_name)
                self.log_stream_info('=========================================================================')
                return

            if order_id:
                self.update_arrangement_status(execution_arrangement_array, target_time, login_username, nick_name, ARRANGEMENT_EXEC_STATUS_SUCCEEDED)
            else:
                self.update_arrangement_status(execution_arrangement_array, target_time, login_username, nick_name, ARRANGEMENT_EXEC_STATUS_FAILED)

    def read_execution_log(self, login_username, nick_name, last_id):
        # steam message
        self.logger_stream = login_username + '_' + nick_name
        self.logger_group = login_username + '_' + nick_name
        self.logger_consumer = nick_name
        
        # read log from cache
        # message_list = self.cache_dao.read_from_stream_group(self.logger_stream, self.logger_group, self.logger_consumer)
        message_list = self.cache_dao.read_from_stream(self.logger_stream, last_id)

        return message_list

    def log_stream_info(self, message, *args):
        if self.stream_enabled:
            level = 'Info'
            self.cache_dao.push_to_stream(self.logger_stream, build_stream_message(message, level, args))
        self.logger.info(message, *args)

    def log_stream_error(self, message, *args):
        if self.stream_enabled:
            level = 'Error'
            if isinstance(message, RestfulException):
                message = message.msg
            self.cache_dao.push_to_stream(self.logger_stream, build_stream_message(message, level, args))
        self.logger.error(message, *args)

    def log_info(self, message, *args):
        self.logger.info(message, *args)

    def log_error(self, message, *args):
        self.logger.error(message, *args)

    def is_jd_user_status_in_cache(self, arrangement_status_cache_value, nick_name):
        if not arrangement_status_cache_value:
            return False
        for arrangement_status_item in arrangement_status_cache_value:
            if nick_name == arrangement_status_item['nick_name']:
                return True
        return False

    def jd_user_has_running_task(self, login_username, nick_name):
        self.execution_status_cache_key = 'seckill_arrangement_' + login_username
        arrangement_status_cache_value = self.cache_dao.get(self.execution_status_cache_key)
        if arrangement_status_cache_value:
            for arrangement_status_item in arrangement_status_cache_value:
                if arrangement_status_item['nick_name'] == nick_name:
                    for arrangement_status_item_each_target_time in arrangement_status_item['seckill_arangement']:
                        if arrangement_status_item_each_target_time['status'] == ARRANGEMENT_EXEC_STATUS_RUNNING:
                            return True
        return False

    def add_or_remove_arrangement(self, leading_time, target_time, login_username, nick_name, is_add):
        lock = redis_lock.Lock(self.cache_dao.get_cache_client(), LOCK_KEY_SECKILL_ARRANGEMENT + login_username)
        
        try:
            while not lock.acquire(blocking=False):
                time.sleep(0.05)

            self.execution_status_cache_key = 'seckill_arrangement_' + login_username
            arrangement_status_cache_value = self.cache_dao.get(self.execution_status_cache_key)

            # 如果是添加sku
            if is_add:
                # 如果缓存不存在，初始化缓存
                if not arrangement_status_cache_value:
                    arrangement_status_cache_value = []

                # 如果用户不存在，添加用户和商品
                if not self.is_jd_user_status_in_cache(arrangement_status_cache_value, nick_name):
                    arrangement_cache_status_item = {
                        'nick_name': nick_name,
                        'leading_time': leading_time,
                        'seckill_arangement':[]
                    }
                    arrangement_cache_status_arangement_item = {
                        'target_time': target_time,
                        'status': ARRANGEMENT_EXEC_STATUS_PLANNED
                    }
                    arrangement_cache_status_item['seckill_arangement'].append(arrangement_cache_status_arangement_item)
                    arrangement_status_cache_value.append(arrangement_cache_status_item)
                else:
                    # 如果用户已经存在，加入商品
                    for index, arrangement_cache_status_item in enumerate(arrangement_status_cache_value):
                        if arrangement_cache_status_item['nick_name'] == nick_name:
                            arrangement_cache_status_arangement_item = {
                                'target_time': target_time,
                                'status': ARRANGEMENT_EXEC_STATUS_PLANNED
                            }
                            arrangement_cache_status_item['seckill_arangement'].append(arrangement_cache_status_arangement_item)
            # 如果是删除商品
            else:
                # 如果缓存不存在，退出
                if not arrangement_status_cache_value:
                    return
                # 如果用户不存在，退出
                elif not self.is_jd_user_status_in_cache(arrangement_status_cache_value, nick_name):
                    return
                else:
                    # 如果用户已经存在，并且找到商品，删除
                    for index, arrangement_status_item in enumerate(arrangement_status_cache_value):
                        if arrangement_status_item['nick_name'] == nick_name:
                            for index_inner, arrangement_status_item_each_target_time in enumerate(arrangement_status_item['seckill_arangement']):
                                if arrangement_status_item_each_target_time['target_time'] == target_time:
                                    del arrangement_status_item_each_target_time[index_inner]
            # 更新缓存
            self.cache_dao.put(self.execution_status_cache_key, arrangement_status_cache_value, DEFAULT_CACHE_STATUS_TTL)
        finally:
            if lock and lock.locked():
                lock.release()

    def update_arrangement_status(self, execution_arrangement_array, target_time, login_username, nick_name, status):
        lock = redis_lock.Lock(self.cache_dao.get_cache_client(), LOCK_KEY_SECKILL_ARRANGEMENT + login_username)
        
        try:
            while not lock.acquire(blocking=False):
                time.sleep(0.05)

            self.execution_status_cache_key = 'seckill_arrangement_' + login_username
            arrangement_status_cache_value = self.cache_dao.get(self.execution_status_cache_key)

            if status == ARRANGEMENT_EXEC_STATUS_PLANNED:
                if self.is_jd_user_status_in_cache(arrangement_status_cache_value, nick_name):
                    for index, arrangement_status_item in enumerate(arrangement_status_cache_value):
                        if arrangement_status_item['nick_name'] == nick_name:
                            del arrangement_status_cache_value[index]
                            break

            if not arrangement_status_cache_value:
                arrangement_status_cache_value = []
                arrangement_cache_status_item = {
                    'nick_name': nick_name,
                    'leading_time': self.order_leading_in_millis,
                    'seckill_arangement':[]
                }
                for arrangement_item in execution_arrangement_array:
                    arrangement_cache_status_arangement_item = {
                        'target_time': arrangement_item.get('target_time'),
                        'status': ARRANGEMENT_EXEC_STATUS_PLANNED,
                        'failure_msg': ''
                    }
                    arrangement_cache_status_item['seckill_arangement'].append(arrangement_cache_status_arangement_item)
                arrangement_status_cache_value.append(arrangement_cache_status_item)
            else:
                if not self.is_jd_user_status_in_cache(arrangement_status_cache_value, nick_name):
                    arrangement_cache_status_item = {
                        'nick_name': nick_name,
                        'leading_time': self.order_leading_in_millis,
                        'seckill_arangement':[]
                    }
                    for arrangement_item in execution_arrangement_array:
                        arrangement_cache_status_arangement_item = {
                            'target_time': arrangement_item.get('target_time'),
                            'status': ARRANGEMENT_EXEC_STATUS_PLANNED,
                            'failure_msg': ''
                        }
                        arrangement_cache_status_item['seckill_arangement'].append(arrangement_cache_status_arangement_item)
                    arrangement_status_cache_value.append(arrangement_cache_status_item)
                else:
                    for arrangement_status_item in arrangement_status_cache_value:
                        if arrangement_status_item['nick_name'] == nick_name:
                            if status == ARRANGEMENT_EXEC_STATUS_CANCELLED:
                                for arrangement_status_item_each_target_time in arrangement_status_item['seckill_arangement']:
                                    if arrangement_status_item_each_target_time['target_time'] == target_time:
                                        if arrangement_status_item_each_target_time['status'] == ARRANGEMENT_EXEC_STATUS_RUNNING:
                                            arrangement_status_item_each_target_time['status'] = status,
                                            arrangement_status_item_each_target_time['failure_msg'] = ''
                            else:
                                for arrangement_status_item_each_target_time in arrangement_status_item['seckill_arangement']:
                                    if arrangement_status_item_each_target_time['target_time'] == target_time:
                                        arrangement_status_item_each_target_time['status'] = status
                                        arrangement_status_item_each_target_time['failure_msg'] = self.failure_msg

            self.cache_dao.put(self.execution_status_cache_key, arrangement_status_cache_value, DEFAULT_CACHE_STATUS_TTL)
        finally:
            if lock and lock.locked():
                lock.release()

    def cancel_arrangement(self, execution_arrangement_array, login_username, nick_name):
        lock = redis_lock.Lock(self.cache_dao.get_cache_client(), LOCK_KEY_CANCEL_SECKILL_ARRANGEMENT + login_username)
        
        try:
            while not lock.acquire(blocking=False):
                time.sleep(0.05)
            # 更新执行状态
            self.execution_cache_key = login_username + '_' + nick_name + '_arrangement_running'
            execution_cache_val = {
                'cancelled': True
            }
            self.cache_dao.put(self.execution_cache_key, execution_cache_val, DEFAULT_CACHE_STATUS_TTL)

            for arrangement_item in execution_arrangement_array:
                target_time = arrangement_item.get('target_time').strip()
                # 更新分步状态
                self.update_arrangement_status(execution_arrangement_array, target_time, login_username, nick_name, ARRANGEMENT_EXEC_STATUS_CANCELLED)
        finally:
            if lock and lock.locked():
                lock.release()

    def get_arrangement_status(self, login_username):
        self.execution_status_cache_key = 'seckill_arrangement_' + login_username
        return self.cache_dao.get(self.execution_status_cache_key)

    def delete_arrangement_item(self, login_username, nick_name, target_time=None):
        lock = redis_lock.Lock(self.cache_dao.get_cache_client(), LOCK_KEY_SECKILL_ARRANGEMENT + login_username)
        
        try:
            while not lock.acquire(blocking=False):
                time.sleep(0.05)

            self.execution_status_cache_key = 'seckill_arrangement_' + login_username
            arrangement_status_cache_value = self.cache_dao.get(self.execution_status_cache_key)
            if not arrangement_status_cache_value:
                return 

            if not self.is_jd_user_status_in_cache(arrangement_status_cache_value, nick_name):
                return
            else:
                if not target_time:
                    for i, arrangement_status_item in enumerate(arrangement_status_cache_value):
                        if arrangement_status_item['nick_name'] == nick_name:
                            del arrangement_status_cache_value[i]
                else:
                    for i, arrangement_status_item in enumerate(arrangement_status_cache_value):
                            if arrangement_status_item['nick_name'] == nick_name:
                                for j, arrangement_status_item_each_target_time in enumerate(arrangement_status_item['seckill_arangement']):
                                    if arrangement_status_item_each_target_time['target_time'] == target_time:
                                        del arrangement_status_item['seckill_arangement'][j]
                                        if len(arrangement_status_item['seckill_arangement']) == 0:
                                            del arrangement_status_cache_value[i]
                                        break
            self.cache_dao.put(self.execution_status_cache_key, arrangement_status_cache_value, DEFAULT_CACHE_STATUS_TTL)
        finally:
            if lock and lock.locked():
                lock.release()

    def add_custom_sku_info_to_cache(self, login_username, sku_data):
        lock = redis_lock.Lock(self.cache_dao.get_cache_client(), LOCK_KEY_SECKILL_ARRANGEMENT + login_username)
        
        try:
            while not lock.acquire(blocking=False):
                time.sleep(0.05)

            custom_sku_data_cache_key = 'custom_sku_data_' + login_username
            self.cache_dao.put(custom_sku_data_cache_key, sku_data, DEFAULT_CACHE_STATUS_TTL)
        finally:
            if lock and lock.locked():
                lock.release()

    def get_custom_sku_info_from_cache(self, login_username):
        custom_sku_data_cache_key = 'custom_sku_data_' + login_username
        return self.cache_dao.get(custom_sku_data_cache_key)

    def delete_custom_sku_info_from_cache(self, login_username):
        lock = redis_lock.Lock(self.cache_dao.get_cache_client(), LOCK_KEY_SECKILL_ARRANGEMENT + login_username)
        try:
            while not lock.acquire(blocking=False):
                time.sleep(0.05)

            custom_sku_data_cache_key = 'custom_sku_data_' + login_username
            self.cache_dao.delete(custom_sku_data_cache_key)
        finally:
            if lock and lock.locked():
                lock.release()

    def get_adjusted_server_time_from_cache(self, target_time):
        lock = redis_lock.Lock(self.cache_dao.get_cache_client(), LOCK_KEY_ADJUST_SERVER_TIME + target_time)
        
        try:
            while not lock.acquire(blocking=False):
                time.sleep(0.05)

            adjust_server_time_cache_key = LOCK_KEY_ADJUST_SERVER_TIME + target_time
            json_obj = self.cache_dao.get(adjust_server_time_cache_key)
            if not json_obj:
                json_obj = {
                    'status': 'running',
                    'adjusted_server_time': target_time
                }
                self.cache_dao.put(adjust_server_time_cache_key, json_obj, DEFAULT_CACHE_TTL)
                return None
            elif json_obj['status'] == 'running':
                if lock.locked():
                    lock.release()
                time.sleep(10)
                json_obj = self.cache_dao.get(adjust_server_time_cache_key)
                if json_obj['status'] == 'finished':
                    return json_obj['adjusted_server_time']
                else:
                    return None
            else:
                return json_obj['adjusted_server_time']
        finally:
                try:
                    if lock and lock.locked():
                        lock.release()
                except Exception as e:
                    pass
    
    def put_adjusted_server_time_in_cache(self, target_time, adjusted_server_time, status):
        lock = redis_lock.Lock(self.cache_dao.get_cache_client(), LOCK_KEY_ADJUST_SERVER_TIME + target_time)
        
        try:
            while not lock.acquire(blocking=False):
                time.sleep(0.05)

            adjust_server_time_cache_key = LOCK_KEY_ADJUST_SERVER_TIME + target_time
            json_obj = {
                'status': status,
                'adjusted_server_time': adjusted_server_time
            }
            self.cache_dao.put(adjust_server_time_cache_key, json_obj, DEFAULT_CACHE_TTL)
        finally:
            if lock and lock.locked():
                lock.release()

    def batch_load_seckill(self, is_force_refresh=False, is_ignore_limit=False):
        parsed_arrange_list = []
        # get predict list
        parsed_predict_list = self.get_sku_predict()
        try:
            should_read_from_cache_flag = True
            # check cache
            if is_force_refresh:
                should_read_from_cache_flag = False
            else:
                seckill_jd_cache_value = self.cache_dao.get(SECKILL_INFO_CACHE_KEY)
                should_read_from_cache_flag = self.should_read_from_cache(seckill_jd_cache_value)
            if should_read_from_cache_flag:
                return {
                    'parsed_arrange_list': seckill_jd_cache_value['parsed_arrange_list'],
                    'parsed_predict_list': parsed_predict_list
                }
            else:
                # get seckill items
                resp_json = self.batch_load_seckill_gid()
                arrange_list = resp_json['groups']
                now_dt = get_now_datetime()
                now_dt_ts = get_timestamp_in_milli_sec(now_dt)

                for item in arrange_list:
                    if is_ignore_limit:
                        parsed_arrange_list.append(item)
                    else:
                        if now_dt_ts < item['startTimeMills']:
                            parsed_arrange_list.append(item)

                for item in parsed_arrange_list:
                    gid = item['gid']

                    # 时间段解析
                    resp_json_each_gid = self.batch_load_seckill_gid(gid)
                    parsed_resp_json_each_gid = []
                    for seckill_item in resp_json_each_gid['miaoShaList']:
                        if not 'tagText' in seckill_item:
                            seckill_item['tagText'] = 'b'
                        else:
                            seckill_item['tagText'] = 'a'

                    # resp_json_each_gid['miaoShaList'] = sorted(resp_json_each_gid['miaoShaList'], key=lambda k: k['rate'])
                    resp_json_each_gid['miaoShaList'] = sorted(sorted(resp_json_each_gid['miaoShaList'], key=lambda k: k['rate']), key=lambda k: k['tagText'])

                    for seckill_item in resp_json_each_gid['miaoShaList']:
                        if seckill_item['tagText'] == 'b':
                            seckill_item['tagText'] = ''
                        else:
                            seckill_item['tagText'] = '超级秒杀'

                    for index, seckill_item in enumerate(resp_json_each_gid['miaoShaList']):
                        if not is_ignore_limit:
                            if index < self.seckill_skus_limit:
                                # if 'tagText' in seckill_item and seckill_item['tagText'] == '超级秒杀':
                                seckill_item['imageurl'] = 'https:' + seckill_item['imageurl']
                                seckill_item['rate'] = seckill_item['rate'].replace('折','')
                                if 'wareId' in seckill_item:
                                    item_info = self.get_item_detail_info(seckill_item['wareId'], is_wait_for_limit=True, is_check_stock = False)
                                    seckill_item['isReserveProduct'] = item_info['is_reserve_product']
                                    seckill_item['isFreeDelivery'] = item_info['is_free_delivery']
                                    # seckill_item['list_price'] =  item_info['list_price']
                                else:
                                    self.log_stream_info(seckill_item)
                                parsed_resp_json_each_gid.append(seckill_item)
                        else:
                            seckill_item['imageurl'] = 'https:' + seckill_item['imageurl']
                            seckill_item['rate'] = seckill_item['rate'].replace('折','')
                            parsed_resp_json_each_gid.append(seckill_item)
                    item['seckill_items'] = parsed_resp_json_each_gid
                if not is_ignore_limit:
                    # put to cache
                    seckill_jd_cache_value = {
                        'parsed_arrange_list': parsed_arrange_list,
                        'last_update_ts': datetime_to_str(get_now_datetime())
                    }
                    self.cache_dao.put(SECKILL_INFO_CACHE_KEY, seckill_jd_cache_value, DEFAULT_CACHE_SECKILL_INFO_TTL)
        except Exception as e:
            self.log_stream_error('获取秒杀信息失败')
            self.system_emailer.send(subject='获取秒杀信息失败', content='获取秒杀信息失败')
            raise RestfulException(error_dict['SERVICE']['JD']['GET_BATCH_SECKILL_FAILURE'])

        if is_ignore_limit:
            return parsed_arrange_list
        else:
            return {
                'parsed_arrange_list': parsed_arrange_list,
                'parsed_predict_list': parsed_predict_list
            }

    def batch_load_seckill_gid(self, gid=''):
        url = 'https://api.m.jd.com/api'
        payload = {
            'callback': '',
            '_': str(int(time.time() * 1000)),
            'appid': 'o2_channels',
            'functionId': 'pcMiaoShaAreaList',
            'client': 'pc',
            'clientVersion': '1.0.0',
            'jsonp': '',
            'body': '{}'
        }

        if gid:
            payload['body'] = '{"gid":_gid}'.replace('_gid', str(gid))

        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://miaosha.jd.com/',
        }
        resp = self.sess.post(url=url, data=payload, headers=headers)
        resp_json = parse_json(resp.text)
        if not resp_json:
            raise RestfulException(error_dict['COMMON']['SECKILL_BATCH_LOAD_FAILURE'])
        return resp_json

    def get_sku_predict(self):
        try:
            """获取用户信息
            :return: 用户名
            """
            url = 'http://www.yunshenjia.com/xianbao/index?keyword=&cat=0&discount=2&sort=1'
            headers = {
                'User-Agent': self.user_agent
            }
            resp = self.sess.get(url=url, headers=headers)

            ret_list = []
            soup = BeautifulSoup(resp.text, "html.parser")
            div_content = soup.find('div', {'class': 'content'})
            ul_child = div_content.findChildren("ul" , recursive=False)[0]
            li_list = ul_child.findChildren("li" , recursive=False)
            for li in li_list:
                item_info = {}
                product_onclick_url_splitted = li['onclick'].split('/')
                sku_id = product_onclick_url_splitted[len(product_onclick_url_splitted) - 1].split('.')[0]
                image_src = li.findChildren("img" , recursive=True)[0]['src']
                sku_name = li.findChildren("h2" , recursive=True)[0].text.strip()
                promo_price = li.findChildren("font" , recursive=True)[0].text
                current_price = li.findChildren("h2" , recursive=True)[1].text.strip()
                rate = li.findChildren("h2" , recursive=True)[2].text.strip()
                seckill_start_time_str = li.findChildren("span" , recursive=True)[1].text.split('：')[1]
                # parse time str, e.g 12月13日 14:00:00
                current_dt = get_now_datetime()
                current_year = current_dt.year
                current_month = current_dt.month

                remote_month = int(seckill_start_time_str.split('月')[0])
                if remote_month < current_month:
                    # a new year
                    current_year = current_year + 1

                seckill_start_time_str = str(current_year) + '-' + seckill_start_time_str.replace("月","-").replace("日","")
                startTimeMills = get_timestamp_in_milli_sec(str_to_datetime(seckill_start_time_str, DATETIME_STR_PATTERN_SHORT))
                
                item_info['sku_id'] = sku_id
                item_info['sku_name'] = sku_name
                item_info['imageUrl'] = 'http:' + image_src
                item_info['promo_price'] = promo_price
                item_info['current_price'] = current_price
                item_info['rate'] = rate
                item_info['seckill_start_time_str'] = seckill_start_time_str
                item_info['startTimeMills'] = startTimeMills

                ret_list.append(item_info)
        except Exception as e:
            self.log_stream_error('秒杀线报获取失败')

        return ret_list