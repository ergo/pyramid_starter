import copy
import hashlib
import inspect

from dogpile.cache import make_region, compat

regions = None


def key_mangler(key):
    return "testscaffold:dogpile:{}".format(key)


def hashgen(namespace, fn, to_str=compat.string_type):
    if namespace is None:
        namespace = '%s:%s' % (fn.__module__, fn.__name__)
    else:
        namespace = '%s:%s|%s' % (fn.__module__, fn.__name__, namespace)

    args = inspect.getargspec(fn)
    has_self = args[0] and args[0][0] in ('self', 'cls')

    def generate_key(*args, **kw):
        if kw:
            raise ValueError(
                "dogpile.cache's default key creation "
                "function does not accept keyword arguments.")
        if has_self:
            args = args[1:]

        return namespace + "|" + hashlib.sha1(
            " ".join(map(to_str, args)).encode('utf8')).hexdigest()

    return generate_key


class CacheRegions(object):
    def __init__(self, settings):
        dogpile_config = {'url': settings['redis.dogpile.url'],
                          "redis_expiration_time": 86400,
                          "redis_distributed_lock": True}

        config_redis = {"arguments": dogpile_config}

        self.redis_sec_1 = make_region(
            function_key_generator=hashgen,
            key_mangler=key_mangler).configure(
            "dogpile.cache.redis",
            expiration_time=1,
            **copy.deepcopy(config_redis))

        self.redis_sec_5 = make_region(
            function_key_generator=hashgen,
            key_mangler=key_mangler).configure(
            "dogpile.cache.redis",
            expiration_time=5,
            **copy.deepcopy(config_redis))

        self.redis_min_1 = make_region(
            function_key_generator=hashgen,
            key_mangler=key_mangler).configure(
            "dogpile.cache.redis",
            expiration_time=60,
            **copy.deepcopy(config_redis))
        self.redis_min_5 = make_region(
            function_key_generator=hashgen,
            key_mangler=key_mangler).configure(
            "dogpile.cache.redis",
            expiration_time=300,
            **copy.deepcopy(config_redis))

        self.redis_min_10 = make_region(
            function_key_generator=hashgen,
            key_mangler=key_mangler).configure(
            "dogpile.cache.redis",
            expiration_time=60,
            **copy.deepcopy(config_redis))

        self.redis_min_60 = make_region(
            function_key_generator=hashgen,
            key_mangler=key_mangler).configure(
            "dogpile.cache.redis",
            expiration_time=3600,
            **copy.deepcopy(config_redis))
