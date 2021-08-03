from django.db import models
from models.base_model import BaseModel
 
class User(BaseModel):
    class Meta(BaseModel.Meta):
        db_table = 'tbl_user'
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=20)
    payment_pwd = models.CharField(max_length=20, blank=True, default='')
    mobile = models.CharField(max_length=11, blank=True, default='')
    level = models.CharField(max_length=1, blank=False, default='1')
    balance = models.CharField(max_length=6, blank=False, default='100')