#!/usr/bin/env python
# -*- encoding=utf8 -*-
import datetime
import json
import traceback
import requests
from config.error_dict import error_dict
from exception.restful_exception import RestfulException
from utils.log import logger

from utils.util import (
    fetch_latency
)


class Messenger(object):
    """消息推送类"""

    def __init__(self, sc_key):
        if not sc_key:
            raise RestfulException(error_dict['USER']['SC_KEY_BLANK'])

        self.sc_key = sc_key

    @fetch_latency
    def send(self, text, desp=''):
        if not text.strip():
            logger.error('Text of message is empty!')
            return

        now_time = str(datetime.datetime.now())
        desp = '[{0}]'.format(now_time) if not desp else '{0} [{1}]'.format(desp, now_time)

        try:
            resp = requests.get(
                'https://sc.ftqq.com/{}.send?text={}&desp={}'.format(self.sc_key, text, desp)
            )
            resp_json = json.loads(resp.text)
            if resp_json.get('errno') == 0:
                logger.info('成功发送微信推送信息')
            else:
                logger.error('Fail to send message, reason: %s', resp.text)
        except requests.exceptions.RequestException as req_error:
            logger.error('Request error: %s', req_error)
        except Exception as e:
            traceback.print_exc()
            logger.error('Fail to send message [text: %s, desp: %s]: %s', text, desp, e)
