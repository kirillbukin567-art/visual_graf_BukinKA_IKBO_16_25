"""Точка входа: визуализатор графа зависимостей пакетов."""

import sys

from apk_repo import RepoError, get_graph
from ascii_tree import ascii_tree
from config import find_error, parse_args
from d2_diagram import DiagramError, build_d2, draw, edges_between
from graph import reverse_graph, traverse
from graph_file import read_graph_file

EXIT_OK = 0
EXIT_ERROR = 1


def load_graph(args):
    """Загружает граф из тестового файла или из репозитория Alpine."""
    if args.test_mode:
        graph = read_graph_file(args.repo)
    else:
        graph = get_graph(args.repo)
    if args.package not in graph:
        raise RepoError(f"пакет '{args.package}' не найден в репозитории")
    return graph


def print_result(package, order, cycles, reverse, tree=None):
    """Печатает найденные пакеты (списком или деревом) и циклы.

    В обычном режиме это зависимости пакета, в обратном — пакеты,
    которые зависят от него. Если передано дерево, оно заменяет список.
    """
    title = "Обратные зависимости" if reverse else "Транзитивные зависимости"
    arrow = " <- " if reverse else " -> "
    packages = order[1:]
    print(f"{title} пакета {package}: {len(packages)}")
    for line in tree or [f"  {name}" for name in packages]:
        print(line)
    if not cycles:
        print("Циклические зависимости: нет")
        return
    print(f"Циклические зависимости: {len(cycles)}")
    for cycle in cycles:
        print("  " + arrow.join(cycle))


def visualize(args, graph, order):
    """Печатает D2-текст, рисует диаграмму и показывает изображение."""
    edges = edges_between(graph, order)
    text = build_d2(args.package, order, edges)
    print("D2-диаграмма:")
    print(text, end="")
    name = args.package + ("_reverse" if args.reverse else "")
    d2_path, svg_path = draw(text, args.output_dir, name)
    print(f"Файлы диаграммы: {d2_path}, {svg_path}")


def fail(message):
    """Печатает сообщение об ошибке и возвращает код ошибки."""
    print(f"Ошибка: {message}", file=sys.stderr)
    return EXIT_ERROR


def use_utf8_output():
    """Включает вывод в UTF-8, чтобы дерево и русский текст не терялись
    при перенаправлении вывода в файл.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")


def main(argv=None):
    """Запускает приложение и возвращает код завершения."""
    args = parse_args(argv)
    error = find_error(args)
    if error:
        return fail(error)
    try:
        graph = load_graph(args)
    except RepoError as repo_error:
        return fail(repo_error)
    walk = reverse_graph(graph) if args.reverse else graph
    order, cycles = traverse(walk, args.package)
    tree = ascii_tree(walk, args.package) if args.ascii_tree else None
    print_result(args.package, order, cycles, args.reverse, tree)
    if args.visualize:
        try:
            visualize(args, graph, order)
        except DiagramError as diagram_error:
            return fail(diagram_error)
    return EXIT_OK


if __name__ == "__main__":
    use_utf8_output()
    sys.exit(main())