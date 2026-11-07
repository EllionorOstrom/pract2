"""Tests for the comparison with pip (no network, no pip runs)."""

import os
import tempfile
import unittest

from src.compare import (compare_orders, format_graph_report,
                         format_order_report, order_violations,
                         parse_install_order, parse_pipdeptree, read_text,
                         reachable)
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


TREE_JSON = """[
 {"package": {"key": "requests", "package_name": "requests"},
  "dependencies": [{"key": "idna"}, {"key": "charset-normalizer"}]},
 {"package": {"key": "idna"}, "dependencies": []},
 {"package": {"key": "charset-normalizer"}, "dependencies": []},
 {"package": {"key": "other"}, "dependencies": [{"key": "idna"}]}
]"""


class GraphCompareTests(unittest.TestCase):
    """Stage 5: comparison with pipdeptree."""

    def test_parse_pipdeptree(self):
        """The flat JSON becomes an adjacency dict."""
        graph = parse_pipdeptree(TREE_JSON)
        self.assertEqual(graph["requests"], ["idna", "charset-normalizer"])

    def test_parse_pipdeptree_errors(self):
        """Broken JSON and wrong structure are errors."""
        for text in ("{bad", '{"a": 1}', "[1]"):
            with self.subTest(text=text):
                with self.assertRaises(CompareError):
                    parse_pipdeptree(text)

    def test_reachable(self):
        """Only packages reachable from the root are kept."""
        graph = parse_pipdeptree(TREE_JSON)
        self.assertNotIn("other", reachable(graph, "requests"))
        self.assertEqual(len(reachable(graph, "requests")), 3)

    def test_identical_graphs(self):
        """Equal graphs have no differences."""
        graph = {"a": ["b"], "b": []}
        text = "\n".join(format_graph_report(graph, graph))
        self.assertIn("Only in our graph: -", text)
        self.assertIn("Dependencies only in pipdeptree: -", text)

    def test_differences(self):
        """Extra packages and links are listed."""
        ours = {"a": ["b", "c"], "b": [], "c": []}
        theirs = {"a": ["b"], "b": ["d"], "d": []}
        text = "\n".join(format_graph_report(ours, theirs))
        self.assertIn("Only in our graph: c", text)
        self.assertIn("Only in pipdeptree: d", text)
        self.assertIn("only in our graph: a->c", text)
        self.assertIn("only in pipdeptree: b->d", text)


if __name__ == "__main__":
    unittest.main()
