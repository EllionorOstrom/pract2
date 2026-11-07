"""Tests for the load order."""

import unittest

from src.order import format_order, load_order


class OrderTests(unittest.TestCase):
    """Dependencies must be loaded before their dependents."""

    def test_single(self):
        """A package without dependencies is alone."""
        self.assertEqual(load_order({"A": []}, "A"), ["A"])

    def test_chain(self):
        """A chain is loaded from the end."""
        graph = {"A": ["B"], "B": ["C"], "C": []}
        self.assertEqual(load_order(graph, "A"), ["C", "B", "A"])

    def test_diamond(self):
        """A shared dependency is loaded once, before both users."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        self.assertEqual(load_order(graph, "A"), ["D", "B", "C", "A"])

    def test_cycle_terminates(self):
        """A cycle does not hang the traversal."""
        graph = {"A": ["B"], "B": ["C"], "C": ["A", "D"], "D": []}
        order = load_order(graph, "A")
        self.assertEqual(sorted(order), ["A", "B", "C", "D"])
        self.assertEqual(order[-1], "A")
        self.assertLess(order.index("D"), order.index("C"))

    def test_self_loop(self):
        """A self-dependency is ignored."""
        self.assertEqual(load_order({"A": ["A", "B"], "B": []}, "A"),
                         ["B", "A"])

    def test_every_dependency_first(self):
        """In an acyclic graph every dependency precedes its package."""
        graph = {"A": ["B", "C", "E"], "B": ["C", "D"], "C": ["D"],
                 "D": [], "E": ["D"]}
        order = load_order(graph, "A")
        for name, deps in graph.items():
            for dep in deps:
                self.assertLess(order.index(dep), order.index(name))

    def test_format(self):
        """Lines are numbered from one."""
        self.assertEqual(
            format_order("A", ["B", "A"]),
            ["Load order of A (dependencies first):", "  1. B", "  2. A"],
        )


if __name__ == "__main__":
    unittest.main()
