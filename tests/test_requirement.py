"""Tests for the requirement string parser."""

import unittest

from src.requirement import normalize, parse_requirement


class RequirementTests(unittest.TestCase):
    """Parsing of Requires-Dist strings."""

    def test_plain_name(self):
        """A bare name is returned as is."""
        self.assertEqual(parse_requirement("idna"), "idna")

    def test_version_in_brackets(self):
        """The old-style version in brackets is ignored."""
        self.assertEqual(parse_requirement("idna (<4,>=2.5)"), "idna")

    def test_version_without_space(self):
        """A version specifier right after the name is ignored."""
        self.assertEqual(parse_requirement("urllib3<3,>=1.21.1"), "urllib3")

    def test_normalization(self):
        """Names are normalized."""
        self.assertEqual(
            parse_requirement("charset_normalizer (<4,>=2)"),
            "charset-normalizer",
        )
        self.assertEqual(normalize("Foo.Bar__baz"), "foo-bar-baz")

    def test_extras_of_dependency(self):
        """Extras of a dependency do not change its name."""
        self.assertEqual(parse_requirement("httpx[http2]>=0.2"), "httpx")

    def test_extra_marker_is_optional(self):
        """Dependencies needed only for an extra are skipped."""
        text = "PySocks (!=1.5.7,>=1.5.6) ; extra == 'socks'"
        self.assertIsNone(parse_requirement(text))

    def test_other_marker_is_kept(self):
        """Other environment markers do not remove the dependency."""
        text = "colorama; platform_system == 'Windows'"
        self.assertEqual(parse_requirement(text), "colorama")

    def test_invalid(self):
        """A string without a name is rejected."""
        with self.assertRaises(ValueError):
            parse_requirement(">=1.0")


if __name__ == "__main__":
    unittest.main()
