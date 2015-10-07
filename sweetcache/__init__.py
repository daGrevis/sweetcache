import functools
from datetime import datetime, timedelta


SEPARATOR = "."


class SweetcacheException(Exception):

    pass


class EmptyKeyError(SweetcacheException):

    pass


class NotFoundError(SweetcacheException):
    
    pass


class ToTimedeltaError(SweetcacheException):

    pass


def to_key_parts(cache_key):
    """
    Normalizes so called **cache key** to **key parts**:

        key_parts = ["foo", "bar"]

    Cache keys can be in many different formats:

        cache_keys = (
            "foo",
            "foo.bar",
            ["foo"],
            ["foo", "bar"],
            ["foo.bar", "baz"],
        )
    """

    if type(cache_key) in (list, tuple):
        key_parts = cache_key
    else:
        key_parts = [cache_key]

    keys = []
    for key_part in key_parts:
        keys.extend([x.strip(SEPARATOR) for x in str(key_part).split(SEPARATOR) if x])

    if not keys:
        raise EmptyKeyError()

    return keys


def to_timedelta(x):
    if x is None:
        return x

    x_type = type(x)

    if x_type is timedelta:
        return x

    if x_type is int:
        return timedelta(seconds=x)

    if x_type is datetime:
        return x - datetime.now()

    raise ToTimedeltaError()


class BaseBackend(object):

    def is_available(self):
        raise NotImplementedError()

    def set(self, key, value, expires):
        raise NotImplementedError()

    def get(self, key):
        raise NotImplementedError()


class DummyBackend(BaseBackend):

    def is_available(self):
        return True

    def set(self, key, value, expires):
        pass

    def get(self, key):
        pass


class Cache(object):

    def __init__(self, backend_class, backend_kwargs=None):
        self.backend_class = backend_class
        self.backend_kwargs = backend_kwargs or {}

        self._backend = self.backend_class(**self.backend_kwargs)

    def __str__(self):
        return "SweetCache({})".format(self.backend_class.__name__)

    def is_available(self):
        return self._backend.is_available()

    def set(self, cache_key, value, expires=None):
        self._backend.set(
            to_key_parts(cache_key),
            value,
            to_timedelta(expires),
        )

    def get(self, *args):
        try:
            cache_key, default = args
            has_default = True
        except ValueError:
            cache_key = args[0]
            has_default = False

        key_parts = to_key_parts(cache_key)

        try:
            return self._backend.get(key_parts)
        except NotFoundError:
            if has_default:
                return default

            raise

    def it(self, key, expires=None):
        def deco(fn):
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                try:
                    return self.get(key)
                except NotFoundError:
                    pass

                value = fn(*args, **kwargs)
                self.set(key, value, expires)

                return value

            return wrapper

        return deco
