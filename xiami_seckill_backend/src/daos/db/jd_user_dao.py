from models.jd_user_model import JDUser
from django.db import connection
from config.config import global_config

class JDUserDao(object):
    
    def find_by_nick_name(self, nick_name):
        try:
            jd_user_data_qs = JDUser.objects.filter(nick_name=nick_name)
            return jd_user_data_qs
        finally:
            connection.close()

    def delete_by_id(self, id):
        jd_user = JDUser.objects.get(id = id)
        jd_user.delete()

    def update_leading_time(self, nick_name, leading_time):
        try:
            jd_user_qs = JDUser.objects.filter(nick_name=nick_name)
            jd_user_model = jd_user_qs.first()
            jd_user_model.leading_time = int(leading_time)
            jd_user_model.save()
        finally:
            connection.close()

    def save_or_update_jd_enduser(self, data, user_model):
        try:
            exists = False
            jd_user_model = None
            jd_user_qs = JDUser.objects.filter(nick_name=data['nick_name'])
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
                                        user = user_model
                                    )
            jd_user_model.save()
            return jd_user_model
        finally:
            connection.close()