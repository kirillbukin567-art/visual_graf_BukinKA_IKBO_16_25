"""Параметры командной строки: разбор и проверка."""

import argparse
import os
import re
from urllib.parse import urlparse

PACKAGE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
URL_SCHEMES = ("http", "https")
DEFAULT_OUTPUT_DIR = "output"


def parse_args(argv=None):
    """Разбирает параметры командной строки и возвращает их."""
    parser = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей пакетов Alpine Linux."
    )
    parser.add_argument(
        "--package", help="имя анализируемого пакета"
    )
    parser.add_argument(
        "--repo",
        help="URL репозитория или путь к файлу тестового репозитория",
    )
    parser.add_argument(
        "--test-mode", action="store_true",
        help="режим тестового репозитория: --repo задаёт путь к файлу",
    )
    parser.add_argument(
        "--reverse", action="store_true",
        help="вывести обратные зависимости (кто зависит от пакета)",
    )
    parser.add_argument(
        "--ascii-tree", action="store_true",
        help="вывести зависимости в формате ASCII-дерева",
    )
    parser.add_argument(
        "--visualize", action="store_true",
        help="построить диаграмму D2, нарисовать и показать изображение",
    )
    parser.add_argument(
        "--output-dir", default=DEFAULT_OUTPUT_DIR,
        help="каталог для файлов диаграммы (по умолчанию output)",
    )
    return parser.parse_args(argv)


def check_package(name):
    """Возвращает текст ошибки для имени пакета или None, если всё верно."""
    if name is None:
        return "не задан параметр --package (имя пакета)"
    if not name.strip():
        return "имя пакета не может быть пустым"
    if not PACKAGE_PATTERN.match(name):
        return (
            f"недопустимое имя пакета: '{name}' (допустимы латинские "
            "буквы, цифры и символы . _ + -)"
        )
    return None


def check_url(repo):
    """Возвращает текст ошибки, если repo не похож на URL, иначе None."""
    parsed = urlparse(repo)
    if parsed.scheme not in URL_SCHEMES or not parsed.netloc:
        return f"некорректный URL репозитория: '{repo}'"
    return None


def check_file(path):
    """Возвращает текст ошибки, если path не файл, иначе None."""
    if not os.path.exists(path):
        return f"файл тестового репозитория не найден: '{path}'"
    if not os.path.isfile(path):
        return f"'{path}' — не файл, а каталог"
    return None


def check_repo(repo, test_mode):
    """Возвращает текст ошибки для источника репозитория или None."""
    if repo is None:
        return "не задан параметр --repo (URL или путь к файлу)"
    if not repo.strip():
        return "параметр --repo не может быть пустым"
    if test_mode:
        return check_file(repo)
    return check_url(repo)


def check_output_dir(path):
    """Возвращает текст ошибки для каталога диаграммы или None."""
    if not path.strip():
        return "параметр --output-dir не может быть пустым"
    if os.path.exists(path) and not os.path.isdir(path):
        return f"'{path}' — не каталог, а файл"
    return None


def find_error(args):
    """Возвращает первую найденную ошибку в параметрах или None."""
    error = check_package(args.package)
    if error:
        return error
    error = check_repo(args.repo, args.test_mode)
    if error:
        return error
    if args.visualize:
        return check_output_dir(args.output_dir)
    return None