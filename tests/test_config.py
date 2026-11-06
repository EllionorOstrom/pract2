"""Tests for configuration loading and validation."""

import os
import tempfile
import unittest

from src.config import build_config, load_config
from src.errors import ConfigError

GOOD = {
    "package_name": "requests",
    "repository": "https://pypi.org/pypi",
}


class ValidationTests(unittest.TestCase):
    """Validation of every parameter."""

    def problems(self, **changes):
        """Return the problems found for GOOD modified by ``changes``."""
        raw = dict(GOOD)
        raw.update(changes)
        with self.assertRaises(ConfigError) as context:
            build_config(raw)
        return context.exception.problems

    def test_defaults(self):
        """Optional parameters get default values."""
        config = build_config(dict(GOOD))
        self.assertFalse(config.test_mode)
        self.assertEqual(config.substring, "")

    def test_all_parameters(self):
        """All parameters are accepted together."""
        config = build_config(dict(GOOD, test_mode=False, filter="x"))
        self.assertEqual(config.substring, "x")

    def test_empty_name(self):
        """An empty package name is rejected."""
        self.assertIn("must not be empty", self.problems(package_name="")[0])

    def test_invalid_name(self):
        """A name with forbidden characters is rejected."""
        self.assertIn("invalid package name",
                      self.problems(package_name="a b")[0])

    def test_name_type(self):
        """A non-string name is rejected."""
        self.assertIn("must be a string", self.problems(package_name=5)[0])

    def test_bad_url(self):
        """A repository that is not an http(s) URL is rejected."""
        self.assertIn("not an http(s) URL", self.problems(repository="x")[0])

    def test_ftp_url(self):
        """Only http and https schemes are accepted."""
        self.assertTrue(self.problems(repository="ftp://host/x"))

    def test_missing_test_file(self):
        """In test mode the repository must be an existing file."""
        problems = self.problems(repository="no/such/file", test_mode=True)
        self.assertIn("not found", problems[0])

    def test_existing_test_file(self):
        """In test mode an existing file path is accepted."""
        with tempfile.NamedTemporaryFile() as file:
            config = build_config(
                {"package_name": "A", "repository": file.name,
                 "test_mode": True}
            )
        self.assertTrue(config.test_mode)

    def test_bad_mode(self):
        """test_mode must be a boolean."""
        self.assertIn("test_mode", self.problems(test_mode="maybe")[0])

    def test_bad_filter(self):
        """filter must be a string."""
        self.assertIn("filter", self.problems(filter=1)[0])

    def test_unknown_parameter(self):
        """Unknown parameters are rejected."""
        self.assertIn("unknown parameter", self.problems(color="red")[0])

    def test_missing_parameters(self):
        """Missing required parameters are reported."""
        with self.assertRaises(ConfigError) as context:
            build_config({})
        self.assertEqual(len(context.exception.problems), 2)

    def test_all_problems_reported(self):
        """Several problems are reported at once."""
        problems = self.problems(package_name="", filter=1)
        self.assertEqual(len(problems), 2)


class FileTests(unittest.TestCase):
    """Reading the YAML file."""

    def setUp(self):
        """Create a temporary folder."""
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def write(self, text):
        """Write a config file and return its path."""
        path = os.path.join(self.folder.name, "c.yaml")
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        return path

    def test_load(self):
        """A valid file is loaded."""
        path = self.write("package_name: flask\nrepository: http://h/p\n")
        self.assertEqual(load_config(path).package_name, "flask")

    def test_missing_file(self):
        """A missing file is reported."""
        with self.assertRaises(ConfigError) as context:
            load_config(os.path.join(self.folder.name, "none.yaml"))
        self.assertIn("not found", context.exception.problems[0])

    def test_broken_yaml(self):
        """Invalid YAML is reported."""
        with self.assertRaises(ConfigError) as context:
            load_config(self.write("a: [b\n"))
        self.assertIn("invalid YAML", context.exception.problems[0])

    def test_not_a_mapping(self):
        """A list at the top level is reported."""
        with self.assertRaises(ConfigError):
            load_config(self.write("- a\n- b\n"))

    def test_empty_file(self):
        """An empty file is reported."""
        with self.assertRaises(ConfigError):
            load_config(self.write(""))


if __name__ == "__main__":
    unittest.main()
