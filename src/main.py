"""Точка входа: визуализатор графа зависимостей пакетов."""

import sys

from config import find_error, parse_args, print_args

EXIT_OK = 0
EXIT_ERROR = 1


def main(argv=None):
    """Запускает приложение и возвращает код завершения."""
    args = parse_args(argv)
    error = find_error(args)
    if error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    print_args(args)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())