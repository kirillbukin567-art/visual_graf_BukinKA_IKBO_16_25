"""Точка входа: визуализатор графа зависимостей пакетов."""

import sys

from apk_repo import RepoError, get_direct_dependencies
from config import find_error, parse_args

EXIT_OK = 0
EXIT_ERROR = 1


def print_dependencies(package, dependencies):
    """Печатает прямые зависимости пакета."""
    print(f"Прямые зависимости пакета {package}: {len(dependencies)}")
    for name in dependencies:
        print(f"  {name}")


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
    if args.test_mode:
        return fail("тестовый режим будет добавлен на этапе 3")
    try:
        dependencies = get_direct_dependencies(args.package, args.repo)
    except RepoError as repo_error:
        return fail(repo_error)
    print_dependencies(args.package, dependencies)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())