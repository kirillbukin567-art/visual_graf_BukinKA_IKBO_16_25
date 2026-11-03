"""Чтение тестового репозитория: файл с описанием графа зависимостей."""

import re

from apk_repo import RepoError

NAME_PATTERN = re.compile(r"^[A-Z]+$")


def parse_line(line, number):
    """Разбирает строку вида 'A: B C' и возвращает (имя, зависимости)."""
    name, separator, rest = line.partition(":")
    name = name.strip()
    if not separator:
        raise RepoError(f"строка {number}: ожидается формат 'A: B C'")
    dependencies = rest.split()
    for item in [name] + dependencies:
        if not NAME_PATTERN.match(item):
            raise RepoError(
                f"строка {number}: недопустимое имя пакета '{item}' "
                "(нужны заглавные латинские буквы)"
            )
    return name, list(dict.fromkeys(dependencies))


def parse_graph(text):
    """Разбирает текст файла: пакет -> список зависимостей.

    Пустые строки и комментарии (после #) пропускаются. Пакет, который
    встречается только как зависимость, считается пакетом без зависимостей.
    """
    graph = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#")[0].strip()
        if not line:
            continue
        name, dependencies = parse_line(line, number)
        if name in graph:
            raise RepoError(f"строка {number}: пакет '{name}' описан повторно")
        graph[name] = dependencies
    for dependencies in list(graph.values()):
        for dependency in dependencies:
            graph.setdefault(dependency, [])
    return graph


def read_graph_file(path):
    """Читает файл тестового репозитория и возвращает граф."""
    try:
        with open(path, encoding="utf-8-sig") as file:
            text = file.read()
    except (OSError, UnicodeDecodeError) as error:
        message = f"не удалось прочитать файл '{path}': {error}"
        raise RepoError(message) from error
    return parse_graph(text)