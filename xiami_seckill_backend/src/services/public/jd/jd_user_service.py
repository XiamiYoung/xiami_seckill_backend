from daos.db.jd.jd_user_dao import JDUserDao
from daos.db.jd.jd_user_arrangement_dao import JDUserArrangementDao
from services.public.common.login_user_service import LoginUserService
from config.error_dict import error_dict
from exception.restful_exception import RestfulException
from config.config import global_config

from utils.util import (
    str_to_json,
)

from utils.token_util import (
    decrypt_token
)

db_prop_secret = global_config.get('config', 'db_prop_secret')

class JDUserService(object):
    def __init__(self):
        self.jd_user_dao = JDUserDao()
        self.jd_user_arrangement_dao = JDUserArrangementDao()
        self.login_user_service = LoginUserService()

    def find_jd_user_by_username_and_nick_name(self, user_name, nick_name, is_mask_jd_pwd=True):
        login_user_model = self.login_user_service.find_user_by_username(user_name, is_return_model=True)
        jd_user_list = list(login_user_model.jduser_set.all().values())
        for jd_user in jd_user_list:
            if jd_user['nick_name'] == nick_name:
                if 'jd_pwd' in jd_user and jd_user['jd_pwd']:
                    jd_user['jd_pwd'] = decrypt_token(jd_user['jd_pwd'], db_prop_secret)['jd_pwd']
                    if is_mask_jd_pwd and jd_user['jd_pwd']:
                        jd_user['jd_pwd'] = '******'
                if 'push_token' in jd_user and jd_user['push_token']:
                    jd_user['push_token'] = decrypt_token(jd_user['push_token'], db_prop_secret)['push_token']
                return jd_user
        return {}
                
    def save_or_update_jd_user(self, user_name, jd_user_data, is_return_model=False):
        user_model = self.login_user_service.find_user_by_username(user_name, is_return_model=True)
        jd_user_model = self.jd_user_dao.save_or_update_jd_enduser(jd_user_data, user_model)
        if is_return_model:
            return jd_user_model
        else:
            return jd_user_model.to_dict(exclude=['pc_cookie_str','mobile_cookie_str'])

    def delete_jd_user_by_nick_name(self, user_name, nick_name):
        login_user_model = self.login_user_service.find_user_by_username(user_name, is_return_model=True)
        jd_user_list = list(login_user_model.jduser_set.all().values())
        for jd_user in jd_user_list:
            if jd_user['nick_name'] == nick_name:
                # delete user arrangement
                jd_user_arrangement_model = self.find_jd_user_arrangement_by_username(user_name)
                if jd_user_arrangement_model and jd_user_arrangement_model['seckill_arrangement']:
                    json_seckill_arrangement = str_to_json(jd_user_arrangement_model['seckill_arrangement'])
                    if nick_name in json_seckill_arrangement:
                        del json_seckill_arrangement[nick_name]
                        self.save_or_update_jd_user_arrangement(user_name, json_seckill_arrangement)
                self.jd_user_dao.delete_by_id(jd_user['id'])

    def find_jd_user_arrangement_by_username(self, user_name, is_return_model=False):
        jd_user_arrangement_model = self.jd_user_arrangement_dao.find_jd_user_arrangement_by_username(user_name)
        if jd_user_arrangement_model:
            if is_return_model:
                return jd_user_arrangement_model
            else:
                return jd_user_arrangement_model.to_dict()
        else:
            return {}

    def save_or_update_jd_user_arrangement(self, user_name, jd_user_arrangement_data, is_return_model=False):
        user_model = self.login_user_service.find_user_by_username(user_name, is_return_model=True)
        jd_user_arrangement_model = self.jd_user_arrangement_dao.save_or_update_jd_user_arrangement(jd_user_arrangement_data, user_model)
        if is_return_model:
            return jd_user_arrangement_model
        else:
            return jd_user_arrangement_model.to_dict()

    def update_jd_user_leading_time(self, user_name, nick_name, user_options):
        user_model = self.login_user_service.find_user_by_username(user_name, is_return_model=True)
        self.jd_user_dao.update_jd_user_leading_time(user_model, nick_name, user_options)

    def update_jd_user_pwd(self, user_name, nick_name, user_options):
        user_model = self.login_user_service.find_user_by_username(user_name, is_return_model=True)
        self.jd_user_dao.update_jd_user_pwd(user_model, nick_name, user_options)

    def update_jd_user_push_token(self, user_name, nick_name, user_options):
        user_model = self.login_user_service.find_user_by_username(user_name, is_return_model=True)
        self.jd_user_dao.update_jd_user_push_token(user_model, nick_name, user_options)

    def update_jd_user_push_email(self, user_name, nick_name, user_options):
        user_model = self.login_user_service.find_user_by_username(user_name, is_return_model=True)
        self.jd_user_dao.update_jd_user_push_email(user_model, nick_name, user_options)

    def update_jd_user_enabled(self, user_name, nick_name, enabled):
        user_model = self.login_user_service.find_user_by_username(user_name, is_return_model=True)
        self.jd_user_dao.update_jd_user_enabled(user_model, nick_name, enabled)

    def update_jd_user_address(self, user_name, nick_name, recipient_name, full_addr):
        user_model = self.login_user_service.find_user_by_username(user_name, is_return_model=True)
        self.jd_user_dao.update_jd_user_address(user_model, nick_name, recipient_name, full_addr)

    def update_jd_user_mobile(self, user_name, nick_name, mobile):
        user_model = self.login_user_service.find_user_by_username(user_name, is_return_model=True)
        self.jd_user_dao.update_jd_user_mobile(user_model, nick_name, mobile)
        