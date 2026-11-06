"""Command line entry point of the dependency graph tool."""

import argparse
import sys

from src.config import load_config
from src.errors import ToolError
from src.repository import PypiRepository

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


def print_dependencies(package, names):
    """Print the direct dependencies of a package."""
    if not names:
        print(f"{package} has no direct dependencies")
        return
    print(f"Direct dependencies of {package} ({len(names)}):")
    for name in names:
        print(f"  {name}")


def report(error):
    """Print every problem of an error to stderr."""
    for problem in error.problems:
        print(f"error: {problem}", file=sys.stderr)


def main(argv=None):
    """Run the tool and return the process exit code."""
    args = parse_args(argv)
    try:
        config = load_config(args.config)
        if config.test_mode:
            raise ToolError("test mode is not supported in this version")
        repository = PypiRepository(config.repository)
        package = repository.canonical_name(config.package_name)
        print_dependencies(package, repository.dependencies(package))
    except ToolError as error:
        report(error)
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
