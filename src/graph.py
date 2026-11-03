"""Обход графа зависимостей в глубину без рекурсии."""


def traverse(graph, start):
    """Обходит граф в глубину от start без рекурсии.

    graph: словарь «пакет -> список его зависимостей».
    Возвращает пару: порядок обхода (первым идёт start) и список
    найденных циклов. Цикл — список пакетов, у которого первый и
    последний элементы совпадают, например ['A', 'B', 'A'].
    """
    order = [start]
    cycles = []
    visited = {start}
    path = [start]
    stack = [iter(graph.get(start, []))]
    while stack:
        child = next(stack[-1], None)
        if child is None:
            stack.pop()
            path.pop()
        elif child in path:
            cycles.append(path[path.index(child):] + [child])
        elif child not in visited:
            visited.add(child)
            order.append(child)
            path.append(child)
            stack.append(iter(graph.get(child, [])))
    return order, cycles