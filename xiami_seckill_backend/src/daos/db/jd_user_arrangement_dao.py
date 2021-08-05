from models.jd_user_arrangement import JDUserArrangement
from django.db import connection
from daos.db.user_dao import UserDao

from utils.util import (
    json_to_str
)

class JDUserArrangementDao(object):
    def save_or_update_jd_user_arrangement(self, data, user_model):
        try:
            user_qs = UserDao().find_by_username(user_model.username)
            user_model = user_qs.first()
            if hasattr(user_model, 'jduserarrangement') and user_model.jduserarrangement is not None:
                jd_user_arrangement_model = user_qs.first().jduserarrangement
                jd_user_arrangement_model.seckill_arrangement = json_to_str(data.get('seckill_arrangement', {}))
                jd_user_arrangement_model.sku_arrangement = json_to_str(data.get('sku_arrangement', {}))
            else:
                jd_user_arrangement_model = JDUserArrangement(
                                        seckill_arrangement = json_to_str(data.get('seckill_arrangement', {})),
                                        sku_arrangement = json_to_str(data.get('sku_arrangement', {})),
                                        user = user_model
                                    )
            jd_user_arrangement_model.save()
            return jd_user_arrangement_model
        finally:
            connection.close()

    def find_jd_user_arrangement_by_username(self, user_name):
        try:
            user_qs = UserDao().find_by_username(user_name)
            user_count = user_qs.count()
            if user_count != 0:
                user_model = user_qs.first()
                if hasattr(user_model, 'jduserarrangement') and user_model.jduserarrangement is not None:
                    return user_model.jduserarrangement
                else:
                    return None
            else:
                return None
        finally:
            connection.close()
