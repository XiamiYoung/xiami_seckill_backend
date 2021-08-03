from django.db import models
import uuid
from itertools import chain
 
class BaseModel(models.Model):
    class Meta:
        app_label = 'xiami_seckill_backend'
        abstract = True
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    created_ts = models.DateTimeField(auto_now_add=True)
    updated_ts = models.DateTimeField(auto_now=True)

    def to_dict(instance, exclude=None):
        opts = instance._meta
        data = {}
        for f in chain(opts.concrete_fields, opts.private_fields):
            if exclude and f.name in exclude:
                continue
            data[f.name] = f.value_from_object(instance)
        for f in opts.many_to_many:
            data[f.name] = [i.id for i in f.value_from_object(instance)]
        return data