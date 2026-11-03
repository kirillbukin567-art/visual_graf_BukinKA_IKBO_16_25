"""Тесты чтения репозитория Alpine: индекс, зависимости, скачивание."""

import gzip
import io
import tarfile
import unittest
import urllib.error
from email.message import Message
from unittest import mock

from apk_repo import (
    RepoError, dependency_name, direct_dependencies, download_index,
    get_graph, package_graph, parse_block, parse_index, provider_map,
    unpack_index,
)

INDEX_TEXT = """C:Q1AAA=
P:musl
V:1.2.5-r0
p:so:libc.musl-x86_64.so.1=1

C:Q1BBB=
P:nginx
V:1.26.3-r0
D:so:libc.musl-x86_64.so.1 pcre2>=10 !apache2 /bin/sh pcre2
p:cmd:nginx=1.26.3-r0

C:Q1CCC=
P:pcre2
V:10.42-r0
D:
"""


def make_tar(name, data, with_end=True):
    """Возвращает байты tar-архива с одним файлом."""
    buffer = io.BytesIO()
    tar = tarfile.open(fileobj=buffer, mode="w")
    info = tarfile.TarInfo(name)
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))
    if with_end:
        tar.close()
    return buffer.getvalue()


def make_archive(text=INDEX_TEXT, with_signature=True):
    """Собирает APKINDEX.tar.gz: поток с подписью и поток с индексом."""
    parts = []
    if with_signature:
        signature = make_tar(".SIGN.RSA.test.rsa.pub", b"sign", False)
        parts.append(gzip.compress(signature))
    parts.append(gzip.compress(make_tar("APKINDEX", text.encode())))
    return b"".join(parts)


class UnpackIndexTest(unittest.TestCase):
    """Проверки распаковки архива индекса."""

    def test_with_signature(self):
        """Индекс читается из архива с подписью (два gzip-потока)."""
        self.assertEqual(unpack_index(make_archive()), INDEX_TEXT)

    def test_without_signature(self):
        """Индекс читается из архива без подписи."""
        archive = make_archive(with_signature=False)
        self.assertEqual(unpack_index(archive), INDEX_TEXT)

    def test_not_an_archive(self):
        """Произвольные байты вызывают RepoError."""
        with self.assertRaises(RepoError):
            unpack_index(b"this is not an archive")

    def test_no_index_file(self):
        """Архив без файла APKINDEX вызывает RepoError."""
        other = gzip.compress(make_tar("OTHER", b"x"))
        with self.assertRaises(RepoError):
            unpack_index(other)

    def test_index_is_directory(self):
        """Если APKINDEX в архиве — каталог, а не файл, выдаётся RepoError."""
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w") as tar:
            info = tarfile.TarInfo("APKINDEX")
            info.type = tarfile.DIRTYPE
            tar.addfile(info)
        with self.assertRaisesRegex(RepoError, "нет файла"):
            unpack_index(gzip.compress(buffer.getvalue()))


class ParseIndexTest(unittest.TestCase):
    """Проверки разбора текста индекса."""

    def test_parse_block(self):
        """Блок разбирается в словарь поле -> значение."""
        record = parse_block("P:nginx\nV:1.0\nD:a b")
        self.assertEqual(record, {"P": "nginx", "V": "1.0", "D": "a b"})

    def test_value_may_contain_colon(self):
        """Двоеточие внутри значения сохраняется."""
        record = parse_block("D:so:libc.so.1")
        self.assertEqual(record["D"], "so:libc.so.1")

    def test_parse_index(self):
        """Все пакеты индекса попадают в словарь по имени."""
        packages = parse_index(INDEX_TEXT)
        self.assertEqual(sorted(packages), ["musl", "nginx", "pcre2"])
        self.assertEqual(packages["nginx"]["V"], "1.26.3-r0")

    def test_block_without_name_is_skipped(self):
        """Блок без поля P (пустой) пропускается."""
        self.assertEqual(parse_index("\n\n\nX:1\n\n"), {})


class DependencyNameTest(unittest.TestCase):
    """Проверки очистки имени зависимости."""

    def test_plain_name(self):
        """Имя без условий остаётся как есть."""
        self.assertEqual(dependency_name("pcre2"), "pcre2")
        self.assertEqual(dependency_name("so:libssl.so.3"), "so:libssl.so.3")
        self.assertEqual(dependency_name("/bin/sh"), "/bin/sh")

    def test_version_conditions(self):
        """Условие версии отбрасывается."""
        for token in ("a>=1.2", "a<=1", "a=1.0-r0", "a<2", "a>1", "a~1.2"):
            self.assertEqual(dependency_name(token), "a")

    def test_conflict_is_not_dependency(self):
        """Запрет (!имя) не является зависимостью."""
        self.assertIsNone(dependency_name("!apache2"))

    def test_empty_name(self):
        """Условие без имени игнорируется."""
        self.assertIsNone(dependency_name(">=1.0"))


class DirectDependenciesTest(unittest.TestCase):
    """Проверки получения прямых зависимостей."""

    def setUp(self):
        """Разбирает тестовый индекс."""
        self.packages = parse_index(INDEX_TEXT)

    def test_dependencies(self):
        """Зависимости очищены, без запретов и повторов, в порядке индекса."""
        result = direct_dependencies(self.packages, "nginx")
        self.assertEqual(result, ["so:libc.musl-x86_64.so.1", "pcre2",
                                  "/bin/sh"])

    def test_no_dependencies(self):
        """Пакет без зависимостей даёт пустой список."""
        self.assertEqual(direct_dependencies(self.packages, "musl"), [])
        self.assertEqual(direct_dependencies(self.packages, "pcre2"), [])

    def test_package_not_found(self):
        """Неизвестный пакет вызывает RepoError."""
        with self.assertRaisesRegex(RepoError, "не найден"):
            direct_dependencies(self.packages, "nope")


class DownloadIndexTest(unittest.TestCase):
    """Проверки скачивания индекса (сеть подменяется)."""

    def test_url_is_built(self):
        """К адресу репозитория добавляется APKINDEX.tar.gz."""
        reply = mock.MagicMock()
        reply.__enter__.return_value.read.return_value = b"data"
        with mock.patch("urllib.request.urlopen", return_value=reply) as m:
            for repo in ("https://h/a/b", "https://h/a/b/"):
                self.assertEqual(download_index(repo), b"data")
                self.assertEqual(
                    m.call_args[0][0], "https://h/a/b/APKINDEX.tar.gz"
                )

    def test_network_error(self):
        """Сетевая ошибка превращается в RepoError."""
        error = urllib.error.URLError("no route")
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(RepoError, "не удалось скачать"):
                download_index("https://h/repo")

    def test_http_error(self):
        """Ответ 404 превращается в RepoError."""
        body = io.BytesIO()
        error = urllib.error.HTTPError("u", 404, "Not Found", Message(), body)
        self.addCleanup(error.close)
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(RepoError, "404"):
                download_index("https://h/repo")


class ProviderMapTest(unittest.TestCase):
    """Проверки словаря «предоставляемое имя -> пакет»."""

    def test_names_and_provides(self):
        """Имена пакетов и их provides указывают на пакет."""
        providers = provider_map(parse_index(INDEX_TEXT))
        self.assertEqual(providers["nginx"], "nginx")
        self.assertEqual(providers["so:libc.musl-x86_64.so.1"], "musl")
        self.assertEqual(providers["cmd:nginx"], "nginx")

    def test_own_name_wins(self):
        """Имя реального пакета важнее чужого provides."""
        text = "P:a\np:b=1\n\nP:b\n"
        self.assertEqual(provider_map(parse_index(text))["b"], "b")

    def test_first_provider_wins(self):
        """Если имя предоставляют несколько пакетов, берётся первый."""
        text = "P:a\np:v\n\nP:b\np:v\n"
        self.assertEqual(provider_map(parse_index(text))["v"], "a")


class PackageGraphTest(unittest.TestCase):
    """Проверки построения графа пакетов."""

    def test_virtual_dependencies_are_resolved(self):
        """so: и повторы заменяются реальными пакетами."""
        graph = package_graph(parse_index(INDEX_TEXT))
        self.assertEqual(graph["nginx"], ["musl", "pcre2"])
        self.assertEqual(graph["musl"], [])
        self.assertEqual(graph["pcre2"], [])

    def test_self_dependency_is_dropped(self):
        """Зависимость пакета от своего же provides отбрасывается."""
        text = "P:a\np:so:a.1\nD:so:a.1 b\n\nP:b\n"
        graph = package_graph(parse_index(text))
        self.assertEqual(graph["a"], ["b"])

    def test_cycle_is_kept(self):
        """Цикл между пакетами сохраняется в графе."""
        text = "P:a\nD:b\n\nP:b\nD:a\n"
        graph = package_graph(parse_index(text))
        self.assertEqual(graph, {"a": ["b"], "b": ["a"]})


class GetGraphTest(unittest.TestCase):
    """Проверка всей цепочки: скачать, распаковать, разобрать, построить."""

    def test_whole_chain(self):
        """Граф строится из архива индекса."""
        with mock.patch("apk_repo.download_index",
                        return_value=make_archive()):
            graph = get_graph("https://h/repo")
        self.assertEqual(graph["nginx"], ["musl", "pcre2"])


if __name__ == "__main__":
    unittest.main()