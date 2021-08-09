#coding:utf-8
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr
import traceback
from config.constants import (
    SMTP_HOST,
    SMTP_PORT 
)

class Emailer:
    def __init__(self, service_ins, email, mail_pass):
        self.mail_host = SMTP_HOST
        self.mail_port = SMTP_PORT
        self.mail_pass = mail_pass
        self.sender = email
        self.receivers = [email]
        self.service_ins = service_ins

    def _format_addr(self, email_addr_str):
        addr = parseaddr(email_addr_str)
        return formataddr(addr)

    def send(self, subject, content):

        message = MIMEText(content, 'html', 'utf-8')

        message['From'] = self._format_addr(self.sender)
        message['To'] =  self._format_addr(self.sender)
        
        subject = subject
        message['Subject'] = Header(subject, 'utf-8') 
        try:
            smtpObj = smtplib.SMTP_SSL(self.mail_host, self.mail_port) 
            smtpObj.login(self.sender, self.mail_pass)
            smtpObj.sendmail(self.sender, self.receivers, message.as_string())
            self.service_ins.log_stream_info('成功发送邮件:%s', self.sender)
        except Exception as e:
            traceback.print_exc()
            self.service_ins.log_stream_error('发送邮件失败:%s', self.sender)
        finally:
            if smtpObj:
                smtpObj.quit()