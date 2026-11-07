"""Load order of dependencies (dependencies before dependents)."""


def load_order(graph, root):
    """Return the packages of the graph in load order.

    A package appears after all of its dependencies (post-order
    depth-first traversal with an explicit stack, no recursion).
    For cyclic dependencies the edge that closes a cycle is ignored,
    so the order inside a cycle is arbitrary but the traversal ends.
    """
    order = []
    visited = {root}
    stack = [(root, iter(graph.get(root, [])))]
    while stack:
        name, children = stack[-1]
        child = next(children, None)
        if child is None:
            order.append(name)
            stack.pop()
        elif child not in visited:
            visited.add(child)
            stack.append((child, iter(graph.get(child, []))))
    return order


def format_order(root, order):
    """Return numbered lines describing the load order."""
    lines = [f"Load order of {root} (dependencies first):"]
    for number, name in enumerate(order, start=1):
        lines.append(f"  {number}. {name}")
    return lines
