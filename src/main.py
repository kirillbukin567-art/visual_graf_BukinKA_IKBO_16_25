"""Точка входа: визуализатор графа зависимостей пакетов."""

import sys

from apk_repo import RepoError, get_graph
from config import find_error, parse_args
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


def print_result(package, order, cycles, reverse):
    """Печатает найденные пакеты и циклы.

    В обычном режиме это зависимости пакета, в обратном — пакеты,
    которые зависят от него.
    """
    title = "Обратные зависимости" if reverse else "Транзитивные зависимости"
    arrow = " <- " if reverse else " -> "
    packages = order[1:]
    print(f"{title} пакета {package}: {len(packages)}")
    for name in packages:
        print(f"  {name}")
    if not cycles:
        print("Циклические зависимости: нет")
        return
    print(f"Циклические зависимости: {len(cycles)}")
    for cycle in cycles:
        print("  " + arrow.join(cycle))


def fail(message):
    """Печатает сообщение об ошибке и возвращает код ошибки."""
    print(f"Ошибка: {message}", file=sys.stderr)
    return EXIT_ERROR


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
    if args.reverse:
        graph = reverse_graph(graph)
    order, cycles = traverse(graph, args.package)
    print_result(args.package, order, cycles, args.reverse)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())