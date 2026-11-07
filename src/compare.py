"""Comparison of the results with the real package manager (pip).

The package is installed by pip into a temporary virtual
environment. The order printed by pip ("Installing collected
packages: ...") is compared with the load order of this tool, and
the graph reported by pipdeptree is compared with our graph.
"""

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
import tempfile
import venv
from collections import deque
from dataclasses import dataclass

from src.config import load_config
from src.errors import CompareError, ToolError
from src.graph import build_graph
from src.main import report, warn
from src.order import load_order
from src.repository import PypiRepository
from src.requirement import normalize

INSTALL_LINE = re.compile(
    r"^Installing collected packages:\s*(.+)$", re.MULTILINE
)
DEFAULT_CONFIG = "config.yaml"
EXIT_OK = 0
EXIT_ERROR = 1


@dataclass
class OrderReport:
    """Result of comparing two load orders."""

    only_ours: list
    only_pip: list
    same_order: bool
    pip_breaks: list


def parse_install_order(text):
    """Extract the package order from the output of ``pip install``."""
    match = INSTALL_LINE.search(text)
    if match is None:
        raise CompareError(
            "no 'Installing collected packages' line in the pip output"
        )
    names = [part.strip() for part in match.group(1).split(",")]
    return [normalize(name) for name in names if name]


def order_violations(order, graph):
    """Return pairs (package, dependency) placed in the wrong order.

    A dependency must come before the package that needs it; only
    packages present in ``order`` are checked.
    """
    position = {name: index for index, name in enumerate(order)}
    pairs = []
    for name, deps in graph.items():
        for dep in deps:
            if name in position and dep in position and dep != name:
                if position[dep] > position[name]:
                    pairs.append((name, dep))
    return pairs


def compare_orders(ours, pip_order, graph):
    """Compare our load order with the order used by pip."""
    pip_set, our_set = set(pip_order), set(ours)
    common_ours = [name for name in ours if name in pip_set]
    common_pip = [name for name in pip_order if name in our_set]
    return OrderReport(
        only_ours=[name for name in ours if name not in pip_set],
        only_pip=[name for name in pip_order if name not in our_set],
        same_order=common_ours == common_pip,
        pip_breaks=order_violations(pip_order, graph),
    )


def format_order_report(ours, pip_order, result):
    """Return the comparison of two orders as text lines."""
    lines = [
        f"Our load order ({len(ours)}): {', '.join(ours)}",
        f"pip install order ({len(pip_order)}): {', '.join(pip_order)}",
        "Only in our result: " + (", ".join(result.only_ours) or "-"),
        "Only in pip: " + (", ".join(result.only_pip) or "-"),
        "Common packages in the same order: "
        + ("yes" if result.same_order else "no"),
    ]
    if result.pip_breaks:
        pairs = ", ".join(f"{a} needs {b}" for a, b in result.pip_breaks)
        lines.append(f"Order of pip breaks our dependencies: {pairs}")
    else:
        lines.append("Order of pip respects all dependencies of our graph")
    return lines


def read_text(path):
    """Read a saved output of the real tool."""
    try:
        with open(path, encoding="utf-8-sig") as file:
            return file.read()
    except (OSError, UnicodeDecodeError) as error:
        raise CompareError(f"cannot read {path}: {error}") from None


def venv_python(folder):
    """Return the path of the Python executable of a virtualenv."""
    if os.name == "nt":
        return os.path.join(folder, "Scripts", "python.exe")
    return os.path.join(folder, "bin", "python")


@contextlib.contextmanager
def sandbox():
    """Create a temporary virtual environment; yield its Python."""
    with tempfile.TemporaryDirectory() as folder:
        venv.create(folder, with_pip=True)
        yield venv_python(folder)


def run_module(python, *args):
    """Run ``python -m <args>`` and return its output."""
    command = [python, "-m", *args]
    result = subprocess.run(
        command, capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False,
    )
    if result.returncode:
        raise CompareError(f"{' '.join(args)} failed: {result.stderr[-300:]}")
    return result.stdout


def pip_install_output(package, saved):
    """Return the output of ``pip install`` (saved or fresh)."""
    if saved:
        return read_text(saved)
    with sandbox() as python:
        return run_module(
            python, "pip", "install", "--no-input",
            "--disable-pip-version-check", package,
        )


def parse_pipdeptree(text):
    """Convert the JSON of ``pipdeptree --json`` to {name: [deps]}."""
    try:
        graph = {}
        for item in json.loads(text):
            name = normalize(item["package"]["key"])
            graph[name] = [normalize(dep["key"])
                           for dep in item["dependencies"]]
    except (ValueError, KeyError, TypeError):
        raise CompareError("unexpected pipdeptree JSON format") from None
    return graph


def reachable(graph, root):
    """Return the part of the graph reachable from ``root`` (BFS)."""
    result = {}
    queue = deque([root])
    while queue:
        name = queue.popleft()
        if name in result:
            continue
        result[name] = graph.get(name, [])
        queue.extend(result[name])
    return result


def edge_set(graph):
    """Return the set of (package, dependency) pairs of a graph."""
    return {(name, dep) for name, deps in graph.items() for dep in deps}


def format_graph_report(ours, other):
    """Compare our graph with the pipdeptree graph, as text lines."""
    our_edges, other_edges = edge_set(ours), edge_set(other)
    only_ours = sorted(set(ours) - set(other))
    only_other = sorted(set(other) - set(ours))
    lines = [
        f"Packages: ours {len(ours)}, pipdeptree {len(other)}",
        "Only in our graph: " + (", ".join(only_ours) or "-"),
        "Only in pipdeptree: " + (", ".join(only_other) or "-"),
        f"Dependencies: ours {len(our_edges)}, "
        f"pipdeptree {len(other_edges)}",
    ]
    for title, edges in (("our graph", our_edges - other_edges),
                         ("pipdeptree", other_edges - our_edges)):
        text = ", ".join(f"{a}->{b}" for a, b in sorted(edges)) or "-"
        lines.append(f"Dependencies only in {title}: {text}")
    return lines


def pipdeptree_output(package, saved):
    """Return the JSON of pipdeptree (saved or fresh)."""
    if saved:
        return read_text(saved)
    with sandbox() as python:
        run_module(python, "pip", "install", "--no-input",
                   "--disable-pip-version-check", package)
        run_module(python, "pip", "install", "--no-input",
                   "--disable-pip-version-check", "pipdeptree")
        return run_module(python, "pipdeptree", "--json", "-p", package)


def parse_args(argv):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="compare",
        description="Compare our results with pip and pipdeptree.",
    )
    parser.add_argument("--config", default=DEFAULT_CONFIG, metavar="PATH")
    parser.add_argument(
        "--what", choices=("order", "graph"), default="order",
        help="order: compare with pip; graph: compare with pipdeptree",
    )
    parser.add_argument(
        "--saved", metavar="FILE",
        help="text saved from the real tool instead of running it",
    )
    return parser.parse_args(argv)


def build_our_graph(config):
    """Build our graph for a configuration with a real repository."""
    if config.test_mode:
        raise CompareError("comparison needs a real repository")
    repository = PypiRepository(config.repository)
    root = repository.canonical_name(config.package_name)
    graph = build_graph(root, repository, config.substring, warn)
    return root, graph


def compare_graph(config, saved):
    """Compare our graph with the one reported by pipdeptree."""
    root, graph = build_our_graph(config)
    theirs = parse_pipdeptree(pipdeptree_output(root, saved))
    for line in format_graph_report(graph, reachable(theirs, root)):
        print(line)


def compare_order(config, saved):
    """Build our order for the configured package and compare it."""
    root, graph = build_our_graph(config)
    ours = load_order(graph, root)
    pip_order = parse_install_order(pip_install_output(root, saved))
    result = compare_orders(ours, pip_order, graph)
    for line in format_order_report(ours, pip_order, result):
        print(line)


def main(argv=None):
    """Run the comparison and return the process exit code."""
    args = parse_args(argv)
    try:
        config = load_config(args.config)
        if args.what == "graph":
            compare_graph(config, args.saved)
        else:
            compare_order(config, args.saved)
    except ToolError as error:
        report(error)
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
