#!/usr/bin/env python
# -*- encoding=utf8 -*-

class RestfulException(Exception):

    def __init__(self, error_entry):
        self.reason_code = error_entry['reasonCode']
        self.http_code = error_entry['httpCode']
        self.msg = error_entry['msg']
        super().__init__(self.msg)