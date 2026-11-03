"""Тесты точки входа: вывод результата и коды завершения."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from apk_repo import RepoError
from d2_diagram import DiagramError
from main import EXIT_ERROR, EXIT_OK, main, use_utf8_output

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


class Utf8OutputTest(unittest.TestCase):
    """Проверка переключения вывода в UTF-8."""

    def test_streams_are_reconfigured(self):
        """stdout и stderr переключаются на UTF-8."""
        out, err = mock.Mock(), mock.Mock()
        with mock.patch("sys.stdout", out), mock.patch("sys.stderr", err):
            use_utf8_output()
        out.reconfigure.assert_called_once_with(encoding="utf-8")
        err.reconfigure.assert_called_once_with(encoding="utf-8")


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


class AsciiTreeModeTest(unittest.TestCase):
    """Проверки вывода ASCII-дерева (--ascii-tree)."""

    def run_tree(self, package, filename, *extra):
        """Запускает main с --ascii-tree в тестовом режиме."""
        argv = ["--package", package, "--repo", data_file(filename),
                "--test-mode", "--ascii-tree", *extra]
        return run_main(argv)

    def test_tree_replaces_list(self):
        """Дерево выводится вместо плоского списка."""
        code, out, _ = self.run_tree("A", "graph_simple.txt")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, (
            "Транзитивные зависимости пакета A: 3\n"
            "A\n├── B\n│   └── D\n└── C\n    └── D\n"
            "Циклические зависимости: нет\n"
        ))

    def test_tree_with_cycles(self):
        """В дереве циклы помечены, список циклов выводится."""
        _, out, _ = self.run_tree("A", "graph_complex.txt")
        self.assertIn("│       ├── B (цикл)", out)
        self.assertIn("        └── E (цикл)", out)
        self.assertIn("  E -> E", out)

    def test_reverse_tree(self):
        """Вместе с --reverse строится дерево обратных зависимостей."""
        _, out, _ = self.run_tree("A", "graph_cycle.txt", "--reverse")
        self.assertIn("Обратные зависимости пакета A: 2", out)
        self.assertIn("        └── A (цикл)", out)

    def test_real_mode_tree(self):
        """В режиме Alpine дерево строится по графу репозитория."""
        argv = ["--package", "nginx", "--repo", URL, "--ascii-tree"]
        _, out, _ = run_main(argv, graph=GRAPH)
        self.assertIn("nginx\n├── pcre2\n│   └── musl\n└── musl", out)


class VisualizeModeTest(unittest.TestCase):
    """Проверки режима диаграммы (--visualize)."""

    def run_visualize(self, package, *extra, draw_error=None):
        """Запускает main с --visualize, не трогая диск и браузер."""
        argv = ["--package", package, "--repo", data_file("graph_complex.txt"),
                "--test-mode", "--visualize", *extra]
        fake = mock.Mock(return_value=("o/A.d2", "o/A.svg"),
                         side_effect=draw_error)
        with mock.patch("main.draw", fake):
            result = run_main(argv)
        return result, fake

    def test_prints_d2_and_draws(self):
        """Выводится D2-текст, вызывается рисование, код 0."""
        (code, out, _), fake = self.run_visualize("A")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("D2-диаграмма:", out)
        self.assertIn('"A" -> "B"', out)
        self.assertIn('"E" -> "E"', out)
        self.assertIn("Файлы диаграммы: o/A.d2, o/A.svg", out)
        text, directory, name = fake.call_args[0]
        self.assertIn('"D" -> "B"', text)
        self.assertEqual((directory, name), ("output", "A"))

    def test_output_dir_is_passed(self):
        """Каталог из --output-dir передаётся в draw."""
        _, fake = self.run_visualize("A", "--output-dir", "pics")
        self.assertEqual(fake.call_args[0][1], "pics")

    def test_reverse_file_name(self):
        """В обратном режиме к имени файла добавляется _reverse."""
        _, fake = self.run_visualize("D", "--reverse")
        self.assertEqual(fake.call_args[0][2], "D_reverse")

    def test_reverse_edges_keep_direction(self):
        """В обратном режиме стрелки остаются «зависит от»."""
        (_, out, _), _ = self.run_visualize("F", "--reverse")
        self.assertIn('"D" -> "F"', out)
        self.assertNotIn('"F" -> "D"', out)

    def test_diagram_error(self):
        """Ошибка диаграммы: сообщение в stderr и код 1."""
        error = DiagramError("программа d2 не найдена")
        (code, _, err), _ = self.run_visualize("A", draw_error=error)
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("Ошибка: программа d2 не найдена", err)

    def test_bad_output_dir(self):
        """Файл вместо каталога: ошибка параметра, draw не вызывается."""
        (code, _, err), fake = self.run_visualize(
            "A", "--output-dir", data_file("graph_simple.txt"))
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("не каталог", err)
        fake.assert_not_called()

    def test_without_flag_no_drawing(self):
        """Без --visualize диаграмма не строится."""
        argv = ["--package", "A", "--repo", data_file("graph_simple.txt"),
                "--test-mode"]
        with mock.patch("main.draw") as fake:
            _, out, _ = run_main(argv)
        fake.assert_not_called()
        self.assertNotIn("D2", out)


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