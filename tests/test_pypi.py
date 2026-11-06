"""Tests for PypiRepository against a local HTTP server."""

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src.errors import PackageNotFoundError, RepositoryError
from src.repository import PypiRepository

PACKAGES = {
    "/pypi/demo/json": {"info": {"requires_dist": [
        "idna (<4,>=2.5)",
        "Charset_Normalizer<4",
        "idna>=2",
        "PySocks ; extra == 'socks'",
    ]}},
    "/pypi/lonely/json": {"info": {"requires_dist": None}},
    "/pypi/bad/json": {"info": {"requires_dist": [">=1"]}},
    "/pypi/list/json": ["not", "a", "dict"],
}


class Handler(BaseHTTPRequestHandler):
    """Serve PACKAGES like the PyPI JSON API."""

    def do_GET(self):
        """Answer with JSON, 404 or a server error."""
        if self.path == "/pypi/broken/json":
            self.reply(200, b"{not json")
        elif self.path == "/pypi/boom/json":
            self.reply(500, b"error")
        elif self.path in PACKAGES:
            self.reply(200, json.dumps(PACKAGES[self.path]).encode())
        else:
            self.reply(404, b"{}")

    def reply(self, code, body):
        """Send a response."""
        self.send_response(code)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        """Keep test output clean."""


class PypiTests(unittest.TestCase):
    """Stage 2: reading direct dependencies."""

    @classmethod
    def setUpClass(cls):
        """Start a local server."""
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=cls.server.serve_forever)
        thread.daemon = True
        thread.start()
        port = cls.server.server_address[1]
        cls.repo = PypiRepository(f"http://127.0.0.1:{port}/pypi/")

    @classmethod
    def tearDownClass(cls):
        """Stop the server."""
        cls.server.shutdown()
        cls.server.server_close()

    def test_direct_dependencies(self):
        """Names are parsed, normalized, deduplicated; extras skipped."""
        self.assertEqual(
            self.repo.dependencies("demo"), ["idna", "charset-normalizer"]
        )

    def test_no_dependencies(self):
        """A null requires_dist means no dependencies."""
        self.assertEqual(self.repo.dependencies("lonely"), [])

    def test_not_found(self):
        """An unknown package gives PackageNotFoundError."""
        with self.assertRaises(PackageNotFoundError):
            self.repo.dependencies("missing")

    def test_server_error(self):
        """An HTTP error gives RepositoryError."""
        with self.assertRaises(RepositoryError):
            self.repo.dependencies("boom")

    def test_invalid_json(self):
        """A broken response gives RepositoryError."""
        with self.assertRaises(RepositoryError):
            self.repo.dependencies("broken")

    def test_unexpected_format(self):
        """A JSON list instead of an object gives RepositoryError."""
        with self.assertRaises(RepositoryError):
            self.repo.dependencies("list")

    def test_bad_requirement(self):
        """An invalid requirement string gives RepositoryError."""
        with self.assertRaises(RepositoryError):
            self.repo.dependencies("bad")

    def test_unreachable(self):
        """A closed port gives RepositoryError."""
        repo = PypiRepository("http://127.0.0.1:9/pypi")
        with self.assertRaises(RepositoryError):
            repo.dependencies("demo")


if __name__ == "__main__":
    unittest.main()
