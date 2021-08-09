#!/usr/bin/env python
# -*- encoding=utf8 -*-
import datetime
import json
import traceback
import requests
from config.error_dict import error_dict
from exception.restful_exception import RestfulException

class Messenger(object):
    """消息推送类"""

    def __init__(self, sc_key, service_ins):
        if not sc_key:
            raise RestfulException(error_dict['USER']['SC_KEY_BLANK'])
        self.sc_key = sc_key
        self.service_ins = service_ins

    def send(self, text, desp=''):
        if not text.strip():
            self.service_ins.log_stream_error('Text of message is empty!')
            return

        now_time = str(datetime.datetime.now())
        desp = '[{0}]'.format(now_time) if not desp else '{0} [{1}]'.format(desp, now_time)

        try:
            resp = requests.get(
                'https://sc.ftqq.com/{}.send?text={}&desp={}'.format(self.sc_key, text, desp)
            )
            resp_json = json.loads(resp.text)
            if resp_json.get('errno') == 0:
                self.service_ins.log_stream_info('成功发送微信推送信息')
            else:
                self.service_ins.log_stream_error('Fail to send message, reason: %s', resp.text)
        except requests.exceptions.RequestException as req_error:
            self.service_ins.log_stream_error('Request error: %s', req_error)
        except Exception as e:
            traceback.print_exc()
            self.service_ins.log_stream_error('Fail to send message [text: %s, desp: %s]: %s', text, desp, e)
