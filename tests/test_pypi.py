"""Tests for PypiRepository with a fake network (no internet needed)."""

import io
import json
import unittest
import urllib.error
from unittest import mock

from src.errors import PackageNotFoundError, RepositoryError
from src.repository import PypiRepository

PACKAGES = {
    "demo": {"info": {"requires_dist": [
        "idna (<4,>=2.5)",
        "Charset_Normalizer<4",
        "idna>=2",
        "PySocks ; extra == 'socks'",
    ]}},
    "lonely": {"info": {"requires_dist": None}},
    "bad": {"info": {"requires_dist": [">=1"]}},
    "list": ["not", "a", "dict"],
}
HTTP_SERVER_ERROR = 500
HTTP_NOT_FOUND = 404


def fake_urlopen(request, timeout=None):
    """Imitate urlopen for the PyPI JSON API."""
    url = request.full_url
    name = url.rstrip("/").split("/")[-2]
    if name == "boom":
        raise urllib.error.HTTPError(
            url, HTTP_SERVER_ERROR, "error", None, None
        )
    if name == "down":
        raise urllib.error.URLError("connection refused")
    if name == "broken":
        return io.BytesIO(b"{not json")
    if name not in PACKAGES:
        raise urllib.error.HTTPError(
            url, HTTP_NOT_FOUND, "not found", None, None
        )
    return io.BytesIO(json.dumps(PACKAGES[name]).encode("utf-8"))


def make_repo(test):
    """Replace the network by the fake one and return a repository."""
    patcher = mock.patch(
        "src.repository.urllib.request.urlopen", side_effect=fake_urlopen
    )
    patcher.start()
    test.addCleanup(patcher.stop)
    return PypiRepository("https://example.test/pypi/")


class PypiTests(unittest.TestCase):
    """Stage 2: reading direct dependencies."""

    def test_direct_dependencies(self):
        """Names are parsed, normalized, deduplicated; extras skipped."""
        repo = make_repo(self)
        self.assertEqual(
            repo.dependencies("demo"), ["idna", "charset-normalizer"]
        )

    def test_no_dependencies(self):
        """A null requires_dist means no dependencies."""
        self.assertEqual(make_repo(self).dependencies("lonely"), [])

    def test_not_found(self):
        """An unknown package gives PackageNotFoundError."""
        with self.assertRaises(PackageNotFoundError):
            make_repo(self).dependencies("missing")

    def test_server_error(self):
        """An HTTP error gives RepositoryError."""
        with self.assertRaises(RepositoryError):
            make_repo(self).dependencies("boom")

    def test_invalid_json(self):
        """A broken response gives RepositoryError."""
        with self.assertRaises(RepositoryError):
            make_repo(self).dependencies("broken")

    def test_unexpected_format(self):
        """A JSON list instead of an object gives RepositoryError."""
        with self.assertRaises(RepositoryError):
            make_repo(self).dependencies("list")

    def test_bad_requirement(self):
        """An invalid requirement string gives RepositoryError."""
        with self.assertRaises(RepositoryError):
            make_repo(self).dependencies("bad")

    def test_unreachable(self):
        """A network failure gives RepositoryError."""
        with self.assertRaises(RepositoryError):
            make_repo(self).dependencies("down")

    def test_package_url(self):
        """The URL is built from the normalized name."""
        repo = PypiRepository("https://example.test/pypi/")
        self.assertEqual(
            repo.package_url("Charset_Normalizer"),
            "https://example.test/pypi/charset-normalizer/json",
        )


if __name__ == "__main__":
    unittest.main()
