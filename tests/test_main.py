"""Tests for the command line entry point."""

import contextlib
import io
import unittest

from src.main import EXIT_ERROR, EXIT_OK, format_value, main


class MainTests(unittest.TestCase):
    """Stage 1: printing of parameters and error exit codes."""

    def run_main(self, path):
        """Run main and return (code, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out):
            with contextlib.redirect_stderr(err):
                code = main(["--config", path])
        return code, out.getvalue(), err.getvalue()

    def test_prints_key_values(self):
        """All parameters are printed as key: value."""
        code, out, _ = self.run_main("configs/remote.yaml")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("package_name: flask\n", out)
        self.assertIn("test_mode: false\n", out)
        self.assertIn("filter: werk\n", out)

    def test_error_exit_code(self):
        """An invalid config gives an error and a non-zero code."""
        code, _, err = self.run_main("configs/errors/all_wrong.yaml")
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(len(err.splitlines()), 4)

    def test_missing_config(self):
        """A missing config file gives an error."""
        code, _, err = self.run_main("configs/none.yaml")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("not found", err)

    def test_format_value(self):
        """Values are formatted for output."""
        self.assertEqual(format_value(True), "true")
        self.assertEqual(format_value(""), '""')


if __name__ == "__main__":
    unittest.main()
