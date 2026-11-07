"""Command line entry point of the dependency graph tool."""

import argparse
import sys

from src.config import load_config
from src.errors import ToolError
from src.graph import build_graph, count_edges, find_cycles, format_graph
from src.repository import PypiRepository, TestRepository

EXIT_OK = 0
EXIT_ERROR = 1
DEFAULT_CONFIG = "config.yaml"


def parse_args(argv):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="depgraph",
        description="Dependency graph visualizer for Python packages.",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        metavar="PATH",
        help=f"path to the YAML configuration (default: {DEFAULT_CONFIG})",
    )
    return parser.parse_args(argv)


def warn(message):
    """Print a warning to stderr."""
    print(f"warning: {message}", file=sys.stderr)


def report(error):
    """Print every problem of an error to stderr."""
    for problem in error.problems:
        print(f"error: {problem}", file=sys.stderr)


def open_repository(config):
    """Create the repository selected by the configuration."""
    if config.test_mode:
        return TestRepository.from_file(config.repository)
    return PypiRepository(config.repository)


def print_graph(root, graph, config):
    """Print the graph, its statistics and the cycles."""
    print(f"Dependency graph of {root} (BFS order):")
    if config.substring:
        print(f"Ignoring packages with {config.substring!r} in the name")
    for line in format_graph(graph):
        print(line)
    print(f"Packages: {len(graph)}, dependencies: {count_edges(graph)}")
    cycles = find_cycles(graph)
    if not cycles:
        print("No cyclic dependencies found")
        return
    print(f"Cyclic dependencies found: {len(cycles)}")
    for cycle in cycles:
        print("  " + " -> ".join(cycle))


def run(config):
    """Build and print the dependency graph for a configuration."""
    repository = open_repository(config)
    root = repository.canonical_name(config.package_name)
    graph = build_graph(root, repository, config.substring, warn)
    print_graph(root, graph, config)


def main(argv=None):
    """Run the tool and return the process exit code."""
    args = parse_args(argv)
    try:
        run(load_config(args.config))
    except ToolError as error:
        report(error)
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
