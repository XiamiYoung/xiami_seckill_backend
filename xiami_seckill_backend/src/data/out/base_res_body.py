import json
from config.constants import (
    DEFAULT_SUC_MESSAGE,
    SUCCESS_CODE
)

class BaseResBody(object):
    def __init__(self, msg=DEFAULT_SUC_MESSAGE, reason_code=SUCCESS_CODE):
        self.msg = msg
        self.reason_code = reason_code
        self.body = {}

    def to_json_body(self, is_keep_body=True):
        resp = {
            'reasonCode': self.reason_code,
            'msg': self.msg,
            'body': self.body
        }

        if not is_keep_body:
            del resp['body']
        return resp

    def to_str(self, is_keep_body=True):
        return json.dumps(self.to_json_body(is_keep_body))