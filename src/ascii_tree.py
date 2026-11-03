"""ASCII-дерево зависимостей (обход без рекурсии)."""

BRANCH = "├── "
LAST_BRANCH = "└── "
PIPE = "│   "
SPACE = "    "
CYCLE_NOTE = " (цикл)"
SEEN_NOTE = " (см. выше)"


def child_note(child, path, expanded, has_children):
    """Возвращает пометку пакета в дереве: цикл, повтор или пустую строку."""
    if child in path:
        return CYCLE_NOTE
    if has_children and child in expanded:
        return SEEN_NOTE
    return ""


def ascii_tree(graph, start):
    """Строит ASCII-дерево зависимостей пакета, возвращает список строк.

    Обход без рекурсии, стек хранит кадры [пакет, дети, индекс, отступ].
    Пакет, который уже лежит на текущем пути, помечается '(цикл)' и не
    раскрывается; пакет, чьи зависимости уже показаны выше, помечается
    '(см. выше)'.
    """
    lines = [start]
    expanded = {start}
    frames = [[start, list(graph.get(start, [])), 0, ""]]
    while frames:
        _, children, index, prefix = frames[-1]
        if index == len(children):
            frames.pop()
            continue
        frames[-1][2] += 1
        child = children[index]
        last = index == len(children) - 1
        grandchildren = list(graph.get(child, []))
        path = [frame[0] for frame in frames]
        note = child_note(child, path, expanded, bool(grandchildren))
        branch = LAST_BRANCH if last else BRANCH
        lines.append(prefix + branch + child + note)
        if grandchildren and not note:
            expanded.add(child)
            deeper = prefix + (SPACE if last else PIPE)
            frames.append([child, grandchildren, 0, deeper])
    return lines