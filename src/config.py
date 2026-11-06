"""Loading and validation of the YAML configuration file."""

import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import yaml

from src.errors import ConfigError

KEYS = ("package_name", "repository", "test_mode", "filter")
REQUIRED = ("package_name", "repository")
NAME_PATTERN = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")
URL_SCHEMES = ("http", "https")


@dataclass(frozen=True)
class Config:
    """Validated user settings."""

    package_name: str
    repository: str
    test_mode: bool
    substring: str

    def as_pairs(self):
        """Return (key, value) pairs in the order of the config file."""
        return [
            ("package_name", self.package_name),
            ("repository", self.repository),
            ("test_mode", self.test_mode),
            ("filter", self.substring),
        ]


def load_config(path):
    """Read, validate and return the configuration from ``path``.

    Raises ConfigError listing every problem that was found.
    """
    return build_config(_read_yaml(path))


def _read_yaml(path):
    """Read the YAML file and return its top-level mapping."""
    try:
        with open(path, encoding="utf-8-sig") as file:
            data = yaml.safe_load(file)
    except FileNotFoundError:
        raise ConfigError([f"configuration file not found: {path}"]) from None
    except (OSError, UnicodeDecodeError) as error:
        raise ConfigError([f"cannot read {path}: {error}"]) from None
    except yaml.YAMLError as error:
        text = " ".join(str(error).split())
        raise ConfigError([f"invalid YAML in {path}: {text}"]) from None
    if not isinstance(data, dict):
        raise ConfigError([f"{path}: expected a mapping of parameters"])
    return data


def build_config(raw):
    """Validate a dict of raw values and create a Config."""
    test_mode = raw.get("test_mode", False)
    problems = []
    problems += [f"unknown parameter: {key}" for key in raw
                 if key not in KEYS]
    problems += [f"missing required parameter: {key}" for key in REQUIRED
                 if key not in raw]
    problems += _check_name(raw.get("package_name", ""), "package_name" in raw)
    problems += _check_repository(raw, test_mode is True)
    problems += _check_test_mode(test_mode)
    problems += _check_filter(raw.get("filter", ""))
    if problems:
        raise ConfigError(problems)
    return Config(
        package_name=raw["package_name"],
        repository=raw["repository"],
        test_mode=test_mode,
        substring=raw.get("filter", ""),
    )


def _check_name(value, present):
    """Check the package name."""
    if not present:
        return []
    if not isinstance(value, str):
        return ["package_name: must be a string"]
    if not value.strip():
        return ["package_name: must not be empty"]
    if not NAME_PATTERN.match(value):
        return [f"package_name: invalid package name {value!r} "
                "(allowed: letters, digits, '.', '_' and '-')"]
    return []


def _check_repository(raw, test_mode):
    """Check the repository URL or the path to the test repository."""
    if "repository" not in raw:
        return []
    value = raw["repository"]
    if not isinstance(value, str) or not value.strip():
        return ["repository: must be a non-empty string"]
    if test_mode:
        if not os.path.isfile(value):
            return [f"repository: test repository file not found: {value}"]
        return []
    parsed = urlparse(value)
    if parsed.scheme not in URL_SCHEMES or not parsed.netloc:
        return [f"repository: {value!r} is not an http(s) URL "
                "(use test_mode: true to give a file path)"]
    return []


def _check_test_mode(value):
    """Check the test repository mode flag."""
    if isinstance(value, bool):
        return []
    return [f"test_mode: must be true or false, got {value!r}"]


def _check_filter(value):
    """Check the package filter substring."""
    if isinstance(value, str):
        return []
    return [f"filter: must be a string, got {value!r}"]
