from daos.db.jd_user_dao import JDUserDao
from daos.db.jd_user_arrangement_dao import JDUserArrangementDao
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


    def find_jd_user_by_nick_name(self, nick_name, is_return_model=False, is_mask_jd_pwd=True):
        jd_user_qs = self.jd_user_dao.find_by_nick_name(nick_name)
        user_count = jd_user_qs.count()
        if user_count == 0:
            return {}
        if user_count > 1:
            exception = RestfulException(error_dict['USER']['USER_DUPLICATED'])
            raise exception
        if is_return_model:
            return jd_user_qs.first()
        else:
            jd_user_data = jd_user_qs.first().to_dict()
            if 'jd_pwd' in jd_user_data and jd_user_data['jd_pwd']:
                jd_user_data['jd_pwd'] = decrypt_token(jd_user_data['jd_pwd'], db_prop_secret)['jd_pwd']
                if is_mask_jd_pwd and jd_user_data['jd_pwd']:
                    jd_user_data['jd_pwd'] = '******'
            if 'push_token' in jd_user_data and jd_user_data['push_token']:
                jd_user_data['push_token'] = decrypt_token(jd_user_data['push_token'], db_prop_secret)['push_token']
            return jd_user_data

    def find_jd_user_by_username_and_nick_name(self, user_name, nick_name):
        login_user_model = self.login_user_service.find_user_by_username(user_name, is_return_model=True)
        jd_user_list = list(login_user_model.jduser_set.all().values())
        for jd_user in jd_user_list:
            if jd_user['nick_name'] == nick_name:
                return jd_user
        return None
                
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
                    if json_seckill_arrangement[nick_name]:
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

    def update_jd_user_leading_time(self, nick_name, user_options):
        self.jd_user_dao.update_jd_user_leading_time(nick_name, user_options)

    def update_jd_user_pwd(self, nick_name, user_options):
        self.jd_user_dao.update_jd_user_pwd(nick_name, user_options)

    def update_jd_user_push_token(self, nick_name, user_options):
        self.jd_user_dao.update_jd_user_push_token(nick_name, user_options)

    def update_jd_user_push_email(self, nick_name, user_options):
        self.jd_user_dao.update_jd_user_push_email(nick_name, user_options)