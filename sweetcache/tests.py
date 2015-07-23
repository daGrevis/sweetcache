from unittest import TestCase
from mock import Mock, patch

from . import Cache, key_join, EmptyKeyError, NotFoundError


class MockCacheTestCase(TestCase):

    def setUp(self):
        backend_class = Mock()
        self.cache = Cache(backend_class)


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


class SettingTests(TestCase):

    def test_set_calls_backend_set(self):
        cache = Cache(Mock())

        key = "foo"
        value = 42
        cache.set(key, value)

        cache._backend.set.assert_called_once_with([key], value, None)

    @patch("sweetcache._unwrap_keys")
    def test_set_calls_unwrap_keys(self, _unwrap_keys):
        separator = "."
        cache = Cache(Mock(), separator=separator)

        key = "foo"
        value = 42
        cache.set(key, value)

        _unwrap_keys.assert_called_once_with(key, separator)


class JoiningKeyTests(TestCase):

    def test_with_empty_string(self):
        with self.assertRaises(EmptyKeyError):
            key_join("")

    def test_with_empty_iterable(self):
        with self.assertRaises(EmptyKeyError):
            key_join([])

    def test_semantically_empty(self):
        with self.assertRaises(EmptyKeyError):
            key_join(".")
        with self.assertRaises(EmptyKeyError):
            key_join([".", ".."])

    def test_with_flat_key(self):
        self.assertEqual(key_join(["foo"]), "foo")

    def test_with_deep_key(self):
        self.assertEqual(key_join(["foo.bar"]), "foo.bar")

    def test_with_multiple_keys(self):
        self.assertEqual(key_join(["foo", "bar"]), "foo.bar")

    def test_flat_and_deep_keys_together(self):
        self.assertEqual(key_join(["foo", "bar.baz"]), "foo.bar.baz")

    def test_extra_separators_are_ignored(self):
        self.assertEqual(key_join(["..foo...", "..bar...baz.."]), "foo.bar.baz")
        # Real use-case could look like:
        #     cache.set(["users.v2", user.id], user)

    def test_with_different_separator(self):
        self.assertEqual(
            key_join(["foo-bar", "-baz"], separator="-"),
            "foo-bar-baz",
        )


class GettingTests(TestCase):

    def test_get_calls_backend_get(self):
        cache = Cache(Mock())

        key = "foo"
        cache.get(key)

        cache._backend.get.assert_called_once_with([key])

    @patch("sweetcache._unwrap_keys")
    def test_get_calls_unwrap_keys(self, _unwrap_keys):
        separator = "."
        cache = Cache(Mock(), separator=separator)

        key = "foo"
        cache.get(key)

        _unwrap_keys.assert_called_once_with(key, separator)

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
