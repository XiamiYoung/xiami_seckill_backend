from django.db import models
from models.base_model import BaseModel
from models.user_model import User
 
class JDUser(BaseModel):
    class Meta(BaseModel.Meta):
        db_table = 'tbl_jd_user'
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nick_name = models.CharField(max_length=20)
    recipient_name = models.CharField(max_length=20, blank=True, default='')
    full_addr = models.CharField(max_length=500, blank=True, default='')
    mobile = models.CharField(max_length=20, blank=True, default='')
    pc_cookie_status = models.BooleanField(default=False)
    pc_cookie_str = models.TextField(blank=True, default='')
    pc_cookie_ts = models.CharField(max_length=100, blank=True, default='')
    pc_cookie_ts_label = models.CharField(max_length=100, blank=True, default='')
    pc_cookie_expire_ts = models.CharField(max_length=100, blank=True, default='')
    pc_cookie_expire_ts_label = models.CharField(max_length=100, blank=True, default='')
    mobile_cookie_status = models.BooleanField(default=False)
    mobile_cookie_str = models.TextField(blank=True, default='')
    mobile_cookie_ts = models.CharField(max_length=100, blank=True, default='')
    mobile_cookie_ts_label = models.CharField(max_length=100, blank=True, default='')
    mobile_cookie_expire_ts = models.CharField(max_length=100, blank=True, default='')
    mobile_cookie_expire_ts_label = models.CharField(max_length=100, blank=True, default='')