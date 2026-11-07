"""Dependency graph: BFS construction, cycle search, text output."""

from collections import deque

from src.errors import GraphError, PackageNotFoundError

ON_PATH = "on_path"
DONE = "done"


def is_excluded(name, substring):
    """Tell whether a package must be ignored because of the filter.

    The comparison ignores case. An empty substring excludes nothing.
    """
    return bool(substring) and substring.lower() in name.lower()


def build_graph(root, repository, substring="", warn=None):
    """Build the transitive dependency graph with BFS (no recursion).

    Returns a dict {package: [direct dependencies]} in BFS order.
    Packages whose name contains ``substring`` are skipped. Cycles
    are safe because every package is visited only once.
    """
    if is_excluded(root, substring):
        raise GraphError(f"package {root} is excluded by the filter")
    graph = {}
    queue = deque([root])
    seen = {root}
    while queue:
        name = queue.popleft()
        deps = _load_dependencies(name, root, repository, substring, warn)
        graph[name] = deps
        for dep in deps:
            if dep not in seen:
                seen.add(dep)
                queue.append(dep)
    return graph


def _load_dependencies(name, root, repository, substring, warn):
    """Return the visible dependencies of one package.

    A missing root package is an error; a missing dependency is
    reported through ``warn`` and treated as a package without
    dependencies.
    """
    try:
        deps = repository.dependencies(name)
    except PackageNotFoundError:
        if name == root:
            raise
        if warn:
            warn(f"package {name} not found, assuming no dependencies")
        deps = []
    return [dep for dep in deps if not is_excluded(dep, substring)]


def find_cycles(graph):
    """Return the list of dependency cycles, each as a list of names.

    A cycle is written with the first name repeated at the end,
    for example ``["A", "B", "A"]``. Uses an explicit stack.
    """
    cycles = []
    state = {}
    for start in graph:
        if start not in state:
            _walk(start, graph, state, cycles)
    return cycles


def _walk(start, graph, state, cycles):
    """Iterative depth-first walk that records the cycles it meets."""
    path = [start]
    state[start] = ON_PATH
    stack = [iter(graph.get(start, []))]
    while stack:
        child = next(stack[-1], None)
        if child is None:
            state[path.pop()] = DONE
            stack.pop()
        elif state.get(child) == ON_PATH:
            cycles.append(path[path.index(child):] + [child])
        elif child not in state:
            state[child] = ON_PATH
            path.append(child)
            stack.append(iter(graph.get(child, [])))


def format_graph(graph):
    """Return the graph as lines ``package -> dep, dep``."""
    lines = []
    for name, deps in graph.items():
        target = ", ".join(deps) if deps else "(no dependencies)"
        lines.append(f"{name} -> {target}")
    return lines


def count_edges(graph):
    """Return the number of dependency links in the graph."""
    return sum(len(deps) for deps in graph.values())
