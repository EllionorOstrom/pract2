"""Text description of a dependency graph in PlantUML."""

ROOT_COLOR = "#LightBlue"


def to_plantuml(root, graph):
    """Return the PlantUML diagram of the graph as a list of lines.

    Every package is a rectangle with an alias ``n0``, ``n1`` ...
    (aliases keep names with '-' or '.' safe); every dependency is
    an arrow from the package to the dependency.
    """
    ids = {name: f"n{index}" for index, name in enumerate(graph)}
    lines = ["@startuml", f"title Dependency graph of {root}"]
    for name, alias in ids.items():
        color = f" {ROOT_COLOR}" if name == root else ""
        lines.append(f'rectangle "{name}" as {alias}{color}')
    for name, deps in graph.items():
        for dep in deps:
            lines.append(f"{ids[name]} --> {ids[dep]}")
    lines.append("@enduml")
    return lines
