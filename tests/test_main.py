"""Tests for the command line entry point."""

import contextlib
import io
import unittest

from src.main import EXIT_ERROR, EXIT_OK, main


class MainTests(unittest.TestCase):
    """Stage 3: whole program in test mode."""

    def run_main(self, path):
        """Run main and return (code, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out):
            with contextlib.redirect_stderr(err):
                code = main(["--config", path])
        return code, out.getvalue(), err.getvalue()

    def test_simple_graph(self):
        """The diamond graph is printed in BFS order."""
        code, out, _ = self.run_main("configs/test_simple.yaml")
        self.assertEqual(code, EXIT_OK)
        expected = "A -> B, C\nB -> D\nC -> D\nD -> (no dependencies)\n"
        self.assertIn(expected, out)
        self.assertIn("Packages: 4, dependencies: 4", out)
        self.assertIn("No cyclic dependencies found", out)

    def test_cycle_reported(self):
        """A cycle is found and the program terminates."""
        code, out, _ = self.run_main("configs/test_cyclic.yaml")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("A -> B -> C -> A", out)

    def test_self_loop_and_second_cycle(self):
        """Self-dependency and a separate cycle are both reported."""
        _, out, _ = self.run_main("configs/test_self_loop.yaml")
        self.assertIn("  A -> A", out)
        self.assertIn("  B -> C -> B", out)

    def test_filter(self):
        """Filtered packages are absent from the output."""
        _, out, _ = self.run_main("configs/test_filter_d.yaml")
        self.assertIn("B -> (no dependencies)\n", out)
        self.assertNotIn("D ->", out)
        self.assertIn("Ignoring packages", out)

    def test_undefined_dependency_warns(self):
        """An undefined dependency gives a warning, not a failure."""
        code, out, err = self.run_main("configs/test_undefined.yaml")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Z -> (no dependencies)", out)
        self.assertIn("warning: package Z not found", err)

    def test_errors(self):
        """Every kind of broken input gives an error and code 1."""
        names = ["missing_root", "filter_root", "broken_syntax",
                 "broken_name", "broken_duplicate"]
        for name in names:
            with self.subTest(name=name):
                code, _, err = self.run_main(f"configs/test_{name}.yaml")
                self.assertEqual(code, EXIT_ERROR)
                self.assertTrue(err.startswith("error: "))


if __name__ == "__main__":
    unittest.main()
