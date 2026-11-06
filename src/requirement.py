"""Parsing of Python requirement strings (Requires-Dist, PEP 508)."""

import re

NAME_PATTERN = re.compile(r"^\s*([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)")
EXTRA_PATTERN = re.compile(r"\bextra\b")
SEPARATORS = re.compile(r"[-_.]+")


def normalize(name):
    """Return the canonical form of a package name (PEP 503)."""
    return SEPARATORS.sub("-", name).lower()


def parse_requirement(text):
    """Return the normalized package name of a requirement string.

    Returns None for optional dependencies, i.e. requirements that
    are only needed for an "extra" (``; extra == "socks"``).
    Raises ValueError if the string does not start with a package name.
    """
    requirement, _, marker = text.partition(";")
    if EXTRA_PATTERN.search(marker):
        return None
    match = NAME_PATTERN.match(requirement)
    if match is None:
        raise ValueError(f"invalid requirement: {text!r}")
    return normalize(match.group(1))
