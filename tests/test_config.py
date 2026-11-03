"""Тесты разбора и проверки параметров командной строки."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr

from config import find_error, parse_args

URL = "https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64"


def check(*argv):
    """Разбирает параметры и возвращает текст ошибки ('' если ошибок нет)."""
    return find_error(parse_args(list(argv))) or ""


class ParseArgsTest(unittest.TestCase):
    """Проверки разбора параметров."""

    def test_values(self):
        """Значения параметров попадают в результат."""
        args = parse_args(["--package", "nginx", "--repo", URL])
        self.assertEqual(args.package, "nginx")
        self.assertEqual(args.repo, URL)

    def test_flags_off_by_default(self):
        """Флаги по умолчанию выключены."""
        args = parse_args(["--package", "nginx", "--repo", URL])
        self.assertFalse(args.test_mode)
        self.assertFalse(args.ascii_tree)
        self.assertFalse(args.reverse)

    def test_flags_on(self):
        """Флаги --test-mode, --ascii-tree и --reverse включаются."""
        args = parse_args(["--test-mode", "--ascii-tree", "--reverse"])
        self.assertTrue(args.test_mode)
        self.assertTrue(args.ascii_tree)
        self.assertTrue(args.reverse)

    def test_unknown_option(self):
        """Неизвестный параметр завершает программу с кодом 2."""
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as context:
                parse_args(["--bogus"])
        self.assertEqual(context.exception.code, 2)

    def test_flag_with_value(self):
        """Флаги не принимают значений: --ascii-tree=yes это ошибка."""
        for option in ("--ascii-tree=yes", "--test-mode=1", "--reverse=1"):
            with redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as context:
                    parse_args([option])
            self.assertEqual(context.exception.code, 2)

    def test_option_without_value(self):
        """Параметр без значения завершает программу с кодом 2."""
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_args(["--package"])


class CheckPackageTest(unittest.TestCase):
    """Проверки имени пакета."""

    def test_good_names(self):
        """Допустимые имена пакетов."""
        for name in ("nginx", "A", "libstdc++", "py3-yaml", "a.b_c-d"):
            self.assertEqual(check("--package", name, "--repo", URL), "")

    def test_missing(self):
        """Параметр --package не задан."""
        self.assertIn("--package", check("--repo", URL))

    def test_empty(self):
        """Пустое имя пакета."""
        self.assertIn("пустым", check("--package", " ", "--repo", URL))

    def test_bad_names(self):
        """Недопустимые символы в имени пакета."""
        for name in ("bad name", "a/b", "-x", "пакет", "a;b"):
            error = check("--package=" + name, "--repo", URL)
            self.assertIn("недопустимое имя", error)


class CheckRepoTest(unittest.TestCase):
    """Проверки источника репозитория."""

    def make_file(self):
        """Создаёт временный файл и возвращает путь к нему."""
        handle, path = tempfile.mkstemp(suffix=".txt")
        os.close(handle)
        self.addCleanup(os.remove, path)
        return path

    def test_good_url(self):
        """Корректный URL в обычном режиме."""
        self.assertEqual(check("--package", "a", "--repo", URL), "")

    def test_missing(self):
        """Параметр --repo не задан."""
        self.assertIn("--repo", check("--package", "a"))

    def test_empty(self):
        """Пустой --repo."""
        self.assertIn("пустым", check("--package", "a", "--repo", ""))

    def test_bad_url(self):
        """Некорректный URL в обычном режиме."""
        for repo in ("not-a-url", "ftp://host/path", "https://"):
            error = check("--package", "a", "--repo", repo)
            self.assertIn("некорректный URL", error)

    def test_good_file(self):
        """Существующий файл в тестовом режиме."""
        path = self.make_file()
        error = check("--package", "A", "--repo", path, "--test-mode")
        self.assertEqual(error, "")

    def test_file_not_found(self):
        """Несуществующий файл в тестовом режиме."""
        error = check(
            "--package", "A", "--repo", "no_such.txt", "--test-mode"
        )
        self.assertIn("не найден", error)

    def test_directory_instead_of_file(self):
        """Каталог вместо файла в тестовом режиме."""
        error = check(
            "--package", "A", "--repo", tempfile.gettempdir(),
            "--test-mode",
        )
        self.assertIn("не файл", error)

    def test_url_in_test_mode(self):
        """В тестовом режиме URL не считается файлом."""
        error = check("--package", "A", "--repo", URL, "--test-mode")
        self.assertIn("не найден", error)


if __name__ == "__main__":
    unittest.main()