from django.db import models
from models.base.base_model import BaseModel
 
class User(BaseModel):
    class Meta(BaseModel.Meta):
        db_table = 'tbl_user'
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=20)
    level = models.CharField(max_length=1, blank=False, default='1')
    balance = models.CharField(max_length=6, blank=False, default='100')