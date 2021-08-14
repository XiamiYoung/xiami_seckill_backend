from models.jd.jd_user_model import JDUser
from django.db import connection
from config.config import global_config
from utils.token_util import (
    encrypt_json
)

db_prop_secret = global_config.get('config', 'db_prop_secret')

class JDUserDao(object):
    
    def delete_by_id(self, id):
        try:
            jd_user = JDUser.objects.get(id = id)
            jd_user.delete()
        finally:
            connection.close()

    def update_jd_user_leading_time(self, user_model, nick_name, user_options):
        try:
            jd_user_qs = JDUser.objects.filter(user=user_model, nick_name=nick_name)
            jd_user_model = jd_user_qs.first()
            if 'leading_time' in user_options:
                jd_user_model.leading_time = int(user_options['leading_time'])
                jd_user_model.save()
        finally:
            connection.close()

    def update_jd_user_pwd(self, user_model, nick_name, user_options):
        try:
            jd_user_qs = JDUser.objects.filter(user=user_model, nick_name=nick_name)
            jd_user_model = jd_user_qs.first()
            if 'jd_pwd' in user_options:
                if user_options['jd_pwd'] != '******' and user_options['jd_pwd'] is not None:
                    jd_pwd_json = {'jd_pwd': user_options['jd_pwd']}
                    jd_user_model.jd_pwd = encrypt_json(jd_pwd_json, db_prop_secret)
                else:
                    jd_user_model.jd_pwd = ''

            jd_user_model.save()
        finally:
            connection.close()

    def update_jd_user_push_token(self, user_model, nick_name, user_options):
        try:
            jd_user_qs = JDUser.objects.filter(user=user_model, nick_name=nick_name)
            jd_user_model = jd_user_qs.first()
            if 'push_token' in user_options:
                push_token_json = {'push_token': user_options['push_token']}
                jd_user_model.push_token = encrypt_json(push_token_json, db_prop_secret)
            else:
                jd_user_model.push_token = ''

            jd_user_model.save()
        finally:
            connection.close()

    def update_jd_user_push_email(self, user_model, nick_name, user_options):
        try:
            jd_user_qs = JDUser.objects.filter(user=user_model, nick_name=nick_name)
            jd_user_model = jd_user_qs.first()
            if 'push_email' in user_options:
                jd_user_model.push_email = user_options['push_email']
            else:
                jd_user_model.push_email = ''

            jd_user_model.save()
        finally:
            connection.close()

    def update_jd_user_enabled(self, user_model, nick_name, enabled):
        try:
            jd_user_qs = JDUser.objects.filter(user=user_model, nick_name=nick_name)
            jd_user_model = jd_user_qs.first()
            jd_user_model.enabled = enabled

            jd_user_model.save()
        finally:
            connection.close()

    def save_or_update_jd_enduser(self, data, user_model):
        try:
            exists = False
            jd_user_model = None
            jd_user_qs = JDUser.objects.filter(user=user_model, nick_name=data['nick_name'])
            user_count = jd_user_qs.count()
            if user_count != 0:
                exists = True
            if exists:
                jd_user_model = jd_user_qs.first()
                jd_user_model.recipient_name = data.get('recipient_name', '')
                jd_user_model.full_addr = data.get('full_addr', '')
                jd_user_model.pc_cookie_status = data.get('pc_cookie_status', False)
                jd_user_model.pc_cookie_str = data.get('pc_cookie_str', '')
                jd_user_model.pc_cookie_ts = data.get('pc_cookie_ts', '')
                jd_user_model.pc_cookie_ts_label = data.get('pc_cookie_ts_label', '')
                jd_user_model.pc_cookie_expire_ts = data.get('pc_cookie_expire_ts', '')
                jd_user_model.pc_cookie_expire_ts_label = data.get('pc_cookie_expire_ts_label', '')
                jd_user_model.mobile = data.get('mobile', '')
                jd_user_model.mobile_cookie_status = data.get('mobile_cookie_status', False)
                jd_user_model.mobile_cookie_str = data.get('mobile_cookie_str', '')
                jd_user_model.mobile_cookie_ts = data.get('mobile_cookie_ts', '')
                jd_user_model.mobile_cookie_ts_label = data.get('mobile_cookie_ts_label', '')
                jd_user_model.mobile_cookie_expire_ts = data.get('mobile_cookie_expire_ts', '')
                jd_user_model.mobile_cookie_expire_ts_label = data.get('mobile_cookie_expire_ts_label', '')
                jd_user_model.leading_time = data.get('leading_time', int(global_config.get('config', 'default_order_leading_in_millis')))
                jd_user_model.enabled = data.get('enabled', True)
                jd_user_model.user = user_model
            else:
                jd_user_model = JDUser(
                                        nick_name = data.get('nick_name', ''),
                                        recipient_name = data.get('recipient_name', ''),
                                        full_addr = data.get('full_addr', ''),
                                        pc_cookie_status = data.get('pc_cookie_status', False),
                                        pc_cookie_str = data.get('pc_cookie_str', ''),
                                        pc_cookie_ts = data.get('pc_cookie_ts', ''),
                                        pc_cookie_ts_label = data.get('pc_cookie_ts_label', ''),
                                        pc_cookie_expire_ts = data.get('pc_cookie_expire_ts', ''),
                                        pc_cookie_expire_ts_label = data.get('pc_cookie_expire_ts_label', ''),
                                        mobile = data.get('mobile', ''),
                                        mobile_cookie_status = data.get('mobile_cookie_status', False),
                                        mobile_cookie_str = data.get('mobile_cookie_str', ''),
                                        mobile_cookie_ts = data.get('mobile_cookie_ts', ''),
                                        mobile_cookie_ts_label = data.get('mobile_cookie_ts_label', ''),
                                        mobile_cookie_expire_ts = data.get('mobile_cookie_expire_ts', ''),
                                        mobile_cookie_expire_ts_label = data.get('mobile_cookie_expire_ts_label', ''),
                                        leading_time = data.get('leading_time', int(global_config.get('config', 'default_order_leading_in_millis'))),
                                        enabled = data.get('enabled', True),
                                        user = user_model
                                    )
            jd_user_model.save()
            return jd_user_model
        finally:
            connection.close()