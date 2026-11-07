"""Tests for the PlantUML output."""

import unittest

from src.plantuml import to_plantuml


class PlantUmlTests(unittest.TestCase):
    """Structure of the generated diagram."""

    def test_simple(self):
        """Nodes and arrows are generated."""
        lines = to_plantuml("A", {"A": ["B"], "B": []})
        self.assertEqual(lines, [
            "@startuml",
            "title Dependency graph of A",
            'rectangle "A" as n0 #LightBlue',
            'rectangle "B" as n1',
            "n0 --> n1",
            "@enduml",
        ])

    def test_names_with_dashes(self):
        """Names with '-' are kept in labels, aliases stay simple."""
        lines = to_plantuml("a-b", {"a-b": ["c.d"], "c.d": []})
        self.assertIn('rectangle "c.d" as n1', lines)
        self.assertIn("n0 --> n1", lines)

    def test_cycle_and_self_loop(self):
        """Cyclic and self arrows are drawn."""
        lines = to_plantuml("A", {"A": ["A", "B"], "B": ["A"]})
        for arrow in ("n0 --> n0", "n0 --> n1", "n1 --> n0"):
            self.assertIn(arrow, lines)

    def test_single_package(self):
        """A package without dependencies has no arrows."""
        lines = to_plantuml("A", {"A": []})
        self.assertFalse([line for line in lines if "-->" in line])


if __name__ == "__main__":
    unittest.main()
