from models.jd_order_model import JDOrder

from utils.util import (
    json_to_str,
)

class JDOrderDao(object):
    def save_jd_order(self, data, user_model):
        jd_order_model = JDOrder(
                                order_time = data.get('order_time', ''),
                                order_id = str(data.get('order_id', '')),
                                sum_price = data.get('sum_price', ''),
                                addr_name = data.get('addr_name', ''),
                                addr = data.get('addr', ''),
                                item_info_array = json_to_str(data.get('item_info_array', {})),
                                nick_name = data.get('nick_name', ''), 
                                user = user_model
                            )
        jd_order_model.save()
        return jd_order_model

