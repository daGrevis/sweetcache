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


def to_key_parts(key_or_key_parts):
    if type(key_or_key_parts) is str:
        key_parts = [key_or_key_parts]
    else:
        key_parts = key_or_key_parts

    keys = []
    for key_part in key_parts:
        keys.extend([x.strip(SEPARATOR) for x in key_part.split(SEPARATOR) if x])

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


def join_key(key_or_key_parts):
    return SEPARATOR.join(
        to_key_parts(key_or_key_parts),
    )


class Cache(object):

    def __init__(self, backend_class, backend_kwargs=None):
        self.backend_class = backend_class
        self.backend_kwargs = backend_kwargs or {}

        self._backend = self.backend_class(**self.backend_kwargs)

    def set(self, key_or_key_parts, value, expires=None):
        self._backend.set(
            to_key_parts(key_or_key_parts),
            value,
            to_timedelta(expires),
        )

    def get(self, *args):
        try:
            key_or_key_parts, default = args
            has_default = True
        except ValueError:
            key_or_key_parts = args[0]
            has_default = False

        key_parts = to_key_parts(key_or_key_parts)

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
