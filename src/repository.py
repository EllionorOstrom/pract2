"""Access to package repositories."""

import json
import re
import urllib.error
import urllib.request
from urllib.parse import quote

from src.errors import PackageNotFoundError, RepositoryError
from src.requirement import normalize, parse_requirement

TIMEOUT_SECONDS = 15
HTTP_NOT_FOUND = 404
USER_AGENT = "depgraph-study-tool/1.0"
TEST_NAME_PATTERN = re.compile(r"^[A-Z]+$")


class PypiRepository:
    """Python package index that serves the PyPI JSON API.

    The package description is requested from
    ``<base_url>/<package>/json``; no package manager is used.
    """

    def __init__(self, base_url):
        """Remember the root URL of the JSON API."""
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def canonical_name(name):
        """Return the name under which the repository knows a package."""
        return normalize(name)

    def package_url(self, package):
        """Return the URL of the JSON description of a package."""
        return f"{self.base_url}/{quote(normalize(package))}/json"

    def dependencies(self, package):
        """Return the names of the direct dependencies of a package."""
        data = self._fetch_json(package)
        info = data.get("info") or {}
        names = []
        for text in info.get("requires_dist") or []:
            name = self._parse(text, package)
            if name and name not in names:
                names.append(name)
        return names

    @staticmethod
    def _parse(text, package):
        """Parse one requirement of a package, reporting bad data."""
        try:
            return parse_requirement(text)
        except ValueError as error:
            raise RepositoryError(f"{package}: {error}") from None

    def _fetch_json(self, package):
        """Download and decode the JSON description of a package."""
        url = self.package_url(package)
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(
                request, timeout=TIMEOUT_SECONDS
            ) as response:
                data = json.load(response)
        except urllib.error.HTTPError as error:
            raise _http_error(error, package, url) from None
        except OSError as error:
            raise RepositoryError(f"cannot reach {url}: {error}") from None
        except ValueError:
            raise RepositoryError(f"{url}: response is not valid JSON") \
                from None
        if not isinstance(data, dict):
            raise RepositoryError(f"{url}: unexpected response format")
        return data


def _http_error(error, package, url):
    """Convert an HTTP error to a repository error."""
    if error.code == HTTP_NOT_FOUND:
        return PackageNotFoundError(f"package not found: {package}")
    return RepositoryError(f"{url}: HTTP error {error.code}")


class TestRepository:
    """Repository described by a text file.

    Every line has the form ``NAME: DEP DEP ...``; names are
    uppercase Latin letters. Text after ``#`` is a comment.
    """

    def __init__(self, graph):
        """Create a repository from a {name: [dependencies]} dict."""
        self.graph = graph

    @classmethod
    def from_file(cls, path):
        """Read a test repository file."""
        try:
            with open(path, encoding="utf-8-sig") as file:
                text = file.read()
        except (OSError, UnicodeDecodeError) as error:
            raise RepositoryError(f"cannot read {path}: {error}") from None
        return cls(parse_test_repository(text, path))

    @staticmethod
    def canonical_name(name):
        """Names of the test repository are used as they are."""
        return name

    def dependencies(self, package):
        """Return the direct dependencies of a package."""
        if package not in self.graph:
            raise PackageNotFoundError(f"package not found: {package}")
        return list(self.graph[package])


def parse_test_repository(text, source):
    """Parse the text of a test repository into a dict."""
    graph = {}
    for number, line in enumerate(text.splitlines(), start=1):
        content = line.split("#", 1)[0].strip()
        if not content:
            continue
        where = f"{source}:{number}"
        name, deps = _parse_line(content, where)
        if name in graph:
            raise RepositoryError(f"{where}: package {name} is defined twice")
        graph[name] = deps
    return graph


def _parse_line(content, where):
    """Parse one line ``NAME: DEP DEP`` and check the names."""
    name, separator, rest = content.partition(":")
    if not separator:
        raise RepositoryError(f"{where}: expected 'NAME: DEP DEP ...'")
    name = name.strip()
    deps = []
    for dep in rest.split():
        if dep not in deps:
            deps.append(dep)
    for item in [name] + deps:
        if not TEST_NAME_PATTERN.match(item):
            raise RepositoryError(
                f"{where}: invalid package name {item!r} "
                "(only uppercase Latin letters are allowed)"
            )
    return name, deps
