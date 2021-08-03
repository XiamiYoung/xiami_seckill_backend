
from django.core.cache import cache
from django_redis import get_redis_connection

from config.constants import (
    DEFAULT_CACHE_TTL
)

class CacheDao(object):

    def __init__(self):
        self.redis_client = get_redis_connection("default")

    def put(self, key, value, timeout=DEFAULT_CACHE_TTL):
        cache.set(key, value, timeout=timeout)

    def get(self,key):
        return cache.get(key)

    def scan_by_key(self,keys):
        return cache.keys(keys)

    def delete(self,keys):
        return cache.delete_pattern(keys)

    def delete_stream(self, stream):
        if self.redis_client.exists(stream):
            self.redis_client.delete(stream)

    def push_to_stream(self, stream, value):
        self.redis_client.xadd(stream, fields=value)

    def read_from_stream(self, stream, id='0-0'):
        return self.redis_client.xread({stream: id})

    def read_from_stream_group(self, stream, group, consumer, id='>'):
        message_list = []
        messages = self.redis_client.xreadgroup(group, consumer, {stream: id})
        if messages:
            for id, fields in messages[0][1]:
                for key in fields.keys():
                    value = fields[key].decode('utf-8')
                    ret_json = {key.decode('utf-8'):value}
                message_list.append(ret_json)
        return message_list

    def create_stream_group(self, stream, group, id=0):
        self.redis_client.xgroup_destroy(stream, group)
        self.redis_client.xgroup_create(stream, group, id)