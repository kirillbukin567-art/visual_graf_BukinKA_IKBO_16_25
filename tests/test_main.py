"""Тесты точки входа: вывод результата и коды завершения."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from apk_repo import RepoError
from main import EXIT_ERROR, EXIT_OK, main

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64"
GRAPH = {"nginx": ["pcre2", "musl"], "pcre2": ["musl"], "musl": []}


def data_file(name):
    """Возвращает путь к файлу из каталога data."""
    return os.path.join(ROOT, "data", name)


def run_main(argv, graph=None, repo_error=None):
    """Запускает main с подменой чтения репозитория Alpine.

    Возвращает код завершения, текст stdout и текст stderr.
    """
    out = io.StringIO()
    err = io.StringIO()
    fake = mock.Mock(return_value=graph, side_effect=repo_error)
    with mock.patch("main.get_graph", fake):
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
    return code, out.getvalue(), err.getvalue()


class RealModeTest(unittest.TestCase):
    """Проверки обычного режима (репозиторий Alpine)."""

    def test_prints_dependencies(self):
        """Транзитивные зависимости выводятся списком, код 0."""
        argv = ["--package", "nginx", "--repo", URL]
        code, out, _ = run_main(argv, graph=GRAPH)
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, (
            "Транзитивные зависимости пакета nginx: 2\n"
            "  pcre2\n  musl\n"
            "Циклические зависимости: нет\n"
        ))

    def test_package_not_in_repository(self):
        """Пакета нет в графе: ошибка и код 1."""
        argv = ["--package", "nope", "--repo", URL]
        code, out, err = run_main(argv, graph=GRAPH)
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("пакет 'nope' не найден", err)

    def test_repo_error(self):
        """Ошибка репозитория: сообщение в stderr, код 1."""
        argv = ["--package", "nginx", "--repo", URL]
        code, _, err = run_main(argv, repo_error=RepoError("нет сети"))
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("Ошибка: нет сети", err)

    def test_parameter_error(self):
        """Ошибка параметров: сообщение в stderr, код 1."""
        code, _, err = run_main([])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("Ошибка:", err)


class ReverseModeTest(unittest.TestCase):
    """Проверки режима обратных зависимостей (--reverse)."""

    def run_reverse(self, package, filename):
        """Запускает main с --reverse в тестовом режиме."""
        argv = ["--package", package, "--repo", data_file(filename),
                "--test-mode", "--reverse"]
        return run_main(argv)

    def test_real_mode(self):
        """В режиме Alpine выводятся пакеты, зависящие от musl."""
        argv = ["--package", "musl", "--repo", URL, "--reverse"]
        code, out, _ = run_main(argv, graph=GRAPH)
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, (
            "Обратные зависимости пакета musl: 2\n"
            "  nginx\n  pcre2\n"
            "Циклические зависимости: нет\n"
        ))

    def test_diamond(self):
        """От D зависят B, A и C (транзитивно)."""
        code, out, _ = self.run_reverse("D", "graph_simple.txt")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, (
            "Обратные зависимости пакета D: 3\n"
            "  B\n  A\n  C\n"
            "Циклические зависимости: нет\n"
        ))

    def test_nobody_depends(self):
        """От A никто не зависит."""
        code, out, _ = self.run_reverse("A", "graph_simple.txt")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("пакета A: 0", out)

    def test_cycle(self):
        """Цикл в обратном графе найден, стрелки направлены обратно."""
        code, out, _ = self.run_reverse("A", "graph_cycle.txt")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, (
            "Обратные зависимости пакета A: 2\n"
            "  C\n  B\n"
            "Циклические зависимости: 1\n"
            "  A <- C <- B <- A\n"
        ))

    def test_complex(self):
        """Цикл между B и D и самозависимость E."""
        _, out, _ = self.run_reverse("D", "graph_complex.txt")
        self.assertIn("пакета D: 3", out)
        self.assertIn("  D <- B <- D", out)
        _, out, _ = self.run_reverse("E", "graph_complex.txt")
        self.assertIn("  E <- E", out)

    def test_package_not_in_file(self):
        """Пакета нет в файле: ошибка."""
        code, _, err = self.run_reverse("Z", "graph_simple.txt")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("пакет 'Z' не найден", err)


class TestModeTest(unittest.TestCase):
    """Проверки тестового режима (файл с графом)."""

    def run_test_mode(self, package, filename):
        """Запускает main в тестовом режиме на файле из data."""
        argv = ["--package", package, "--repo", data_file(filename),
                "--test-mode"]
        return run_main(argv)

    def test_diamond(self):
        """Ромб без циклов: общая зависимость выводится один раз."""
        code, out, _ = self.run_test_mode("A", "graph_simple.txt")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, (
            "Транзитивные зависимости пакета A: 3\n"
            "  B\n  D\n  C\n"
            "Циклические зависимости: нет\n"
        ))

    def test_cycle(self):
        """Цикл найден, программа завершилась с кодом 0."""
        code, out, _ = self.run_test_mode("A", "graph_cycle.txt")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, (
            "Транзитивные зависимости пакета A: 2\n"
            "  B\n  C\n"
            "Циклические зависимости: 1\n"
            "  A -> B -> C -> A\n"
        ))

    def test_complex(self):
        """Два цикла: между B и D и самозависимость E."""
        code, out, _ = self.run_test_mode("A", "graph_complex.txt")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("пакета A: 5", out)
        self.assertIn("Циклические зависимости: 2", out)
        self.assertIn("  B -> D -> B", out)
        self.assertIn("  E -> E", out)

    def test_package_not_in_file(self):
        """Пакета нет в файле: ошибка."""
        code, _, err = self.run_test_mode("Z", "graph_simple.txt")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("пакет 'Z' не найден", err)

    def test_bad_file(self):
        """Неверный формат файла: ошибка с номером строки."""
        code, _, err = self.run_test_mode("A", "graph_bad.txt")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("строка 3", err)

    def test_unreadable_file(self):
        """Файл, который не удаётся прочитать как текст: ошибка."""
        handle, path = tempfile.mkstemp()
        self.addCleanup(os.remove, path)
        with os.fdopen(handle, "wb") as file:
            file.write(b"\xff\xfe\x00")
        code, _, err = run_main(
            ["--package", "A", "--repo", path, "--test-mode"]
        )
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("не удалось прочитать", err)


if __name__ == "__main__":
    unittest.main()