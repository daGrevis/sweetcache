# Sweetcache

Lightweight, framework agnostic caching library with sweet API

[![Project Status: Wip - Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](http://www.repostatus.org/badges/0.1.0/wip.svg)](http://www.repostatus.org/#wip)

**NB! API is expected to change!**

## Usage

```python
from datetime import datetime, timedelta

import sweetcache
import sweetcache_redis


cache = sweetcache.Cache(sweetcache_redis.RedisBackend)


cache.set("foo", 42)
assert cache.get("foo") == 42


user = {
    "id": 1,
    "username": "daGrevis",
}
cache.set(["users.v1", user["id"]], user)


cache.set("foo", 42, expires=timedelta(minutes=5))
cache.set("foo", 42, expires=datetime(2015, 9, 28))
cache.set("foo", 42, expires=60 * 5)


try:
    foo = cache.get("foo")
except sweetcache.NotFoundError:
    foo = None

foo = cache.get("foo", None)


@cache.it("charts.v2", expires=timedelta(hours=2))
def get_charts():
    charts = calculate_charts()
    return charts
```

## Running Tests

~~~
nosetests -s sweetcache
~~~

### With Coverage

~~~
nosetests -s sweetcache --with-coverage --cover-html --cover-package sweetcache
~~~
