"""Точка входа: визуализатор графа зависимостей пакетов."""

import sys

from apk_repo import RepoError, get_graph
from config import find_error, parse_args
from graph import traverse
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


def print_result(package, order, cycles):
    """Печатает транзитивные зависимости пакета и найденные циклы."""
    dependencies = order[1:]
    print(f"Транзитивные зависимости пакета {package}: {len(dependencies)}")
    for name in dependencies:
        print(f"  {name}")
    if not cycles:
        print("Циклические зависимости: нет")
        return
    print(f"Циклические зависимости: {len(cycles)}")
    for cycle in cycles:
        print("  " + " -> ".join(cycle))


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
    order, cycles = traverse(graph, args.package)
    print_result(args.package, order, cycles)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())