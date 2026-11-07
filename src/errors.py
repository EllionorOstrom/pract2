"""Exceptions that are reported to the user without a traceback."""


class ToolError(Exception):
    """Base class for all expected, user-facing errors."""

    @property
    def problems(self):
        """Return the list of messages to show to the user."""
        return [str(self)]


class ConfigError(ToolError):
    """The configuration file is missing or contains invalid values."""

    def __init__(self, problems):
        """Keep every found problem, not only the first one."""
        self._problems = list(problems)
        super().__init__("; ".join(self._problems))

    @property
    def problems(self):
        """Return all problems found in the configuration."""
        return self._problems


class RepositoryError(ToolError):
    """Package data cannot be obtained from the repository."""


class PackageNotFoundError(RepositoryError):
    """The repository does not contain the requested package."""


class GraphError(ToolError):
    """The dependency graph cannot be built."""
