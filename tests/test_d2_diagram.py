"""Тесты диаграммы D2: текст, сохранение, рисование, показ."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from d2_diagram import (
    DiagramError, build_d2, draw, edges_between, quote, render_svg,
    save_text, show_image,
)

GRAPH = {"A": ["B", "C"], "B": ["C"], "C": [], "X": ["A"]}


def make_dir(test):
    """Создаёт временный каталог, который удалится после теста."""
    path = tempfile.mkdtemp()
    test.addCleanup(shutil.rmtree, path, True)
    return path


class TextTest(unittest.TestCase):
    """Проверки текста диаграммы."""

    def test_quote(self):
        """Имя берётся в кавычки, спецсимволы экранируются."""
        self.assertEqual(quote("libstdc++"), '"libstdc++"')
        self.assertEqual(quote('a"b'), '"a\\"b"')
        self.assertEqual(quote("a\\b"), '"a\\\\b"')

    def test_edges_between(self):
        """Берутся только рёбра между заданными узлами."""
        edges = edges_between(GRAPH, ["A", "B", "C"])
        self.assertEqual(edges, [("A", "B"), ("A", "C"), ("B", "C")])

    def test_edges_skip_outside_nodes(self):
        """Рёбра к узлам вне набора не берутся."""
        self.assertEqual(edges_between(GRAPH, ["A", "B"]), [("A", "B")])

    def test_build_d2(self):
        """Текст содержит стартовый пакет, узлы и стрелки."""
        text = build_d2("A", ["A", "B"], [("A", "B"), ("B", "A")])
        self.assertEqual(text, (
            'direction: right\n\n'
            '"A": {\n'
            '  style.fill: "#ffe699"\n'
            '}\n'
            '"B"\n'
            '"A" -> "B"\n'
            '"B" -> "A"\n'
        ))

    def test_build_d2_single_node(self):
        """Пакет без зависимостей тоже попадает в диаграмму."""
        text = build_d2("A", ["A"], [])
        self.assertIn('"A": {', text)
        self.assertNotIn("->", text)


class SaveTextTest(unittest.TestCase):
    """Проверки сохранения текста."""

    def test_save_creates_directory(self):
        """Каталог создаётся, файл записывается в UTF-8."""
        path = Path(make_dir(self)) / "new" / "a.d2"
        save_text("текст\n", path)
        self.assertEqual(path.read_text(encoding="utf-8"), "текст\n")

    def test_save_error(self):
        """Ошибка записи превращается в DiagramError."""
        directory = make_dir(self)
        with self.assertRaisesRegex(DiagramError, "не удалось сохранить"):
            save_text("x", Path(directory))


class RenderTest(unittest.TestCase):
    """Проверки запуска d2 (подменяется subprocess.run)."""

    def run_render(self, **kwargs):
        """Вызывает render_svg с подменой subprocess.run."""
        with mock.patch("subprocess.run", **kwargs) as fake:
            render_svg("a.d2", "a.svg")
        return fake

    def test_command(self):
        """d2 вызывается с входным и выходным файлами."""
        reply = mock.Mock(returncode=0, stderr="")
        fake = self.run_render(return_value=reply)
        self.assertEqual(fake.call_args[0][0], ["d2", "a.d2", "a.svg"])

    def test_not_installed(self):
        """Нет программы d2: понятная ошибка."""
        with self.assertRaisesRegex(DiagramError, "d2 не найдена"):
            self.run_render(side_effect=FileNotFoundError())

    def test_timeout(self):
        """Долгая работа d2 прерывается ошибкой."""
        error = subprocess.TimeoutExpired("d2", 1)
        with self.assertRaisesRegex(DiagramError, "не уложилась"):
            self.run_render(side_effect=error)

    def test_failure(self):
        """Ненулевой код d2: ошибка с текстом stderr."""
        reply = mock.Mock(returncode=1, stderr="bad syntax\n")
        with self.assertRaisesRegex(DiagramError, "bad syntax"):
            self.run_render(return_value=reply)

    @unittest.skipUnless(shutil.which("d2"), "программа d2 не установлена")
    def test_real_d2(self):
        """Настоящая d2 рисует SVG с именами пакетов."""
        directory = make_dir(self)
        d2_path = os.path.join(directory, "a.d2")
        svg_path = os.path.join(directory, "a.svg")
        text = build_d2("a.b", ["a.b", "c++"], [("a.b", "c++")])
        save_text(text, d2_path)
        render_svg(d2_path, svg_path)
        with open(svg_path, encoding="utf-8") as file:
            content = file.read()
        self.assertIn("a.b", content)
        self.assertIn("c++", content)


class ShowAndDrawTest(unittest.TestCase):
    """Проверки показа изображения и общей функции draw."""

    def test_show_opens_file_uri(self):
        """Изображение открывается по адресу file://."""
        with mock.patch("webbrowser.open", return_value=True) as fake:
            show_image("x.svg")
        self.assertTrue(fake.call_args[0][0].startswith("file://"))
        self.assertTrue(fake.call_args[0][0].endswith("/x.svg"))

    def test_show_failure(self):
        """Если открыть не удалось, выдаётся DiagramError."""
        with mock.patch("webbrowser.open", return_value=False):
            with self.assertRaisesRegex(DiagramError, "не удалось открыть"):
                show_image("x.svg")

    def test_draw_order(self):
        """draw сохраняет текст, рисует и показывает изображение."""
        directory = make_dir(self)
        calls = []
        with mock.patch("d2_diagram.render_svg",
                        side_effect=lambda *a: calls.append("render")):
            with mock.patch("d2_diagram.show_image",
                            side_effect=lambda *a: calls.append("show")):
                d2_path, svg_path = draw("text\n", directory, "pkg")
        self.assertEqual(calls, ["render", "show"])
        self.assertEqual(d2_path.name, "pkg.d2")
        self.assertEqual(svg_path.name, "pkg.svg")
        self.assertTrue(d2_path.exists())


if __name__ == "__main__":
    unittest.main()