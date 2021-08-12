from django.db import models
from models.base.base_model import BaseModel
from models.common.login_user_model import User
 
class JDOrder(BaseModel):
    class Meta(BaseModel.Meta):
        db_table = 'tbl_jd_order'
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nick_name = models.CharField(max_length=50)
    order_time = models.CharField(max_length=50)
    order_id = models.CharField(max_length=50)
    sum_price = models.CharField(max_length=20)
    addr_name = models.CharField(max_length=50)
    addr = models.CharField(max_length=500)
    leading_time = models.CharField(max_length=10, blank=True, default='')
    is_reserve = models.CharField(max_length=10, blank=True, default='')
    is_seckill = models.CharField(max_length=10, blank=True, default='')
    stock_count = models.CharField(max_length=100, blank=True, default='')
    target_price = models.FloatField(default=0)
    original_price = models.FloatField(default=0)
    saved_price = models.FloatField(default=0)
    item_info_array = models.TextField()