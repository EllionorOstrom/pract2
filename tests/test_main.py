"""Tests for the command line entry point."""

import contextlib
import io
import unittest

from src.main import EXIT_ERROR, EXIT_OK, main, print_dependencies


class MainTests(unittest.TestCase):
    """Stage 2: output and error exit codes."""

    def run_main(self, path):
        """Run main and return (code, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out):
            with contextlib.redirect_stderr(err):
                code = main(["--config", path])
        return code, out.getvalue(), err.getvalue()

    def test_invalid_config(self):
        """An invalid config gives an error and a non-zero code."""
        code, _, err = self.run_main("configs/errors/all_wrong.yaml")
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(len(err.splitlines()), 4)

    def test_test_mode_not_supported(self):
        """Test mode is not available at this stage."""
        code, _, err = self.run_main("configs/test.yaml")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("not supported", err)

    def test_print_dependencies(self):
        """Dependencies are printed one per line."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            print_dependencies("demo", ["a", "b"])
        self.assertEqual(
            out.getvalue(),
            "Direct dependencies of demo (2):\n  a\n  b\n",
        )

    def test_print_no_dependencies(self):
        """An empty list is announced."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            print_dependencies("demo", [])
        self.assertIn("no direct dependencies", out.getvalue())


if __name__ == "__main__":
    unittest.main()
