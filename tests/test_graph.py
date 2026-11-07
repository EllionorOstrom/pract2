"""Tests for BFS construction and cycle search."""

import unittest

from src.errors import GraphError, PackageNotFoundError
from src.graph import (build_graph, count_edges, find_cycles, format_graph,
                       is_excluded)
from src.repository import TestRepository, parse_test_repository


def repo(text):
    """Create a test repository from text."""
    return TestRepository(parse_test_repository(text, "t"))


class BuildTests(unittest.TestCase):
    """Graph construction."""

    def test_bfs_order(self):
        """Packages are stored level by level."""
        graph = build_graph("A", repo("A: B C\nB: D\nC: E\nD:\nE:\n"))
        self.assertEqual(list(graph), ["A", "B", "C", "D", "E"])

    def test_transitive(self):
        """Transitive dependencies are included."""
        graph = build_graph("A", repo("A: B\nB: C\nC:\n"))
        self.assertEqual(graph["B"], ["C"])
        self.assertIn("C", graph)

    def test_shared_dependency_visited_once(self):
        """A package reached twice appears once."""
        graph = build_graph("A", repo("A: B C\nB: D\nC: D\nD:\n"))
        self.assertEqual(len(graph), 4)
        self.assertEqual(count_edges(graph), 4)

    def test_cycle_terminates(self):
        """Cyclic dependencies do not loop forever."""
        graph = build_graph("A", repo("A: B\nB: A\n"))
        self.assertEqual(graph, {"A": ["B"], "B": ["A"]})

    def test_long_chain_without_recursion(self):
        """A very deep chain works (no recursion limit)."""
        size = 5000
        names = [f"N{i}" for i in range(size)]
        graph = {}
        for index, name in enumerate(names):
            graph[name] = [names[index + 1]] if index + 1 < size else []
        result = build_graph(names[0], TestRepository(graph))
        self.assertEqual(len(result), size)

    def test_filter_removes_branch(self):
        """A filtered package and its subtree are not analysed."""
        text = "A: B C\nB: D\nC:\nD:\n"
        graph = build_graph("A", repo(text), "B")
        self.assertEqual(graph, {"A": ["C"], "C": []})

    def test_filter_ignores_case(self):
        """The filter is case-insensitive."""
        self.assertTrue(is_excluded("Flask", "fla"))
        self.assertFalse(is_excluded("Flask", ""))

    def test_filtered_root(self):
        """A root excluded by the filter is an error."""
        with self.assertRaises(GraphError):
            build_graph("A", repo("A:\n"), "A")

    def test_missing_root(self):
        """A root that is not in the repository is an error."""
        with self.assertRaises(PackageNotFoundError):
            build_graph("Z", repo("A:\n"))

    def test_missing_dependency_warns(self):
        """A missing dependency is a leaf and a warning."""
        warnings = []
        graph = build_graph("A", repo("A: Z\n"), warn=warnings.append)
        self.assertEqual(graph["Z"], [])
        self.assertEqual(len(warnings), 1)


class CycleTests(unittest.TestCase):
    """Cycle detection."""

    def test_no_cycles(self):
        """An acyclic graph has no cycles."""
        self.assertEqual(find_cycles({"A": ["B"], "B": []}), [])

    def test_simple_cycle(self):
        """A two-node cycle is found."""
        cycles = find_cycles({"A": ["B"], "B": ["A"]})
        self.assertEqual(cycles, [["A", "B", "A"]])

    def test_self_loop(self):
        """A self-dependency is a cycle."""
        self.assertEqual(find_cycles({"A": ["A"]}), [["A", "A"]])

    def test_long_cycle(self):
        """The cycle starts at the repeated node."""
        graph = {"A": ["B"], "B": ["C"], "C": ["B", "D"], "D": []}
        self.assertEqual(find_cycles(graph), [["B", "C", "B"]])


class TestRepositoryTests(unittest.TestCase):
    """Parsing of the test repository file."""

    def test_comments_and_blank_lines(self):
        """Comments and empty lines are ignored."""
        graph = parse_test_repository("# c\n\nA: B # x\nB:\n", "t")
        self.assertEqual(graph, {"A": ["B"], "B": []})

    def test_duplicate_dependencies_removed(self):
        """Repeated dependencies are stored once."""
        self.assertEqual(parse_test_repository("A: B B\n", "t"),
                         {"A": ["B"]})

    def test_format_graph(self):
        """Graph lines are readable."""
        lines = format_graph({"A": ["B"], "B": []})
        self.assertEqual(lines, ["A -> B", "B -> (no dependencies)"])

    def test_errors(self):
        """Syntax, name and duplicate errors are reported."""
        for text in ["A B\n", "a: B\n", "A: b\n", "A: B\nA: C\n"]:
            with self.subTest(text=text):
                with self.assertRaises(Exception) as context:
                    parse_test_repository(text, "t")
                self.assertIn("t:", str(context.exception))


if __name__ == "__main__":
    unittest.main()
