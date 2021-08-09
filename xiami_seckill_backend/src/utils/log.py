#!/usr/bin/env python
# -*- encoding=utf8 -*-
import logging
import logging.handlers

from config.constants import (
    LOG_FILENAME_PREFIX
)

class Logger(object):
    def __init__(self, login_username=''):
        self.logger = logging.getLogger()
        self.login_username = login_username

    def set_logger(self):
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(processName)s %(threadName)s %(levelname)s: %(message)s')

        logFileName = LOG_FILENAME_PREFIX + ".log"
        if self.login_username:
            logFileName = LOG_FILENAME_PREFIX + "-" + self.login_username + ".log"

        if not self.logger.hasHandlers():
            # file handler
            file_handler = logging.handlers.RotatingFileHandler(
                logFileName, maxBytes=10485760, backupCount=5, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.addHandler(file_handler)

            # console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
        return self.logger