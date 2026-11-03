"""Чтение репозитория Alpine Linux (apk): индекс пакетов и зависимости."""

import http.client
import io
import re
import tarfile
import urllib.request

INDEX_ARCHIVE = "APKINDEX.tar.gz"
INDEX_FILE = "APKINDEX"
TIMEOUT_SECONDS = 30
VERSION_SIGNS = re.compile(r"[<>=~]")


class RepoError(Exception):
    """Ошибка при получении или разборе данных репозитория."""


def download_index(repo_url):
    """Скачивает архив APKINDEX.tar.gz репозитория и возвращает его байты."""
    url = repo_url.rstrip("/") + "/" + INDEX_ARCHIVE
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as reply:
            return reply.read()
    except (OSError, ValueError, http.client.HTTPException) as error:
        raise RepoError(f"не удалось скачать {url}: {error}") from error


def unpack_index(archive):
    """Достаёт из архива текст файла APKINDEX."""
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
            member = tar.extractfile(INDEX_FILE)
            if member is None:
                raise RepoError("в архиве нет файла APKINDEX")
            return member.read().decode("utf-8")
    except (tarfile.TarError, OSError, EOFError, KeyError,
            UnicodeDecodeError) as error:
        raise RepoError(f"не удалось прочитать индекс: {error}") from error


def parse_block(block):
    """Разбирает блок индекса (один пакет): поле -> значение."""
    record = {}
    for line in block.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            record[key] = value
    return record


def parse_index(text):
    """Разбирает текст APKINDEX: имя пакета -> запись о пакете."""
    packages = {}
    for block in text.split("\n\n"):
        record = parse_block(block)
        if "P" in record:
            packages[record["P"]] = record
    return packages


def dependency_name(token):
    """Возвращает имя зависимости без условия версии.

    Для запретов (начинаются с '!') и пустых имён возвращает None.
    """
    if token.startswith("!"):
        return None
    return VERSION_SIGNS.split(token)[0] or None


def direct_dependencies(packages, name):
    """Возвращает прямые зависимости пакета в порядке индекса, без повторов."""
    record = packages.get(name)
    if record is None:
        raise RepoError(f"пакет '{name}' не найден в репозитории")
    result = []
    for token in record.get("D", "").split():
        dependency = dependency_name(token)
        if dependency and dependency not in result:
            result.append(dependency)
    return result


def get_direct_dependencies(package, repo_url):
    """Скачивает индекс репозитория и возвращает зависимости пакета."""
    archive = download_index(repo_url)
    packages = parse_index(unpack_index(archive))
    return direct_dependencies(packages, package)