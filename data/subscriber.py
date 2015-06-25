import json
import redis
import re  # regular expressions
import base64


class Subscriber:
    def __init__(self, subscription='L8'):
        self.redis = redis.Redis()
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(subscription)

    def work(self, callable, decode=True):
        for item in self.pubsub.listen():
            record = json.loads(item['data'])
            if decode:
                regex = re.compile('^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{4}|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)$')
                if regex.match(record['context']):
                    record['context'] = base64.b64decode(record['context'])
            callable(record)

    def work_raw(self, callable):
        for item in self.pubsub.listen():
            callable(item)
