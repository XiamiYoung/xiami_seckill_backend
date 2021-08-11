from models.jd.jd_order_model import JDOrder
from django.db import connection

from utils.util import (
    json_to_str,
)

class JDOrderDao(object):
    def save_jd_order(self, data, user_model):
        try:
            jd_order_model = JDOrder(
                                    order_time = data.get('order_time', ''),
                                    order_id = str(data.get('order_id', '')),
                                    sum_price = data.get('sum_price', ''),
                                    addr_name = data.get('addr_name', ''),
                                    addr = data.get('addr', ''),
                                    item_info_array = json_to_str(data.get('item_info_array', {})),
                                    nick_name = data.get('nick_name', ''), 
                                    is_reserve = data.get('is_reserve', ''), 
                                    is_seckill = data.get('is_seckill', ''), 
                                    leading_time = data.get('leading_time', ''), 
                                    stock_count = data.get('stock_count', ''), 
                                    current_price = data.get('current_price', 0), 
                                    original_price = data.get('original_price', 0), 
                                    saved_price = data.get('saved_price', 0), 
                                    user = user_model
                                )
            jd_order_model.save()
            connection.close()
            return jd_order_model
        finally:
            connection.close()