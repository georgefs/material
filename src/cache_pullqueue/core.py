import threading
from datetime import datetime
from django.core.cache import cache
import time

class CacheLock:
    def __init__(self, key, default=[], timeout=5):
        t = datetime.now().strftime('%s')
        thread_id = threading.current_thread().ident
        sign = "{}_{}".format(t, thread_id)
        self.sign = sign
        self.key = key
        self.lock_name = "__{}__lock".format(key)
        self.timeout = timeout
        self.default = default

    def __enter__(self):
        while True:
            if not cache.get(self.lock_name, None):
                if cache.get_or_set(self.lock_name, self.sign, self.timeout) == self.sign:
                    return cache.get(self.key) or self.default
            time.sleep(0.01)

    def __exit__(self, type, value, traceback):
        cache.delete(self.lock_name)


class PullQueue:
    @staticmethod
    def push(topic_key, value, unique=False):
        with CacheLock(topic_key) as v:
            if not(unique and value in v):
                v.append(value)
            cache.set(topic_key, v)

    @staticmethod
    def push_multi(topic_key, values, unique=False):
        with CacheLock(topic_key) as v:
            for value in values:
                if not(unique and values in v):
                    v.append(value)
            cache.set(topic_key, v)

    @staticmethod
    def pull(topic_key):
        with CacheLock(topic_key) as v:
            s, v = v[:1], v[1:]
            cache.set(topic_key, v)
            return s[0]

    @staticmethod
    def pull_multi(topic_key, length=-1):
        with CacheLock(topic_key) as v:
            if length != -1:
                s, v = v[:length], v[length:]
            else:
                s, v = v, []
            cache.set(topic_key, v)
            return s

    @staticmethod
    def get_len(topic_key):
        return len(cache.get(topic_key, []))

    @staticmethod
    def read(topic_key, length=-1):
        if length != -1:
            return cache.get(topic_key, [])
        else:
            return cache.get(topic_key, [])[:length]
