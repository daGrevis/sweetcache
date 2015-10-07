from unittest import TestCase
from mock import Mock, patch, ANY
from datetime import datetime, timedelta

from freezegun import freeze_time

from . import  Cache, to_key_parts, to_timedelta, EmptyKeyError, NotFoundError, ToTimedeltaError


class ToTimedeltaTests(TestCase):

    def test_none_is_ignored(self):
        self.assertEqual(to_timedelta(None), None)

    def test_timedelta_is_ignored(self):
        self.assertEqual(to_timedelta(timedelta()), timedelta())

    def test_int_to_timedelta(self):
        self.assertEqual(to_timedelta(4 * 60 + 20), timedelta(minutes=4, seconds=20))

    @freeze_time("2015-08-02 16")
    def test_datetime_to_timedelta(self):
        self.assertEqual(to_timedelta(datetime(2015, 8, 2, 16, 20)), timedelta(minutes=20))

    def test_exception_on_invalid(self):
        with self.assertRaises(ToTimedeltaError):
            to_timedelta("a")


class ToKeyPartsTests(TestCase):

    def test_empty(self):
        empty_keys = (
            "",
            ".",
            [],
            ["."],
        )

        for key in empty_keys:
            with self.assertRaises(EmptyKeyError):
                to_key_parts(key)

    def test_single_part(self):
        self.assertEqual(
            to_key_parts("foo"),
            ["foo"],
        )

    def test_many_parts(self):
        self.assertEqual(
            to_key_parts("foo.bar"),
            ["foo", "bar"],
        )

    def test_non_str(self):
        self.assertEqual(
            to_key_parts(42),
            ["42"],
        )

    def test_coll_with_single_part(self):
        self.assertEqual(
            to_key_parts(["foo"]),
            ["foo"],
        )

    def test_coll_with_many_parts(self):
        self.assertEqual(
            to_key_parts(["foo", "bar"]),
            ["foo", "bar"],
        )

    def test_coll_with_non_str(self):
        self.assertEqual(
            to_key_parts(["foo", 42]),
            ["foo", "42"],
        )

    def test_coll_with_separators(self):
        self.assertEqual(
            to_key_parts(["foo", "bar.baz"]),
            ["foo", "bar", "baz"],
        )
        self.assertEqual(
            to_key_parts([".foo.", ".bar.baz."]),
            ["foo", "bar", "baz"],
        )


class CacheTests(TestCase):

    def test_cache_is_called_with_backend_class(self):
        backend_class = Mock()
        cache = Cache(backend_class)

        self.assertEqual(cache.backend_class, backend_class)
        self.assertEqual(cache.backend_kwargs, {})
        backend_class.assert_called_once_with()

    def test_cache_called_with_backend_class_and_backend_kwargs(self):
        backend_class = Mock()
        backend_kwargs = {
            "foo": 42,
            "bar": 69,
        }
        cache = Cache(backend_class, backend_kwargs)

        self.assertEqual(cache.backend_class, backend_class)
        self.assertEqual(cache.backend_kwargs, backend_kwargs)
        backend_class.assert_called_once_with(**backend_kwargs)

    def test_cache_to_str_is_pretty(self):
        backend_class = Mock(__name__="DummyBackend")
        cache = Cache(backend_class)

        self.assertEqual(str(cache), "SweetCache(DummyBackend)")


class CacheSetTests(TestCase):

    def test_set_calls_backend_set(self):
        cache = Cache(Mock())

        key = "foo"
        value = 42
        expires = timedelta(minutes=5)
        cache.set(key, value, expires=expires)

        cache._backend.set.assert_called_once_with([key], value, expires)

    @patch("sweetcache.to_key_parts")
    def test_set_calls_to_key_parts(self, to_key_parts):
        cache = Cache(Mock())

        key = "foo"
        cache.set(key, ANY)

        to_key_parts.assert_called_once_with(key)

    @patch("sweetcache.to_timedelta")
    @patch("sweetcache.to_key_parts")
    def test_set_calls_to_timedelta(self, _, to_timedelta):
        cache = Cache(Mock())

        expires = timedelta(minutes=5)
        cache.set(ANY, ANY, expires=expires)

        to_timedelta.assert_called_once_with(expires)


class CacheGetTests(TestCase):

    def test_get_calls_backend_get(self):
        cache = Cache(Mock())

        key = "foo"
        cache.get(key)

        cache._backend.get.assert_called_once_with([key])

    @patch("sweetcache.to_key_parts")
    def test_get_calls_to_key_parts(self, to_key_parts):
        cache = Cache(Mock())

        key = "foo"
        cache.get(key)

        to_key_parts.assert_called_once_with(key)

    def test_not_found_raises_exception(self):
        backend_class = Mock()
        backend_class.return_value = Mock(get=Mock(side_effect=NotFoundError()))
        cache = Cache(backend_class)

        with self.assertRaises(NotFoundError):
            cache.get("foo")

    def test_not_found_with_default(self):
        backend_class = Mock()
        backend_class.return_value = Mock(get=Mock(side_effect=NotFoundError()))
        cache = Cache(backend_class)

        self.assertEqual(cache.get("foo", None), None)
        self.assertEqual(cache.get("foo", 42), 42)


class CacheItTests(TestCase):

    def test_it_calls_get(self):
        key = "foo"
        value = 42

        cache = Cache(Mock())
        cache.get = Mock(return_value=value)

        fn = cache.it(key)(Mock())
        return_value = fn()

        cache.get.assert_called_once_with(key)
        self.assertEqual(return_value, value)

    def test_it_calls_set(self):
        key = "foo"
        value = 42
        expires = timedelta(minutes=5)

        cache = Cache(Mock())
        cache.get = Mock(side_effect=NotFoundError())
        cache.set = Mock()

        setter = Mock(return_value=value)

        fn = cache.it(key, expires)(setter)
        return_value = fn()

        cache.set.assert_called_once_with(key, value, expires)
        self.assertEqual(return_value, value)
