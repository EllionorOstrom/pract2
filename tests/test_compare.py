"""Tests for the comparison with pip (no network, no pip runs)."""

import os
import tempfile
import unittest

from src.compare import (compare_orders, format_order_report,
                         order_violations, parse_install_order, read_text)
from src.errors import CompareError

PIP_OUTPUT = (
    "Collecting requests\n"
    "  Downloading requests-2.32.3-py3-none-any.whl (64 kB)\n"
    "Installing collected packages: urllib3, idna, charset-normalizer, "
    "certifi, requests\n"
    "Successfully installed certifi-2024.8.30 requests-2.32.3\n"
)


class CompareTests(unittest.TestCase):
    """Parsing pip output and comparing orders."""

    def test_parse_install_order(self):
        """Names are taken from the 'Installing collected' line."""
        self.assertEqual(
            parse_install_order(PIP_OUTPUT),
            ["urllib3", "idna", "charset-normalizer", "certifi", "requests"],
        )

    def test_parse_normalizes(self):
        """Names are normalized."""
        text = "Installing collected packages: Foo_Bar, baz\n"
        self.assertEqual(parse_install_order(text), ["foo-bar", "baz"])

    def test_parse_missing_line(self):
        """Output without the line is an error."""
        with self.assertRaises(CompareError):
            parse_install_order("Requirement already satisfied: x\n")

    def test_violations(self):
        """A dependency placed after its package is reported."""
        graph = {"A": ["B"], "B": []}
        self.assertEqual(order_violations(["A", "B"], graph), [("A", "B")])
        self.assertEqual(order_violations(["B", "A"], graph), [])

    def test_same_sets_different_order(self):
        """Different but valid orders are detected."""
        graph = {"A": ["B", "C"], "B": [], "C": []}
        result = compare_orders(["B", "C", "A"], ["C", "B", "A"], graph)
        self.assertFalse(result.same_order)
        self.assertEqual(result.pip_breaks, [])
        self.assertEqual(result.only_ours, [])

    def test_different_sets(self):
        """Packages present on one side only are listed."""
        graph = {"A": ["B"], "B": []}
        result = compare_orders(["B", "A"], ["B", "A", "extra"], graph)
        self.assertEqual(result.only_pip, ["extra"])
        self.assertTrue(result.same_order)

    def test_report_text(self):
        """The report mentions every part of the comparison."""
        graph = {"A": ["B"], "B": []}
        result = compare_orders(["B", "A"], ["B", "A"], graph)
        text = "\n".join(format_order_report(["B", "A"], ["B", "A"], result))
        self.assertIn("Common packages in the same order: yes", text)
        self.assertIn("respects all dependencies", text)

    def test_read_text(self):
        """A saved file is read; a missing file is an error."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "pip.txt")
            with open(path, "w", encoding="utf-8") as file:
                file.write("hello")
            self.assertEqual(read_text(path), "hello")
            with self.assertRaises(CompareError):
                read_text(os.path.join(folder, "none.txt"))


if __name__ == "__main__":
    unittest.main()
