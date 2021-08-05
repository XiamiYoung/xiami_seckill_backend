from django.db import models
from models.base_model import BaseModel
from models.user_model import User
 
class JDUserArrangement(BaseModel):
    class Meta(BaseModel.Meta):
        db_table = 'tbl_jd_user_arrangement'
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    seckill_arrangement = models.TextField()
    sku_arrangement = models.TextField()