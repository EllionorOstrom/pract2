"""Command line entry point of the dependency graph tool."""

import argparse
import sys

from src.config import load_config
from src.errors import ToolError

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


def format_value(value):
    """Format a parameter value for key-value output."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return value or '""'


def print_params(config):
    """Print every user-configurable parameter as key: value."""
    for key, value in config.as_pairs():
        print(f"{key}: {format_value(value)}")


def report(error):
    """Print every problem of an error to stderr."""
    for problem in error.problems:
        print(f"error: {problem}", file=sys.stderr)


def main(argv=None):
    """Run the tool and return the process exit code."""
    args = parse_args(argv)
    try:
        config = load_config(args.config)
    except ToolError as error:
        report(error)
        return EXIT_ERROR
    print_params(config)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
