from redis import Redis
import pickle


SEPARATOR = "."


class SweetcacheException(Exception):

    pass


class EmptyKeyError(SweetcacheException):

    pass


class NotFoundError(SweetcacheException):
    
    pass


class RedisBackend(object):

    def __init__(self, **kwargs):
        self.redis = Redis(**kwargs)

    @staticmethod
    def _make_key(key):
        return ".".join(key)

    def set(self, key, value, expires):
        name = self._make_key(key)

        value = pickle.dumps(value)

        if expires is None:
            assert self.redis.set(
                name,
                value,
            )
        else:
            time = int(expires.total_seconds())

            assert self.redis.setex(
                name,
                value,
                time,
            )

    def get(self, key):
        value = self.redis.get(
            self._make_key(key),
        )

        if value is None:
            raise NotFoundError()

        value = pickle.loads(value)

        return value


def _unwrap_keys(key_or_key_parts, separator=None):
    assert separator is not None

    if isinstance(key_or_key_parts, str):
        key_parts = [key_or_key_parts]
    else:
        key_parts = key_or_key_parts

    keys = []
    for key_part in key_parts:
        keys.extend([x.strip(separator) for x in key_part.split(separator) if x])

    if not keys:
        raise EmptyKeyError()

    return keys


def key_join(key_or_key_parts, separator=SEPARATOR):
    return separator.join(
        _unwrap_keys(key_or_key_parts, separator),
    )


class Cache(object):

    def __init__(self, backend_class, backend_kwargs=None, separator=SEPARATOR):
        self.backend_class = backend_class
        self.backend_kwargs = backend_kwargs or {}
        self.separator = separator

        self._backend = self.backend_class(**self.backend_kwargs)

    def set(self, key_or_key_parts, value, expires=None):
        self._backend.set(
            _unwrap_keys(key_or_key_parts, self.separator),
            value,
            expires,
        )

    def get(self, *args):
        try:
            key_or_key_parts, default = args
            has_default = True
        except ValueError:
            key_or_key_parts = args[0]
            has_default = False

        key_parts = _unwrap_keys(key_or_key_parts, self.separator)

        try:
            return self._backend.get(key_parts)
        except NotFoundError:
            if has_default:
                return default

            raise
