# Sweetcache

Lightweight, framework agnostic caching library with sweet API

**Work in progress. API is expected to change.**

## Usage

~~~
from datetime import timedelta

import sweetcache


cache = sweetcache.Cache(sweetcache.RedisBackend)


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


@cache.it("charts.v2", expires=timedelta(hours=2))
def get_charts():
    charts = calculate_charts()
    return charts
~~~

## Running Tests

~~~
nosetests -s sweetcache
~~~

### With Coverage

~~~
nosetests -s sweetcache --with-coverage --cover-html --cover-package sweetcache
~~~
